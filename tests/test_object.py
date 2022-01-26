import numpy as np

from arc.object import Object
from arc.definitions import Constants as cst
from arc.generator import Generator


def test_basics():
    """Test the simple properties of objects: row, column, color, inheritance."""
    dot1 = Object()
    assert dot1.loc == (0, 0)
    assert dot1.seed == (0, 0, cst.NULL_COLOR)
    assert dot1.shape == (1, 1)
    assert dot1.size == 1
    assert dot1.category == "Dot"

    cluster1 = Object(1, 1, 1, children=[Object(0, 0, 2), Object(1, 1)])
    assert cluster1.seed == (1, 1, 1)
    assert (cluster1.grid == np.array([[2, cst.NULL_COLOR], [cst.NULL_COLOR, 1]])).all()
    assert cluster1.shape == (2, 2)
    assert cluster1.size == 2
    assert cluster1.category == "Cluster"

    deep1 = Object(children=[Object(1, 1, children=[Object(1, 1, 1)])])
    assert deep1.points == {(2, 2): 1}


def test_overlap():
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 2, children=[dot1, Object(1, 1)])
    assert dot2.points == {(1, 1): 2}


def test_points_constructor():
    obj = Object.from_points([(1, 1, 1)])
    assert obj == Object(1, 1, 1)


def test_grid_constructor():
    grid = np.array([[0, 1], [1, 0]])
    obj = Object.from_grid(grid)
    assert obj.seed == (0, 0, cst.NULL_COLOR)
    assert obj.points == {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 0}
    assert obj.shape == (2, 2)
    assert obj.size == 4


def test_comparisons():
    """Test operators between objects"""
    # Two different ways of defining a dot at (1, 1) (with different colors)
    # NOTE One might decide to enforce dot2 to "normalize" during construction
    # such that it flattens. Unclear whether this matters...
    dot1 = Object(1, 1, 1)
    dot2 = Object(1, 1, 2, children=[Object()])
    assert dot1 != dot2
    assert not dot1.sim(dot2)
    assert dot1.sil(dot2)
    assert dot1 < dot2  # Compares seed (here color is smaller)

    # Two adjacent pointsdefined different ways, obj3 is translated
    obj1 = Object.from_grid(np.array([[0, 1]]))
    obj2 = Object(children=[Object(color=0), Object(col=1, color=1)])
    obj3 = Object(1, children=[Object(color=0), Object(0, 1, 1)])
    assert obj1 == obj2
    assert not obj1 < obj2
    assert obj1 != obj3
    assert obj1.sim(obj3)
    assert obj1.sil(obj3)
    assert obj1 < obj3  # Compares seed (here row is smaller)

    # Compare the first children of these objects
    assert obj2[0] == obj3[0]

    assert dot1.issubset(obj3)
    # dot1 has 1 point compared to obj1's 2
    assert dot1 < obj1
    # same size, but obj1's shape is (1, 2) < (2, 1) of obj2
    assert obj1 < Object.from_grid(np.array([[0], [1]]))


def test_simple_flatten():
    l2 = Object(1, 1, color=1)
    l1 = Object(1, 1, children=[l2])
    l0 = Object(children=[l1])

    flat = l0.flatten()
    assert flat.points == {(2, 2): 1}
    assert flat.children[0].children == []


def test_deep_flatten():
    l31 = Object(color=3, generator=Generator.from_codes(["R2"]))
    l32 = Object(0, 1, 4, generator=Generator.from_codes(["R2"]))
    l21 = Object(color=2, generator=Generator.from_codes(["R2"]))
    l22 = Object(0, 1, children=[l31, l32])
    l11 = Object(color=1, generator=Generator.from_codes(["R2"]))
    l12 = Object(0, 1, children=[l21, l22])
    l0 = Object(children=[l11, l12])

    flat = l0.flatten()
    assert np.array_equal(l0.grid, flat.grid)
    assert len(flat.children) == 4
    for child in flat.children:
        assert child.category == "Line"
