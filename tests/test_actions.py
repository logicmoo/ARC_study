from arc.generator import Generator
from arc.object import Object
from arc.actions import chebyshev_vector
from arc.actions import Actions


def test_translations():
    """Test each action that translates an Object."""
    pt1 = Object(1, 1, 1)
    pt2 = Actions.HTile().act(pt1)
    assert pt2 == Object(1, 2, 1)
    assert pt2 != pt1

    # 'Konami' test :) (up down left right is idempotent)
    pt3 = Actions.Horizontal.act(
        Actions.Horizontal.act(
            Actions.Vertical.act(Actions.Vertical.act(pt1, -1), 1), -1
        ),
        1,
    )
    assert pt3 == pt1

    # Zeroing should be equivalent to justifying each axis
    assert Actions.Zero.act(pt1) == Actions.Justify.act(Actions.Justify.act(pt1, 0), 1)

    # Tiling ops translate based on the object size
    group = Object(children=[Object(0, 0, 1), pt1])
    assert Actions.VTile.act(group).loc == (2, 0)
    assert Actions.HTile.act(group).loc == (0, 2)
    assert Actions.Tile.act(group, 1, 1) == Actions.VTile.act(Actions.HTile.act(group))


def test_deformations():
    """Test scaling, skewing, etc of Objects."""
    # If there's no generator, just return a copy of the original object
    pt1 = Object(1, 1, 1)
    assert Actions.Scale.act(pt1, "V", 2) == pt1

    sq_gen = Generator.from_codes(("V*4", "H*4"))
    square = Object(1, 1, 1, generator=sq_gen)

    flat = Actions.VScale.act(square, 2)
    assert flat.loc == (1, 1)
    assert flat.shape == (3, 5)

    thin = Actions.HScale.act(square, 2)
    assert thin.loc == (1, 1)
    assert thin.shape == (5, 3)

    assert Actions.Scale.act(Actions.Scale.act(square, "R", 1), "R", 4) == square


def test_rotation():
    """Test object rotation."""
    # Turning a point should yield itself
    pt1 = Object(1, 1, 1)
    assert Actions.Turn.act(pt1, 1) == pt1

    # A monocolor line is symmetric under 180 deg rotation
    blue_line = Object(children=[Object(0, 0, 1), Object(1, 0, 1), Object(2, 0, 1)])
    assert Actions.Turn.act(blue_line, 1).shape == (1, 3)
    assert Actions.Turn.act(blue_line, 2) == blue_line

    composite = Object(children=[blue_line, pt1])
    assert Actions.Turn.act(composite, 1).shape == (2, 3)
    assert Actions.Turn.act(composite, 2).shape == (3, 2)
    assert Actions.Turn.act(composite, 2) != composite
    assert Actions.Turn.act(composite, 4) == composite


def test_reflection():
    """Test reflecting the Object over an axis."""
    pt1 = Object(1, 1, 1)
    assert Actions.VFlip.act(pt1) == pt1
    assert Actions.HFlip.act(pt1) == pt1

    group = Object(children=[Object(0, 0, 2), pt1])

    h_true_points = {(0, 1): 2, (1, 0): 1}
    assert Actions.HFlip.act(group).points == h_true_points

    v_true_points = {(0, 1): 1, (1, 0): 2}
    assert Actions.VFlip.act(group).points == v_true_points


def test_color():
    pt1 = Object(1, 1, 1)
    assert Actions.Paint.act(pt1, 2).color == 2
    assert Actions.Paint.act(Actions.Paint.act(pt1, 0), 1) == pt1


def test_resize():
    obj1 = Object(generator=Generator.from_codes(("V*5", "H*3")))
    obj2 = Object(2, 1, generator=Generator.from_codes(("V*1", "H*1")))
    obj3 = Object(generator=Generator.from_codes(("V*1", "H*1")))
    assert Actions.Resize.act(obj1, obj2) == obj3

    obj4 = Object(1, 5, generator=Generator.from_codes(("V*5", "H*1")))
    obj5 = Object(generator=Generator.from_codes(("V*5", "H*1")))
    assert Actions.Resize.act(obj1, obj4) == obj5

    obj6 = Object(generator=Generator.from_codes(("V*3", "H*3")))
    obj7 = Object(generator=Generator.from_codes(("V*3", "H*3")))
    assert Actions.Resize.act(obj1, obj6) == obj7


def test_chebyshev():
    obj1 = Object(5, 5, generator=Generator.from_codes(("V*2", "H*3")))
    obj2 = Object(2, 1, generator=Generator.from_codes(("V*1", "H*1")))
    assert chebyshev_vector(obj2, obj1) == (1, 0)
    assert chebyshev_vector(obj1, obj2) == (-1, 0)

    obj3 = Object(2, 1, generator=Generator.from_codes(("V*5", "H*1")))
    assert chebyshev_vector(obj3, obj1) == (0, 2)
    assert chebyshev_vector(obj1, obj3) == (0, -2)

    obj4 = Object(4, 4, generator=Generator.from_codes(("V*1", "H*2")))
    assert chebyshev_vector(obj1, obj4) == (0, 0)
    assert chebyshev_vector(obj4, obj1) == (0, 0)

    obj5 = Object(10, 1)
    assert chebyshev_vector(obj5, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj5) == (2, 0)

    obj6 = Object(10, 10)
    assert chebyshev_vector(obj6, obj1) == (0, -1)
    assert chebyshev_vector(obj1, obj6) == (0, 1)

    obj7 = Object(10, 6, generator=Generator.from_codes(("H*6",)))
    assert chebyshev_vector(obj7, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj7) == (2, 0)


def test_adjoin():
    obj1 = Object(5, 5, generator=Generator.from_codes(("V*2", "H*3")))
    obj2 = Object(2, 1, generator=Generator.from_codes(("V*1", "H*1")))
    assert Actions.Adjoin.act(obj2, obj1) == Actions.Vertical.act(obj2, 1)

    obj3 = Object(10, 10)
    assert Actions.Adjoin.act(obj3, obj1) == Actions.Horizontal.act(obj3, -1)


def test_align():
    obj1 = Object(5, 5, generator=Generator.from_codes(("V*2", "H*3")))
    obj2 = Object(2, 1, generator=Generator.from_codes(("V*1", "H*1")))
    assert Actions.Align.act(obj2, obj1) == Actions.Vertical.act(obj2, 3)

    obj3 = Object(2, 3)
    assert Actions.Align.act(obj3, obj1) == Actions.Horizontal.act(obj3, 2)
