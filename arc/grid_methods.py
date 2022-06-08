from collections import Counter
from typing import Callable

import numpy as np

from arc.definitions import Constants as cst
from arc.util import logger

log = logger.fancy_logger("GridMethods", level=30)

from arc.types import (
    Grid,
    PointDict,
    PointList,
    Position,
    PositionList,
    PositionSet,
    Shape,
)


def gridify(data: Grid | list[list[int]], tile: tuple[int, int] = (1, 1)) -> Grid:
    if hasattr(data, "shape"):
        return data  # type: ignore
    return np.tile(data, tile)  # type: ignore


def grid_overlap(left: Grid, right: Grid) -> float:
    return np.sum(left == right) / left.size  # type: ignore


def grid_equal(left: Grid, right: Grid) -> bool:
    return np.array_equal(left, right)  # type: ignore


def norm_points(points: PointDict) -> tuple[Position, PointDict, bool]:
    """Calculate the anchor (min row and col) of a list of points and norm them.

    Returns a tuple: anchor coordinates, materialized point list.
    """
    minrow, mincol = cst.MAX_ROWS, cst.MAX_COLS
    monochrome = True
    first_color = list(points.values())[0]
    for (row, col), color in points.items():
        minrow = min(minrow, row)
        mincol = min(mincol, col)
        if first_color != color:
            monochrome = False
    result: PointDict = {}
    for (row, col), color in points.items():
        result[(row - minrow, col - mincol)] = color
    return (minrow, mincol), result, monochrome


def shift_locs(locs: PositionSet, ref_loc: Position) -> PositionList:
    """Subtract a vector from a list of positions."""
    new_locs: PositionList = []
    for loc in locs:
        new_loc = (loc[0] - ref_loc[0], loc[1] - ref_loc[1])
        if new_loc[0] > 0 and new_loc[1] > 0:
            new_locs.append(new_loc)
    return new_locs


def point_filter(points: PointDict, color: int) -> tuple[PointDict, PointDict]:
    """Filter out a single color from a grid."""
    match_pts: PointDict = {}
    other_pts: PointDict = {}
    for loc, val in points.items():
        if val == color:
            match_pts[loc] = val
        else:
            other_pts[loc] = val
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


def connect(marked: Grid, max_ct: int = 10) -> list[PointDict]:
    """Connect any objects based on point adjacency."""
    M, N = marked.shape
    blobs: list[PointDict] = []
    for start in zip(*np.where(marked != cst.MARKED_COLOR)):  # type: ignore
        if marked[start] == cst.MARKED_COLOR:
            continue
        # Find all points connected to the start point
        pts: PointList = [(*start, marked[start])]  # type: ignore
        marked[start] = cst.MARKED_COLOR
        idx = 0
        while idx < len(pts):
            c_row, c_col, _ = pts[idx]
            idx += 1
            for dr, dc in cst.ALL_STEPS:
                new_r, new_c = (c_row + dr, c_col + dc)
                if (
                    0 <= new_r < M
                    and 0 <= new_c < N
                    and marked[new_r][new_c] != cst.MARKED_COLOR
                ):
                    pts.append((new_r, new_c, marked[new_r][new_c]))
                    marked[new_r][new_c] = cst.MARKED_COLOR
        blobs.append({(row, col): color for row, col, color in pts})

        blobs = sorted(blobs, key=lambda x: len(x), reverse=True)
    return blobs


def get_boundary(grid: Grid) -> tuple[PointList, PositionList]:
    """Determine all points on the outside surface of a 2D grid."""
    M, N = grid.shape
    if M == 1 or N == 1:
        log.error("Object.bound_info should handle cases with small shape parameters.")
    marked = grid.copy()
    bound_pts: PointList = []
    queue: PositionList = []
    # The following two for loops check the bounding box of the Object. If the point is part
    # of the object, it is added to the boundary, else it is queued for flood fill.
    for row in range(M):
        for pt in [(row, 0), (row, N - 1)]:
            if marked[pt] == cst.NULL_COLOR:
                queue.append(pt)
            else:
                bound_pts.append((*pt, marked[pt]))
            marked[pt] = cst.MARKED_COLOR
    for col in range(1, N - 1):
        for pt in [(0, col), (M - 1, col)]:
            if marked[pt] == cst.NULL_COLOR:
                queue.append(pt)
            else:
                bound_pts.append((*pt, marked[pt]))
            marked[pt] = cst.MARKED_COLOR

    # For each queue point, look at all neighbors, assign to queue if transparent
    # and assign to boundary (not queue) if it has a color.
    while queue:
        c_row, c_col = queue.pop()
        for dr, dc in cst.STEPS_BASE:
            new_r, new_c = (c_row + dr, c_col + dc)
            if 0 <= new_r < M and 0 <= new_c < N:
                if marked[new_r][new_c] != cst.MARKED_COLOR:
                    if marked[new_r][new_c] == cst.NULL_COLOR:
                        queue.append((new_r, new_c))
                    else:
                        bound_pts.append((new_r, new_c, marked[new_r][new_c]))
                    marked[new_r][new_c] = cst.MARKED_COLOR

    # Enclosed points are points not part of the Object but contained in its
    # boundary. They are the leftover transparent points after the exterior flood.
    enclosed_locs: PositionList = []
    for row, col in zip(*np.where(marked == cst.NULL_COLOR)):  # type: ignore
        enclosed_locs.append((row, col))  # type: ignore

    return bound_pts, enclosed_locs


def tile_mesh_func(grid: Grid, cell_shape: Shape, loc: Position) -> list[int]:
    row, col = loc
    row_stride, col_stride = cell_shape
    return grid[row::row_stride, col::col_stride].ravel()  # type: ignore


# @logger.log_call(log, "warning", ignore_idxs={0})
def eval_mesh(
    grid: Grid,
    cell_shape: Shape,
    mesh_func: Callable[[Grid, Shape, Position], list[int]],
    remove_noise: bool = True,
    ignore_colors: list[int] | None = None,
) -> PointDict:
    """Count how many times each color shows up in a sub-mesh.

    Define a sub-mesh from a grid by starting from a position (i, j) and moving by
    a stride amount in the row or col directions. Count the occurrences of each
    color in this mesh and choose the most frequent.

    If 'remove_noise' is True, and any 'noise' color is detected (used in the
    unit cell but also present during other positions where it isn't used),
    'eval_mesh' is called again and will attempt to ignore those colors.
    """
    ignored: list[int] = ignore_colors or [cst.NULL_COLOR]
    cell_pts: PointDict = {}
    noise_cts: list[int] = [0] * cst.N_COLORS
    used_cts: list[int] = [0] * cst.N_COLORS

    row_stride, col_stride = cell_shape
    for i in range(row_stride):
        for j in range(col_stride):
            cts = Counter(mesh_func(grid, cell_shape, (i, j)))
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
            if best_color != cst.NULL_COLOR:
                cell_pts[i, j] = best_color

    if remove_noise:
        for color, (used, noise) in enumerate(zip(used_cts, noise_cts)):
            if used and noise and (noise / (used + noise)) > 0.5:
                ignored.append(color)
        if ignored:
            return eval_mesh(
                grid,
                cell_shape,
                mesh_func,
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
    # TODO Temporary, look into this...
    order = np.power(hits / grid.size, max(0.5, stride / R))  # type: ignore
    return (stride, order)  # type: ignore


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
