import pytest
from arc.actions import Actions
from arc.grid_methods import gridify
from arc.inventory import Inventory
from arc.object import Object
from arc.types import BoardData, Grid


@pytest.fixture(scope="module")
def board_data_3x3() -> BoardData:
    return [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]


@pytest.fixture(scope="module")
def grid3x3(board_data_3x3: BoardData) -> Grid:
    return gridify(board_data_3x3)


def test_translation():
    """Test changes in location for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(2, 1, 1)
    delta = Inventory.invert(dot1, dot2)
    assert delta.transform.code == "t1,0"

    dot3 = Object(1, 2, 1)
    delta = Inventory.invert(dot1, dot3)
    assert delta.transform.code == "t0,1"

    delta = Inventory.invert(dot2, dot3)
    assert delta.transform.code == "t-1,1"


def test_recoloring():
    """Test changes in color for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 4)
    delta = Inventory.invert(dot1, dot2)
    assert delta.transform.code == "c4"


def test_rotation(grid3x3: Grid):
    """Test if rotations, reflections are detected."""
    left = Object.from_grid(grid3x3)

    r90 = Actions.Rotate.act(Object.from_grid(grid3x3), 1)
    delta = Inventory.invert(left, r90)
    assert delta.transform.actions == [Actions.Orthogonal]
    assert delta.transform.args == [(0, 1)]

    r180 = Actions.Rotate.act(Object.from_grid(grid3x3), 2)
    delta = Inventory.invert(left, r180)
    assert delta.transform.actions == [Actions.Orthogonal]
    assert delta.transform.args == [(0, 2)]

    r270 = Actions.Rotate.act(Object.from_grid(grid3x3), 3)
    delta = Inventory.invert(left, r270)
    assert delta.transform.actions == [Actions.Orthogonal]
    assert delta.transform.args == [(0, 3)]


def test_reflection(grid3x3: Grid):
    """Test if rotations, reflections are detected."""
    left = Object.from_grid(grid3x3)

    vertical = Actions.Flip.act(Object.from_grid(grid3x3), 0)
    delta = Inventory.invert(left, vertical)
    assert delta.transform.actions == [Actions.Orthogonal]
    assert delta.transform.args == [(1, 0)]

    horizontal = Actions.Flip.act(Object.from_grid(grid3x3), 1)
    delta = Inventory.invert(left, horizontal)
    assert delta.transform.actions == [Actions.Orthogonal]
    # TODO We should make sure the simplest transform comes from inversion
    assert delta.transform.args == [(1, 2)]
