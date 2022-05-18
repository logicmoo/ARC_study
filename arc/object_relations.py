import collections
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from arc.object import Object


def compare_structure(objs: list["Object"]) -> dict[str, Any]:
    args: dict[str, Any] = {}
    for prop, default in [("row", 0), ("col", 0), ("color", 10)]:
        cts = collections.Counter([getattr(obj, prop) for obj in objs])
        if len(cts) == 1 and (val := next(iter(cts))) != default:
            args[prop] = val
    cts = collections.Counter([getattr(obj.generator, "codes", "") for obj in objs])
    if len(cts) == 1 and (val := next(iter(cts))) != "":
        args["generator"] = next(iter(cts))

    child_args: list[dict[str, Any]] = []
    dot_ct = 0
    child_match: bool = True
    for kids in zip(*[obj.children for obj in objs]):
        # TODO This could require multiple schemas of child-checking
        # as there could be a common child that's not at a constant layer
        child_args.append(compare_structure(list(kids)))
        if not all([kid == kids[0] for kid in kids[1:]]):  # type: ignore
            child_match = False
        if any([kid.category == "Dot" for kid in kids]):
            dot_ct += 1
    if child_args and (dot_ct <= 3 or child_match):
        args["children"] = child_args
    return args


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
