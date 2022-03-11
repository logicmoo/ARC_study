from arc.generator import Generator
from arc.object import Object
from arc.actions import Action


def test_translations():
    """Test each action that translates an Object."""
    pt1 = Object(1, 1, 1)
    pt2 = Action.right(pt1)
    assert pt2 == Object(1, 2, 1)
    assert pt2 != pt1

    # 'Konami' test :) (up down left right is idempotent)
    pt3 = Action.right(Action.left(Action.down(Action.up(pt1))))
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
