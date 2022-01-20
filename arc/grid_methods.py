import numpy as np

from arc.util import logger
from arc.definitions import Constants as cst

log = logger.fancy_logger("BoardMethods", level=30)

from arc.types import PointDict, PointList, Position


def norm_points(points: PointList) -> tuple[Position, PointList, bool]:
    """Calculate the seed (min row and col) of a list of points and norm them.

    Returns a tuple: seed coordinates, normalized point list.
    """
    minrow, mincol = cst.MAX_ROWS, cst.MAX_COLS
    monochrome = True
    color = points[0][2]
    for pt in points:
        minrow = min(minrow, pt[0])
        mincol = min(mincol, pt[1])
        if color != pt[2]:
            monochrome = False
    result = []
    for pt in points:
        result.append((pt[0] - minrow, pt[1] - mincol, pt[2]))
    return (minrow, mincol), result, monochrome


# TODO Reconsider object use + modifying objects
def norm_children(children):
    """Makes sure the parent/kid position relationship is normalized"""
    if not children:
        return (0, 0)
    minrow, mincol = cst.MAX_ROWS, cst.MAX_COLS
    for obj in children:
        minrow = min(minrow, obj.row)
        mincol = min(mincol, obj.col)
    for obj in children:
        obj.row -= minrow
        obj.col -= mincol
    return (minrow, mincol)


def point_filter(points: PointDict, color: int) -> tuple[PointList, PointList]:
    """Filter out a single color from a grid."""
    match_pts: PointList = []
    other_pts: PointList = []
    for (row, col), val in points.items():
        if val == color:
            match_pts.append((row, col, val))
        else:
            other_pts.append((row, col, val))
    return match_pts, other_pts


def intersect(grids: list[np.ndarray]) -> np.ndarray:
    """WIP"""
    base = grids[0].copy()
    for comp in grids[1:]:
        if base.shape != comp.shape:
            base[:, :] = cst.MARKED_COLOR
            return base
        base[base != comp] = cst.MARKED_COLOR
    return base


def expand(grid: np.ndarray, mult: tuple[int, int]) -> np.ndarray:
    M, N = grid.shape
    out = np.full((M * mult[0], N * mult[1]), -1)
    for i in range(M):
        rows = slice(i * mult[0], (i + 1) * mult[0], 1)
        for j in range(N):
            cols = slice(j * mult[1], (j + 1) * mult[1], 1)
            out[rows, cols] = grid[i, j]
    return out


# TODO Review
def color_connect(marked: np.ndarray, max_ct: int = 10) -> tuple[list[PointList], str]:
    """Try connecting groups of points based on colors

    If we only produce 1 group, or more than max_ct, we Fail.
    If all groups are only size 1, we Fail.
    """
    blobs = []
    max_size = 0
    for start in zip(*np.where(marked != cst.MARKED_COLOR)):
        if marked[start] == cst.MARKED_COLOR:
            continue
        pts = get_blob(marked, start)
        max_size = max(max_size, len(pts))
        blobs.append(pts)
        if len(blobs) > max_ct:
            return [], "Too many blobs"
    if len(blobs) <= 1:
        return [], "Only one blob"
    elif max_size <= 1:
        return [], "All blobs are dots"
    return blobs, ""


# TODO Review
def get_blob(marked, start):
    M, N = marked.shape
    pts = [(*start, marked[start])]
    marked[start] = cst.MARKED_COLOR
    idx = 0
    while idx < len(pts):
        c_row, c_col, _ = pts[idx]
        idx += 1
        for dr, dc in cst.ALL_STEPS:
            new_r, new_c = (c_row + dr, c_col + dc)
            if 0 <= new_r < M and 0 <= new_c < N:
                if marked[new_r][new_c] != cst.MARKED_COLOR:
                    pts.append((new_r, new_c, marked[new_r][new_c]))
                    marked[new_r][new_c] = cst.MARKED_COLOR
    return pts


# @nb.njit
def _eval_mesh(grid: np.ndarray, stride: int) -> tuple[int, float]:
    """Compiled subroutine to measure order in a strided grid"""
    R, C = grid.shape
    hits = 0
    for j in range(stride):
        active_mesh = grid[j::stride]
        rebase = (active_mesh + (cst.N_COLORS * np.arange(C))).ravel()
        cts = np.bincount(rebase, minlength=cst.N_COLORS * C).reshape(C, -1).T
        for k in range(C):
            hits += np.max(cts[:, k])
    # We adjust the order measurement to unbias larger order params.
    # A given order defect will fractionally count against a smaller grid more,
    # so without adjusting we will end up favoring larger order strides.
    # NOTE: The current fractional power isn't rigorously motivated...
    order = np.power(hits / grid.size, stride / R)
    return (stride, order)


def _skewroll_grid(grid: np.ndarray, skew: tuple[int, int]) -> np.ndarray:
    if 0 in skew:
        log.warning("_skewroll_grid doesn't support uniform rolling")
    result = np.ones(grid.shape, dtype=int)
    for idx, row in enumerate(grid):
        result[idx] = np.roll(row, idx * skew[1] // skew[0])

    return result


def translational_order(grid: np.ndarray, row_axis: bool) -> list[tuple[int, float]]:
    """Measure and rank the order for every 2D stride"""
    grid = grid if row_axis else grid.T
    params = []
    if grid.shape[0] == 1:
        return [(1, 1)]
    for stride in range(1, grid.shape[0] // 2 + 1):
        params.append(_eval_mesh(grid, stride))
    return sorted(params, key=lambda x: x[1], reverse=True)
