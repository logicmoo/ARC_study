from arc.board import default_comparisons
from arc.object import Object
from arc.object_delta import ObjectDelta


def test_translation():
    """Test changes in location for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(2, 1, 1)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.transform.code == "w1"

    dot3 = Object(1, 2, 1)
    delta = ObjectDelta(dot1, dot3, default_comparisons)
    assert delta.transform.code == "s1"

    delta = ObjectDelta(dot2, dot3, default_comparisons)
    assert delta.transform.code == "w-1s1"


def test_justification():
    """Test special translations, justifying an axis or zeroing both."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(0, 1, 1)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.transform.code == "j0"

    dot3 = Object(1, 0, 1)
    delta = ObjectDelta(dot1, dot3, default_comparisons)
    assert delta.transform.code == "j1"

    dot4 = Object(0, 0, 1)
    delta = ObjectDelta(dot1, dot4, default_comparisons)
    assert delta.transform.code == "z"


def test_recoloring():
    """Test changes in color for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 4)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.transform.code == "c4"
