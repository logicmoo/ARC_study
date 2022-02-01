import numpy as np

from arc.grid_methods import color_connect, norm_points, translational_order
from arc.definitions import Constants as cst


def test_norm_pts():
    pts = [(1, 1, 1), (3, 1, 1)]
    anchor, normed, mono = norm_points(pts)
    assert anchor == (1, 1)
    assert normed == [(0, 0, 1), (2, 0, 1)]
    assert mono == True


def test_color_connect():
    mc = cst.MARKED_COLOR
    grid = np.array([[1, mc, 1, mc, 1]])

    result, fail_msg = color_connect(grid.copy(), max_ct=2)
    assert result == []
    assert fail_msg == "Too many blobs"

    result, fail_msg = color_connect(grid.copy(), max_ct=3)
    assert result == []
    assert fail_msg == "All blobs are dots"

    grid = np.array([[1, 1, 1, 1, 1]])
    result, fail_msg = color_connect(grid.copy())
    assert result == []
    assert fail_msg == "Only one blob"

    grid = np.array([[1, 1, mc, 1, 1]])
    result, fail_msg = color_connect(grid.copy())
    assert fail_msg == ""
    assert result == [[(0, 0, 1), (0, 1, 1)], [(0, 3, 1), (0, 4, 1)]]


def _disorder(grid, anchor=7):
    messy = grid.copy()
    rows, cols = grid.shape
    for ct in range(1, rows * cols, anchor):
        i, j = (ct // cols) % rows, ct % cols
        messy[i, j] = (messy[i, j] + 1) % 11
    return messy


def _get_leading_order(grid):
    row_o = translational_order(grid, True)
    col_o = translational_order(grid, False)
    return (row_o[0][0], col_o[0][0])


def test_order():
    assert translational_order(np.array([[1]]), True) == [(1, 1)]

    tile2x2 = np.tile([[1, 2], [3, 4]], (3, 3))
    assert (2, 2) == _get_leading_order(tile2x2)
    tile1x4 = np.tile([np.arange(4)], (8, 2))
    assert (1, 4) == _get_leading_order(tile1x4)
    tile2x5 = np.tile([np.arange(5), np.arange(5) + 1], (2, 2))
    assert (2, 5) == _get_leading_order(tile2x5)
    tile4x4 = np.tile([np.arange(4) + i for i in range(4)], (2, 2))
    assert (4, 4) == _get_leading_order(tile4x4)
    assert (2, 2) == _get_leading_order(_disorder(tile2x2))
    assert (1, 4) == _get_leading_order(_disorder(tile1x4))
    assert (4, 4) == _get_leading_order(_disorder(tile4x4))
