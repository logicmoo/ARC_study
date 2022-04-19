import numpy as np

from arc.grid_methods import (
    color_connect,
    gridify,
    norm_points,
    translational_order,
    mirror_order,
)
from arc.definitions import Constants as cst
from arc.types import Grid


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


def test_order():
    assert translational_order(gridify([[1]]), True) == [(1, 1)]

    tile2x2 = gridify([[1, 2], [3, 4]], (3, 3))
    assert (2, 2) == _get_leading_order(tile2x2)
    tile1x4 = gridify([[0, 1, 2, 3]], (8, 2))
    assert (1, 4) == _get_leading_order(tile1x4)
    tile2x5 = gridify([[0, 1, 2, 3, 4], [1, 2, 3, 4, 5]], (2, 2))
    assert (2, 5) == _get_leading_order(tile2x5)
    tile4x4 = gridify([np.arange(4) + i for i in range(4)], (2, 2))
    assert (4, 4) == _get_leading_order(tile4x4)
    assert (2, 2) == _get_leading_order(_disorder(tile2x2))
    assert (1, 4) == _get_leading_order(_disorder(tile1x4))
    assert (4, 4) == _get_leading_order(_disorder(tile4x4))


def test_mirror_order():
    tile4x4x2 = gridify([np.arange(4) + i for i in range(4)], (2, 2))
    assert mirror_order(tile4x4x2, False) == 0
    assert mirror_order(tile4x4x2, True) == 0

    tilebase = gridify([np.arange(4) + i for i in range(4)])
    row_mirrored = tilebase + tilebase[::-1]
    assert mirror_order(row_mirrored, True) == 1
    assert mirror_order(row_mirrored, False) == 0

    col_mirrored = np.concatenate([tilebase, tilebase[:, ::-1]], 1)
    assert mirror_order(col_mirrored, True) == 0
    assert mirror_order(col_mirrored, False) == 1
