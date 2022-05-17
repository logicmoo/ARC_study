import numpy as np
import pytest

from arc.grid_methods import (
    connect,
    get_boundary,
    gridify,
    norm_points,
    rotational_order,
    translational_order,
    mirror_order,
)
from arc.definitions import Constants as cst
from arc.types import BoardData, Grid


@pytest.fixture(scope="module")
def board_data_3x3() -> BoardData:
    return [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]


@pytest.fixture(scope="module")
def tiled3x3(board_data_3x3: BoardData) -> Grid:
    return gridify(board_data_3x3, (2, 2))


@pytest.fixture(scope="module")
def mirror3x3(board_data_3x3: BoardData) -> Grid:
    grid = gridify(board_data_3x3)
    row_mirror = np.concatenate([grid, grid[::-1]], 0)  # type: ignore
    col_mirror = np.concatenate([row_mirror, row_mirror[:, ::-1]], 1)  # type: ignore
    return col_mirror


@pytest.fixture(scope="module")
def rotated3x3(board_data_3x3: BoardData) -> Grid:
    grid = gridify(board_data_3x3)
    left = np.concatenate([grid, np.rot90(grid)], 0)  # type: ignore
    full = np.concatenate([left, np.rot90(np.rot90(left))], 1)  # type: ignore
    return full


def test_norm_pts():
    pts = [(1, 1, 1), (3, 1, 1)]
    anchor, normed, mono = norm_points(pts)
    assert anchor == (1, 1)
    assert normed == [(0, 0, 1), (2, 0, 1)]
    assert mono == True


def test_connect():
    mc = cst.MARKED_COLOR
    grid = gridify([[1, mc, 1, mc, 1]])

    result = connect(grid.copy())
    assert result == [[(0, 0, 1)], [(0, 2, 1)], [(0, 4, 1)]]

    grid = gridify([[1, 1, 1, 1, 1]])
    result = connect(grid.copy())
    assert result == [[(0, i, 1) for i in range(5)]]

    grid = gridify([[1, 1, mc, 1, 1]])
    result = connect(grid.copy())
    assert result == [[(0, 0, 1), (0, 1, 1)], [(0, 3, 1), (0, 4, 1)]]


def test_get_boundary():
    nc = cst.NULL_COLOR
    grid = gridify([[1, 1, 1], [1, nc, 1], [1, 1, 1]])
    bounds, enclosed = get_boundary(grid)
    assert bounds == [
        (0, 0, 1),
        (0, 2, 1),
        (1, 0, 1),
        (1, 2, 1),
        (2, 0, 1),
        (2, 2, 1),
        (0, 1, 1),
        (2, 1, 1),
    ]
    assert enclosed == [(1, 1)]

    # Task 2 scene 3 green points
    grid = gridify(
        [
            [3, 3, 3, 3, nc, nc, nc, nc],
            [3, nc, nc, 3, nc, nc, nc, nc],
            [3, nc, nc, 3, nc, 3, nc, nc],
            [3, 3, 3, 3, 3, 3, 3, nc],
            [nc, 3, nc, nc, nc, nc, 3, nc],
            [nc, 3, nc, nc, nc, 3, 3, nc],
            [nc, 3, 3, nc, nc, 3, nc, 3],
            [nc, 3, nc, 3, nc, nc, 3, nc],
            [nc, nc, 3, nc, nc, nc, nc, nc],
        ]
    )
    bounds, enclosed = get_boundary(grid)
    assert sorted(bounds) == [
        (0, 0, 3),
        (0, 1, 3),
        (0, 2, 3),
        (0, 3, 3),
        (1, 0, 3),
        (1, 3, 3),
        (2, 0, 3),
        (2, 3, 3),
        (2, 5, 3),
        (3, 0, 3),
        (3, 2, 3),
        (3, 3, 3),
        (3, 4, 3),
        (3, 5, 3),
        (3, 6, 3),
        (4, 1, 3),
        (4, 6, 3),
        (5, 1, 3),
        (5, 5, 3),
        (5, 6, 3),
        (6, 1, 3),
        (6, 2, 3),
        (6, 5, 3),
        (6, 7, 3),
        (7, 1, 3),
        (7, 3, 3),
        (7, 6, 3),
        (8, 2, 3),
    ]
    assert enclosed == [(1, 1), (1, 2), (2, 1), (2, 2), (6, 6), (7, 2)]


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
