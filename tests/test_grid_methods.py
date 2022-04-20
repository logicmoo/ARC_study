import numpy as np
import pytest

from arc.grid_methods import (
    color_connect,
    gridify,
    norm_points,
    rotational_order,
    translational_order,
    mirror_order,
)
from arc.definitions import Constants as cst
from arc.types import BoardData, Grid


@pytest.fixture(scope="module")
def grid3x3() -> BoardData:
    return [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]


@pytest.fixture(scope="module")
def tiled3x3(grid3x3: BoardData) -> Grid:
    return gridify(grid3x3, (2, 2))


@pytest.fixture(scope="module")
def mirror3x3(grid3x3: BoardData) -> Grid:
    grid = gridify(grid3x3)
    row_mirror = np.concatenate([grid, grid[::-1]], 0)  # type: ignore
    col_mirror = np.concatenate([row_mirror, row_mirror[:, ::-1]], 1)  # type: ignore
    return col_mirror


@pytest.fixture(scope="module")
def rotated3x3(grid3x3: BoardData) -> Grid:
    grid = gridify(grid3x3)
    left = np.concatenate([grid, np.rot90(grid)], 0)  # type: ignore
    full = np.concatenate([left, np.rot90(np.rot90(left))], 1)  # type: ignore
    return full


def test_norm_pts():
    pts = [(1, 1, 1), (3, 1, 1)]
    anchor, normed, mono = norm_points(pts)
    assert anchor == (1, 1)
    assert normed == [(0, 0, 1), (2, 0, 1)]
    assert mono == True


def test_color_connect():
    mc = cst.MARKED_COLOR
    grid = gridify([[1, mc, 1, mc, 1]])

    result, fail_msg = color_connect(grid.copy(), max_ct=2)
    assert result == []
    assert fail_msg == "Too many blobs"

    result, fail_msg = color_connect(grid.copy(), max_ct=3)
    assert result == []
    assert fail_msg == "All blobs are dots"

    grid = gridify([[1, 1, 1, 1, 1]])
    result, fail_msg = color_connect(grid.copy())
    assert result == []
    assert fail_msg == "Only one blob"

    grid = gridify([[1, 1, mc, 1, 1]])
    result, fail_msg = color_connect(grid.copy())
    assert fail_msg == ""
    assert result == [[(0, 0, 1), (0, 1, 1)], [(0, 3, 1), (0, 4, 1)]]


def _disorder(grid: Grid, anchor: int = 7):
    messy = grid.copy()
    rows, cols = grid.shape
    for ct in range(1, rows * cols, anchor):
        i, j = (ct // cols) % rows, ct % cols
        messy[i, j] = (messy[i, j] + 1) % 11
    return messy


def _get_leading_order(grid: Grid):
    row_o = translational_order(grid, True)
    col_o = translational_order(grid, False)
    return (row_o[0][0], col_o[0][0])


def test_order(tiled3x3: Grid):
    assert translational_order(gridify([[1]]), True) == [(1, 1)]

    tiled2x2 = gridify([[1, 2], [3, 4]], (3, 3))
    assert (2, 2) == _get_leading_order(tiled2x2)
    tiled1x4 = gridify([[0, 1, 2, 3]], (8, 2))
    assert (1, 4) == _get_leading_order(tiled1x4)
    tiled2x5 = gridify([[0, 1, 2, 3, 4], [1, 2, 3, 4, 5]], (2, 2))
    assert (2, 5) == _get_leading_order(tiled2x5)
    assert (3, 3) == _get_leading_order(tiled3x3)
    assert (2, 2) == _get_leading_order(_disorder(tiled2x2))
    assert (1, 4) == _get_leading_order(_disorder(tiled1x4))
    assert (3, 3) == _get_leading_order(_disorder(tiled3x3))


def test_mirror_order(tiled3x3: Grid, mirror3x3: Grid, rotated3x3: Grid):
    assert 1 / 3 == mirror_order(tiled3x3, row_axis=False)
    assert 1 / 3 == mirror_order(tiled3x3, row_axis=True)
    assert 1 / 3 == mirror_order(rotated3x3, row_axis=True)
    assert 1 / 3 == mirror_order(rotated3x3, row_axis=False)
    assert 1 == mirror_order(mirror3x3, row_axis=True)
    assert 1 == mirror_order(mirror3x3, row_axis=False)


def test_rotational_order(tiled3x3: Grid, mirror3x3: Grid, rotated3x3: Grid):
    assert (3, 1 / 9) == rotational_order(tiled3x3)
    assert (3, 1 / 3) == rotational_order(mirror3x3)
    assert (3, 1) == rotational_order(rotated3x3)
