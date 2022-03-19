from typing import Callable, TypeAlias
from arc.actions import Action
from arc.generator import Transform
from arc.util import logger
from arc.object import Object

log = logger.fancy_logger("Comparisons", level=30)

ComparisonReturn: TypeAlias = list[tuple[Transform | None, int]]
ObjectComparison: TypeAlias = Callable[[Object, Object], ComparisonReturn]


def get_order_diff(left: Object, right: Object) -> ComparisonReturn:
    """Checks for differences in the arrangement of points"""
    log.debug("Comparing Order")
    transforms: ComparisonReturn = []
    if len(left.c_rank) == 1 and len(right.c_rank) == 1:
        # A monochrome, matching silhouette means no internal positioning differences
        if left.sil(right):
            log.debug("  Sillhouettes match")
            return transforms

    # Without a matching silhouette, only a fully ordered transformation works here
    # NOTE Including flooding and similar ops will change this
    if left.order[2] != 1 or right.order[2] != 1:
        transforms.append((None, 0))
    else:
        # There could exist one or more generators to create the other object
        for axis, code in [(0, "R"), (1, "C")]:
            if left.shape[axis] != right.shape[axis]:
                ct = right.shape[axis]
                scaler = Action.r_scale if code == "R" else Action.c_scale
                transforms.append((Transform([scaler], [(ct,)]), 0))
    return transforms


def get_color_diff(left: Object, right: Object) -> ComparisonReturn:
    log.debug("Comparing Color")
    transforms: ComparisonReturn = []
    c1 = set([item[0] for item in left.c_rank])
    c2 = set([item[0] for item in right.c_rank])
    if c1 != c2:
        # Color remapping is a basic transform
        if len(c1) == 1 and len(c2) == 1:
            transforms.append((Transform([Action.recolor], [(list(c2)[0],)]), 0))
        # However, partial or multiple remapping is not
        else:
            transforms.append((None, 0))
    return transforms


def get_translation(left: Object, right: Object) -> list[tuple[Transform | None, int]]:
    log.debug("Comparing Position")
    transforms: list[tuple[Transform | None, int]] = []
    r1, c1 = left.loc
    r2, c2 = right.loc
    if r2 == r1 and c2 == c1:
        return transforms
    # Check for zeroing, which is special
    # NOTE We will also need to include some way to handle determining between
    # equivalent operations. For example, if an object is moved from (3, 0) to (0, 0)
    # this could be a 'zeroing', a 'row-justify' or an upward move of 3 units.
    if r2 == 0 and c2 == 0:
        transforms.append((Transform([Action.zero]), 0))
        return transforms
    if r2 != r1:
        # Justifying a single dimension is also special
        if r2 == 0:
            transforms.append((Transform([Action.justify], [(0,)]), 0))
        else:
            transforms.append((Transform([Action.vertical], [(r2 - r1,)]), 0))
    if c2 != c1:
        if c2 == 0:
            transforms.append((Transform([Action.justify], [(1,)]), 0))
        else:
            transforms.append((Transform([Action.horizontal], [(c2 - c1,)]), 0))
    return transforms
