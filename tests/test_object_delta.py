from arc.board import default_comparisons
from arc.object import Object, ObjectDelta


def test_translation():
    """Test changes in location for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(2, 1, 1)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.generator.codes == ["s1"]

    dot3 = Object(1, 2, 1)
    delta = ObjectDelta(dot1, dot3, default_comparisons)
    assert delta.generator.codes == ["w1"]

    delta = ObjectDelta(dot2, dot3, default_comparisons)
    assert delta.generator.codes == ["s-1", "w1"]


def test_justification():
    """Test special translations, justifying an axis or zeroing both."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(0, 1, 1)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.generator.codes == ["j0"]

    dot3 = Object(1, 0, 1)
    delta = ObjectDelta(dot1, dot3, default_comparisons)
    assert delta.generator.codes == ["j1"]

    dot4 = Object(0, 0, 1)
    delta = ObjectDelta(dot1, dot4, default_comparisons)
    assert delta.generator.codes == ["z"]


def test_recoloring():
    """Test changes in color for a given object."""
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 4)
    delta = ObjectDelta(dot1, dot2, default_comparisons)
    assert delta.generator.codes == ["c4"]
