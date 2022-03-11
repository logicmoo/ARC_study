from arc.actions import Action
from arc.definitions import Constants as cst
from arc.generator import Transform
from arc.util import logger
from arc.object import Object

log = logger.fancy_logger("Comparisons", level=30)


def get_order_diff(left: Object, right: Object) -> list[Transform | None]:
    """Checks for differences in the arrangement of points"""
    log.debug("Comparing Order")
    transforms: list[Transform | None] = []
    if len(left.c_rank) == 1 and len(right.c_rank) == 1:
        # A monochrome, matching silhouette means no internal positioning differences
        if left.sil(right):
            log.debug("  Sillhouettes match")

    # Without a matching silhouette, only an ordered transformation works here
    # NOTE Including flooding and similar ops will change this
    if left.order[2] != 1 or right.order[2] != 1:
        transforms.append(None)
    else:
        # There could exist one or more generators to create the other object
        for axis, code in [(0, "R"), (1, "C")]:
            if left.shape[axis] != right.shape[axis]:
                ct = left.shape[axis]
                scaler = Action.r_scale if code == "R" else Action.c_scale
                transforms.append(Transform([scaler], [(ct,)]))
    return transforms


def get_color_diff(left: Object, right: Object) -> list[Transform | None]:
    log.debug("Comparing Color")
    transforms: list[Transform | None] = []
    c1 = set([item[0] for item in left.c_rank])
    c2 = set([item[0] for item in right.c_rank])
    if c1 != c2:
        # Color remapping is a basic transform
        if len(c1) == 1 and len(c2) == 1:
            transforms.append(Transform([Action.recolor], [(list(c1)[0],)]))
        # However, partial or multiple remapping is not
        else:
            transforms.append(None)
    return transforms


def get_translation(left: Object, right: Object) -> list[Transform | None]:
    log.debug("Comparing Position")
    transforms: list[Transform | None] = []
    r1, c1 = left.loc
    r2, c2 = right.loc
    # Check for zeroing, which is special
    if r2 == 0 and c2 == 0:
        transforms.append(Transform([Action.zero]))
        return transforms
    if r2 != r1:
        # Justifying a single dimension is also special
        if r2 == 0:
            transforms.append(Transform([Action.justify], [(0,)]))
        else:
            transforms.append(Transform([Action.horizontal], [(r2 - r1,)]))
    if c2 != c1:
        if c2 == 0:
            transforms.append(Transform([Action.justify], [(1,)]))
        else:
            transforms.append(Transform([Action.vertical], [(c2 - c1,)]))
    return transforms
