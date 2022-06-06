from arc.actions import Actions

from arc.object import Object
from arc.transform import Transform
from arc.grid_methods import gridify, grid_equal


def test_transform():
    obj = Object(1, 1, 1)
    trans = Transform([Actions.Horizontal, Actions.Vertical], args=[(-1,), (-1,)])
    assert trans.apply(obj) == Object(0, 0, 1)

    trans = Transform([Actions.Zero], args=[])
    assert trans.args == [tuple()]


def test_codes():
    obj = Object(codes={"V": 1, "H": 2, "O": 0})
    assert obj.char == "HV"


def test_line():
    line = Object(color=2, codes={"H": 9})
    true_grid = gridify([[2]], (1, 10))
    assert grid_equal(line.grid, true_grid)


def test_rectangle():
    square1 = Object(color=1, codes={"H": 2, "V": 2})
    true_grid = gridify([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
    assert grid_equal(square1.grid, true_grid)


def test_chessboard():
    tile_data = [[1, 0], [0, 1]]
    tile2x2 = Object.from_grid(tile_data)
    cb = Object(children=[tile2x2], codes={"H": 3, "V": 3})
    assert grid_equal(cb.grid, gridify(tile_data, (4, 4)))


def test_deep_generators():
    children = [
        Object(0, 0, 1, codes={"H": 2, "V": 1}),
        Object(2, 0, 2, codes={"H": 1, "V": 2}),
        Object(0, 3, 3, codes={"H": 1, "V": 2}),
        Object(3, 2, 4, codes={"H": 2, "V": 1}),
        Object(2, 2, 6),
    ]
    board = Object(children=children, codes={"H": 2, "V": 2})

    true_grid = gridify(
        [
            [1, 1, 1, 3, 3],
            [1, 1, 1, 3, 3],
            [2, 2, 6, 3, 3],
            [2, 2, 4, 4, 4],
            [2, 2, 4, 4, 4],
        ],
        (3, 3),
    )
    assert grid_equal(board.grid, true_grid)
