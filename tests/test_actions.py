from arc.generator import Generator
from arc.object import Object
from arc.actions import Action, chebyshev_vector


def test_translations():
    """Test each action that translates an Object."""
    pt1 = Object(1, 1, 1)
    pt2 = Action.horizontal(pt1, 1)
    assert pt2 == Object(1, 2, 1)
    assert pt2 != pt1

    # 'Konami' test :) (up down left right is idempotent)
    pt3 = Action.horizontal(
        Action.horizontal(Action.vertical(Action.vertical(pt1, -1), 1), -1), 1
    )
    assert pt3 == pt1

    # Zeroing should be equivalent to justifying each axis
    assert Action.zero(pt1) == Action.justify(Action.justify(pt1, 0), 1)

    # Tiling ops translate based on the object size
    group = Object(children=[Object(0, 0, 1), pt1])
    assert Action.rtile(group).loc == (2, 0)
    assert Action.ctile(group).loc == (0, 2)
    assert Action.mtile(group, 1, 1) == Action.rtile(Action.ctile(group))


def test_deformations():
    """Test scaling, skewing, etc of Objects."""
    # If there's no generator, just return a copy of the original object
    pt1 = Object(1, 1, 1)
    assert Action.scale(pt1, "R", 2) == pt1

    sq_gen = Generator.from_codes(["R*4", "C*4"])
    square = Object(1, 1, 1, generator=sq_gen)

    flat = Action.r_scale(square, 2)
    assert flat.loc == (1, 1)
    assert flat.shape == (3, 5)

    thin = Action.c_scale(square, 2)
    assert thin.loc == (1, 1)
    assert thin.shape == (5, 3)

    assert Action.scale(Action.scale(square, "R", 1), "R", 4) == square


def test_rotation():
    """Test object rotation."""
    # Turning a point should yield itself
    pt1 = Object(1, 1, 1)
    assert Action.turn(pt1, 1) == pt1

    # A monocolor line is symmetric under 180 deg rotation
    blue_line = Object(children=[Object(0, 0, 1), Object(1, 0, 1), Object(2, 0, 1)])
    assert Action.turn(blue_line, 1).shape == (1, 3)
    assert Action.turn(blue_line, 2) == blue_line

    composite = Object(children=[blue_line, pt1])
    assert Action.turn(composite, 1).shape == (2, 3)
    assert Action.turn(composite, 2).shape == (3, 2)
    assert Action.turn(composite, 2) != composite
    assert Action.turn(composite, 4) == composite


def test_reflection():
    """Test reflecting the Object over an axis."""
    pt1 = Object(1, 1, 1)
    assert Action.flip_v(pt1) == pt1
    assert Action.flip_h(pt1) == pt1

    group = Object(children=[Object(0, 0, 2), pt1])

    h_true_points = {(0, 1): 2, (1, 0): 1}
    assert Action.flip_h(group).points == h_true_points

    v_true_points = {(0, 1): 1, (1, 0): 2}
    assert Action.flip_v(group).points == v_true_points


def test_color():
    pt1 = Object(1, 1, 1)
    assert Action.recolor(pt1, 2).color == 2
    assert Action.recolor(Action.recolor(pt1, 0), 1) == pt1


def test_resize():
    obj1 = Object(generator=Generator.from_codes(["R*5", "C*3"]))
    obj2 = Object(2, 1, generator=Generator.from_codes(["R*1", "C*1"]))
    obj3 = Object(generator=Generator.from_codes(["R*1", "C*1"]))
    assert Action().resize(obj1, obj2) == obj3

    obj4 = Object(1, 5, generator=Generator.from_codes(["R*5", "C*1"]))
    obj5 = Object(generator=Generator.from_codes(["R*5", "C*1"]))
    assert Action().resize(obj1, obj4) == obj5

    obj6 = Object(generator=Generator.from_codes(["R*3", "C*3"]))
    obj7 = Object(generator=Generator.from_codes(["R*3", "C*3"]))
    assert Action().resize(obj1, obj6) == obj7


def test_chebyshev():
    obj1 = Object(5, 5, generator=Generator.from_codes(["R*2", "C*3"]))
    obj2 = Object(2, 1, generator=Generator.from_codes(["R*1", "C*1"]))
    assert chebyshev_vector(obj2, obj1) == (1, 0)
    assert chebyshev_vector(obj1, obj2) == (-1, 0)

    obj3 = Object(2, 1, generator=Generator.from_codes(["R*5", "C*1"]))
    assert chebyshev_vector(obj3, obj1) == (0, 2)
    assert chebyshev_vector(obj1, obj3) == (0, -2)

    obj4 = Object(4, 4, generator=Generator.from_codes(["R*1", "C*2"]))
    assert chebyshev_vector(obj1, obj4) == (0, 0)
    assert chebyshev_vector(obj4, obj1) == (0, 0)

    obj5 = Object(10, 1)
    assert chebyshev_vector(obj5, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj5) == (2, 0)

    obj6 = Object(10, 10)
    assert chebyshev_vector(obj6, obj1) == (0, -1)
    assert chebyshev_vector(obj1, obj6) == (0, 1)

    obj7 = Object(10, 6, generator=Generator.from_codes(["C*6"]))
    assert chebyshev_vector(obj7, obj1) == (-2, 0)
    assert chebyshev_vector(obj1, obj7) == (2, 0)


def test_adjoin():
    obj1 = Object(5, 5, generator=Generator.from_codes(["R*2", "C*3"]))
    obj2 = Object(2, 1, generator=Generator.from_codes(["R*1", "C*1"]))
    assert Action().adjoin(obj2, obj1) == Action().vertical(obj2, 1)

    obj6 = Object(10, 10)
    assert Action().adjoin(obj6, obj1) == Action().horizontal(obj6, -1)
