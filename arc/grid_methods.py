from collections import Counter

import numpy as np

from arc.util import logger
from arc.definitions import Constants as cst

log = logger.fancy_logger("GridMethods", level=30)

from arc.types import Grid, Point, PointDict, PointList, Position


def gridify(data: Grid | list[list[int]], tile: tuple[int, int] = (1, 1)) -> Grid:
    if hasattr(data, "shape"):
        return data  # type: ignore
    return np.tile(data, tile)  # type: ignore


def grid_overlap(left: Grid, right: Grid) -> float:
    return np.sum(left == right) / left.size  # type: ignore


def grid_equal(left: Grid, right: Grid) -> bool:
    return np.array_equal(left, right)  # type: ignore


def norm_points(points: PointList) -> tuple[Position, PointList, bool]:
    """Calculate the anchor (min row and col) of a list of points and norm them.

    Returns a tuple: anchor coordinates, materialized point list.
    """
    minrow, mincol = cst.MAX_ROWS, cst.MAX_COLS
    monochrome = True
    color = points[0][2]
    for pt in points:
        minrow = min(minrow, pt[0])
        mincol = min(mincol, pt[1])
        if color != pt[2]:
            monochrome = False
    result: PointList = []
    for pt in points:
        result.append((pt[0] - minrow, pt[1] - mincol, pt[2]))
    return (minrow, mincol), result, monochrome


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


# def intersect(grids: list[np.ndarray]) -> np.ndarray:
#     """WIP"""
#     base = grids[0].copy()
#     for comp in grids[1:]:
#         if base.shape != comp.shape:
#             base[:, :] = cst.MARKED_COLOR
#             return base
#         base[base != comp] = cst.MARKED_COLOR
#     return base


# def expand(grid: np.ndarray, mult: tuple[int, int]) -> np.ndarray:
#     M, N = grid.shape
#     out = np.full((M * mult[0], N * mult[1]), -1)
#     for i in range(M):
#         rows = slice(i * mult[0], (i + 1) * mult[0], 1)
#         for j in range(N):
#             cols = slice(j * mult[1], (j + 1) * mult[1], 1)
#             out[rows, cols] = grid[i, j]
#     return out


# TODO Review
def color_connect(marked: Grid, max_ct: int = 10) -> tuple[list[PointList], str]:
    """Try connecting groups of points based on colors

    If we only produce 1 group, or more than max_ct, we Fail.
    If all groups are only size 1, we Fail.
    """
    blobs: list[PointList] = []
    max_size = 0
    for start in zip(*np.where(marked != cst.MARKED_COLOR)):  # type: ignore
        if marked[start] == cst.MARKED_COLOR:
            continue
        pts = get_blob(marked, start)  # type: ignore
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
def get_blob(marked: Grid, start: Position) -> PointList:
    M, N = marked.shape
    pts: PointList = [(*start, marked[start])]
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


# @logger.log_call(log, "warning", ignore_idxs={0})
def eval_mesh(
    grid: Grid,
    row_stride: int,
    col_stride: int,
    remove_noise: bool = True,
    ignore_colors: list[int] | None = None,
) -> list[Point]:
    """Count how many times each color shows up in a sub-mesh.

    Define a sub-mesh from a grid by starting from a position (i, j) and moving by
    a stride amount in the row or col directions. Count the occurrences of each
    color in this mesh and choose the most frequent.

    If 'remove_noise' is True, and any 'noise' color is detected (used in the
    unit cell but also present during other positions where it isn't used),
    'eval_mesh' is called again and will attempt to ignore those colors.
    """
    ignored: list[int] = ignore_colors or []
    cell_pts: list[Point] = []
    noise_cts: list[int] = [0] * cst.N_COLORS
    used_cts: list[int] = [0] * cst.N_COLORS

    for i in range(row_stride):
        for j in range(col_stride):
            cts = Counter(grid[i::row_stride, j::col_stride].ravel())
            color_stats = cts.most_common()  # most_common() -> [(key, ct), ...]
            use_idx = 0
            while color_stats[use_idx][0] in ignored:
                if use_idx == len(color_stats) - 1:
                    break
                use_idx += 1
            best_color = color_stats[use_idx][0]
            used_cts[best_color] += color_stats[use_idx][1]
            for item in color_stats[use_idx + 1 :]:
                noise_cts[item[0]] += item[1]
            cell_pts.append((i, j, best_color))

    if remove_noise:
        ignored: list[int] = []
        for color, (used, noise) in enumerate(zip(used_cts, noise_cts)):
            if used and noise and (noise / (used + noise)) > 0.5:
                ignored.append(color)
        if ignored:
            return eval_mesh(
                grid,
                row_stride,
                col_stride,
                remove_noise=False,
                ignore_colors=ignored,
            )

    return cell_pts


# @nb.njit  # (Numba JIT can speed this up)
def _eval_row_mesh(grid: Grid, stride: int) -> tuple[int, float]:
    """Compiled subroutine to measure row order in a strided grid"""
    R, _ = grid.shape
    hits = 0
    for j in range(stride):
        active_mesh = grid[:, j::stride]
        for row in active_mesh:
            hits += Counter(row).most_common()[0][1]
    # We adjust the order measurement to unbias larger order params.
    # A given order defect will fractionally count against a smaller grid more,
    # so without adjusting we will end up favoring larger order strides.
    # NOTE: The current fractional power isn't rigorously motivated...
    order = np.power(hits / grid.size, stride / R)
    return (stride, order)


# TODO WIP
# def _skewroll_grid(grid: np.ndarray, skew: tuple[int, int]) -> np.ndarray:
#     if 0 in skew:
#         log.warning("_skewroll_grid doesn't support uniform rolling")
#     result = np.ones(grid.shape, dtype=int)
#     for idx, row in enumerate(grid):
#         result[idx] = np.roll(row, idx * skew[1] // skew[0])

#     return result


def translational_order(grid: Grid, row_axis: bool) -> list[tuple[int, float]]:
    """Measure the order along an axis for every stride value."""
    grid = grid.T if row_axis else grid
    params: list[tuple[int, float]] = []
    if grid.shape[1] == 1:
        return [(1, 1)]
    for stride in range(1, grid.shape[1] // 2 + 1):
        params.append(_eval_row_mesh(grid, stride))
    return sorted(params, key=lambda x: x[1], reverse=True)


def mirror_order(grid: Grid, row_axis: bool) -> float:
    """Measure the level of mirror symmetry."""
    grid = grid if row_axis else grid.T
    return grid_overlap(np.flip(grid, 0), grid)  # type: ignore


def rotational_order(grid: Grid) -> tuple[int, float]:
    """Measure the level of rotational symmetry."""
    r90 = np.rot90(grid)  # type: ignore
    r180 = np.rot90(r90)  # type: ignore
    r270 = np.rot90(r180)  # type: ignore
    return max([(ct, grid_overlap(rot, grid)) for ct, rot in [(1, r90), (2, r180), (3, r270)]])  # type: ignore
