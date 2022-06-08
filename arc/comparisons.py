from typing import Any, Callable, TypeAlias

from arc.actions import Actions
from arc.object import Object
from arc.transform import Transform
from arc.util import logger

log = logger.fancy_logger("Comparisons", level=30)

ComparisonReturn: TypeAlias = Transform
ObjectComparison: TypeAlias = Callable[["Object", "Object"], ComparisonReturn]


def compare_position(left: "Object", right: "Object") -> ComparisonReturn:
    log.debug("Comparing Position")
    transform: ComparisonReturn = Transform([])
    r1, c1 = left.loc
    r2, c2 = right.loc
    if r2 == r1 and c2 == c1:
        return transform
    # Check for zeroing, which is special
    # NOTE We will also need to include some way to handle determining between
    # equivalent operations. For example, if an object is moved from (3, 0) to (0, 0)
    # this could be a 'zeroing', a 'row-justify' or an upward move of 3 units.
    if r2 == 0 and c2 == 0:
        transform.actions.append(Actions.Zero)
        transform.args.append(tuple([]))
        return transform
    if r2 != r1:
        # Justifying a single dimension is also special
        if r2 == 0:
            transform.actions.append(Actions.Justify)
            transform.args.append((0,))
        else:
            transform.actions.append(Actions.Vertical)
            transform.args.append((r2 - r1,))
    if c2 != c1:
        if c2 == 0:
            transform.actions.append(Actions.Justify)
            transform.args.append((1,))
        else:
            transform.actions.append(Actions.Horizontal)
            transform.args.append((c2 - c1,))
    return transform


def compare_color(left: "Object", right: "Object") -> ComparisonReturn:
    log.debug("Comparing Color")
    transform: ComparisonReturn = Transform([])
    c1 = set([item[0] for item in left.c_rank])
    c2 = set([item[0] for item in right.c_rank])
    if c1 != c2:
        # Color remapping is a basic transform
        if len(c1) == 1 and len(c2) == 1:
            transform.actions.append(Actions.Paint)
            transform.args.append((list(c2)[0],))
    return transform


# TODO compare_order still seems a bit off (not fundamental), can it be improved?
def compare_order(left: "Object", right: "Object") -> ComparisonReturn:
    """Checks for differences in the applications of generators."""
    log.debug("Comparing Order")
    transform: ComparisonReturn = Transform([])
    if len(left.c_rank) == 1 and len(right.c_rank) == 1:
        # A monochrome, matching silhouette means no internal positioning differences
        if left.sil(right):
            log.debug("  Sillhouettes match")
            return transform

    # There could exist one or more generators to create the other object
    for axis, code in [(0, "R"), (1, "C")]:
        if left.shape[axis] != right.shape[axis]:
            ct = right.shape[axis] - 1
            scaler = Actions.VScale if code == "R" else Actions.HScale
            transform.actions.append(scaler)
            transform.args.append((ct,))
    return transform


def compare_orientation(left: "Object", right: "Object") -> ComparisonReturn:
    """Checks whether the objects are related via a rotation, reflection."""
    log.debug("Comparing Orientation")
    transform: ComparisonReturn = Transform([])
    if left.c_rank != right.c_rank:
        # The number of points of each color must match
        return transform

    # TODO For now, just brute force search. This could be made more efficient.
    for code in ["|", "_"]:
        if (action := Actions.map[code]).act(left) == right:
            transform.actions.append(action)
            transform.args.append(tuple([]))
            return transform
    if (rotation := compare_rotation(left, right)).actions:
        return rotation
    for code in ["|", "_"]:
        for ct in [1, 2, 3]:
            if (action := Actions.map[code]).act(Actions.Rotate.act(left, ct)) == right:
                transform.actions.append(Actions.Rotate)
                transform.args.append(tuple([ct]))
                transform.actions.append(action)
                transform.args.append(tuple([]))
                return transform

    return transform


def compare_rotation(left: "Object", right: "Object") -> ComparisonReturn:
    log.debug("Comparing Rotation")
    for ct in [1, 2, 3]:
        if Actions.Rotate.act(left, ct) == right:
            return Transform([Actions.Rotate], [(ct,)])
    return Transform([])


# TODO handle type
default_comparisons: list[Any] = [
    compare_position,
    compare_color,
    compare_order,
    compare_orientation,
]

decomposition_comparisons: list[Any] = [
    compare_position,
    compare_color,
]
