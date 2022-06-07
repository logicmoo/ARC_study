import pytest

from arc.actions import Actions
from arc.grid_methods import gridify
from arc.object import Object
from arc.link import ObjectDelta
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
    delta = ObjectDelta(dot1, dot2)
    assert delta.transform.code == "v1"

    dot3 = Object(1, 2, 1)
    delta = ObjectDelta(dot1, dot3)
    assert delta.transform.code == "h1"

    delta = ObjectDelta(dot2, dot3)
    assert delta.transform.code == "v-1h1"


def test_justification():
    """Test special translations, justifying an axis or zeroing both."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(0, 1, 1)
    delta = ObjectDelta(dot1, dot2)
    assert delta.transform.code == "j0"

    dot3 = Object(1, 0, 1)
    delta = ObjectDelta(dot1, dot3)
    assert delta.transform.code == "j1"

    dot4 = Object(0, 0, 1)
    delta = ObjectDelta(dot1, dot4)
    assert delta.transform.code == "z"


def test_recoloring():
    """Test changes in color for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 4)
    delta = ObjectDelta(dot1, dot2)
    assert delta.transform.code == "c4"


def test_rotation(grid3x3: Grid):
    """Test if rotations, reflections are detected."""
    left = Object.from_grid(grid3x3)

    r90 = Actions.Rotate.act(Object.from_grid(grid3x3), 1)
    delta = ObjectDelta(left, r90)
    assert delta.transform.actions == [Actions.Rotate]
    assert delta.transform.args == [(1,)]

    r180 = Actions.Rotate.act(Object.from_grid(grid3x3), 2)
    delta = ObjectDelta(left, r180)
    assert delta.transform.actions == [Actions.Rotate]
    assert delta.transform.args == [(2,)]

    r270 = Actions.Rotate.act(Object.from_grid(grid3x3), 3)
    delta = ObjectDelta(left, r270)
    assert delta.transform.actions == [Actions.Rotate]
    assert delta.transform.args == [(3,)]


def test_reflection(grid3x3: Grid):
    """Test if rotations, reflections are detected."""
    left = Object.from_grid(grid3x3)

    vertical = Actions.Flip.act(Object.from_grid(grid3x3), 0)
    delta = ObjectDelta(left, vertical)
    assert delta.transform.actions == [Actions.VFlip]
    assert delta.transform.args == [tuple()]

    horizontal = Actions.Flip.act(Object.from_grid(grid3x3), 1)
    delta = ObjectDelta(left, horizontal)
    assert delta.transform.actions == [Actions.HFlip]
    assert delta.transform.args == [tuple()]
