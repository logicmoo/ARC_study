from arc.actions import Actions

from arc.object import Object
from arc.generator import Generator, Transform
from arc.definitions import Constants as cst
from arc.grid_methods import gridify, grid_equal


def test_transform():
    obj = Object(1, 1, 1)
    trans = Transform([Actions.Horizontal, Actions.Vertical], args=[(-1,), (-1,)])
    assert trans.apply(obj) == Object(0, 0, 1)

    trans = Transform([Actions.Zero], args=[])
    assert trans.args == [tuple()]


def test_codes():
    gen = Generator.from_codes(("zVm2,3*9", "j1z"))
    assert gen.char == "Vjmz"


def test_line():
    gen = Generator.from_codes(("H*9",))
    line = Object(color=2, generator=gen)
    true_grid = gridify([[2]], (1, 10))
    assert grid_equal(line.grid, true_grid)


def test_rectangle():
    gen = Generator.from_codes(("H*2", "V*2"))
    square1 = Object(color=1, generator=gen)
    true_grid = gridify([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
    assert grid_equal(square1.grid, true_grid)

    rev_gen = Generator.from_codes(("V*2", "H*2"))
    square2 = Object(color=1, generator=rev_gen)
    assert square1 == square2


def test_chessboard():
    tile_data = [[1, 0], [0, 1]]
    tile2x2 = Object.from_grid(tile_data)
    gen = Generator.from_codes(("V*3", "H*3"))
    cb = Object(children=[tile2x2], generator=gen)
    assert grid_equal(cb.grid, gridify(tile_data, (4, 4)))


def test_3x_generator():
    checked = Generator.from_codes(("v1h1*1", "v2*1", "h2*1"))
    obj = Object(color=1, generator=checked)
    true_grid = gridify([[1, cst.NULL_COLOR], [cst.NULL_COLOR, 1]], (2, 2))
    assert obj.category == "Compound"
    assert grid_equal(obj.grid, true_grid)


def test_deep_generators():
    rect1_gen = Generator.from_codes(("V*2", "H*1"))
    rect2_gen = Generator.from_codes(("V*1", "H*2"))
    sq_gen = Generator.from_codes(("V*2", "H*2"))
    children = [
        Object(0, 0, 1, generator=rect2_gen),
        Object(2, 0, 2, generator=rect1_gen),
        Object(0, 3, 3, generator=rect1_gen),
        Object(3, 2, 4, generator=rect2_gen),
        Object(2, 2, 6),
    ]
    board = Object(children=children, generator=sq_gen)

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
