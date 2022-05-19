import collections
from typing import TYPE_CHECKING

from arc.definitions import Constants as cst
from arc.types import ObjectPath, Hook, StructureDef

if TYPE_CHECKING:
    from arc.object import Object


def compare_structure(
    objs: list["Object"], path: ObjectPath
) -> tuple[StructureDef, list[Hook]]:
    """Return the specification for the common elements among Objects."""
    struc: StructureDef = {}
    hooks: list[Hook] = []
    for prop, default in [
        ("row", cst.DEFAULT_ROW),
        ("col", cst.DEFAULT_COL),
        ("color", cst.DEFAULT_COLOR),
    ]:
        cts = collections.Counter([getattr(obj, prop) for obj in objs])
        if len(cts) == 1:
            if (val := next(iter(cts))) != default:
                struc[prop] = val
        else:
            hooks.append((path, prop))

    cts = collections.Counter(
        [getattr(obj.generator, "codes", tuple()) for obj in objs]
    )
    # TODO We need to check for more than just the exact generator
    if len(cts) == 1 and (val := next(iter(cts))) != tuple():
        struc["generator"] = next(iter(cts))

    child_args: list[StructureDef] = []
    child_hooks: list[Hook] = []
    dot_ct = 0
    child_match: bool = True
    for idx, kid_group in enumerate(zip(*[obj.children for obj in objs])):
        # TODO This could require multiple schemas of child-checking
        # as there could be a common child that's not at a constant layer
        # or constant depth.
        structure, kid_hooks = compare_structure(list(kid_group), path=path + (idx,))
        child_args.append(structure)
        child_hooks.extend(kid_hooks)
        if not all([kid == kid_group[0] for kid in kid_group[1:]]):  # type: ignore
            child_match = False
        if any([kid.category == "Dot" for kid in kid_group]):
            dot_ct += 1
    # Only include dot children if there's a limited number, or they all match
    if child_args:
        if dot_ct <= 5 or child_match:
            struc["children"] = child_args
            hooks.extend(child_hooks)
        else:
            hooks.append((path, "children"))
    return struc, hooks


def chebyshev_vector(left: "Object", right: "Object") -> tuple[int, int]:
    left_min_row, left_min_col = left.loc
    left_max_row = left.row + left.shape[0]
    left_max_col = left.col + left.shape[1]

    right_min_row, right_min_col = right.loc
    right_max_row = right.row + right.shape[0]
    right_max_col = right.col + right.shape[1]

    dist: list[int | None] = [None, None]
    # Check for any horizontal overlap
    if left_min_row >= right_max_row:
        dist[0] = right_max_row - left_min_row
    elif left_max_row <= right_min_row:
        dist[0] = right_min_row - left_max_row
    # Check for any vertical overlap
    if left_min_col >= right_max_col:
        dist[1] = right_max_col - left_min_col
    elif left_max_col <= right_min_col:
        dist[1] = right_min_col - left_max_col

    if dist[0] is None:
        if dist[1] is None:
            return (0, 0)
        else:
            return (0, dist[1])
    elif dist[1] is None:
        return (dist[0], 0)
    else:
        if abs(dist[0]) < abs(dist[1]):
            return (dist[0], 0)
        else:
            return (0, dist[1])
