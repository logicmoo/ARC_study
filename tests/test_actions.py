from arc.object import Object
from arc.concepts import Action


def test_actions():
    """Test each action on Objects"""
    pt1 = Object(1, 1, 1)
    pt2 = Action.right(pt1)
    assert pt2 == Object(1, 2, 1)
    assert pt2 != pt1

    pt3 = Action.left(Action.right(Action.down(Action.up(pt1))))
    assert pt3 == pt1
    assert pt3 != pt2
