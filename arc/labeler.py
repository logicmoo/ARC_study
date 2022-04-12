from typing import Any, Callable

from arc.object import Object
from arc.util import logger

log = logger.fancy_logger("Description", level=30)

# NOTE: These lists are priority ranked. When finding a Selector,
# and choosing amongst possible uniquely identifying trait sets,
# intrinsic properties are valued first, over ranked, and "color"
# would be used over "category".
intrinsic_properties = ["color", "category", "anchor"]
# TODO Include properties based on children
child_relations = ["child_count"]
ranked_parameters = ["size", "width", "row", "col"]

all_traits = intrinsic_properties + [item + "-rank" for item in ranked_parameters]


class Labeler:
    def __init__(self, obj_groups: list[list[Object]]) -> None:
        self.labels: dict[str, dict[str, Any]] = {
            obj.uid: {} for group in obj_groups for obj in group
        }
        for group in obj_groups:
            self.label_intrinsic_properties(group, intrinsic_properties)
            for param in ranked_parameters:
                self.obj_rank(group, param=param)

    def label_intrinsic_properties(
        self, obj_list: list[Object], intrinsic_properties: list[str]
    ) -> None:
        for obj in obj_list:
            for property in intrinsic_properties:
                self.labels[obj.uid][property] = getattr(obj, property)

    def obj_rank(
        self,
        obj_list: list[Object],
        param: str = "",
        key_function: Callable[[Object], int] | None = None,
        name: str = "",
        reverse: bool = True,
    ):
        name = name or f"{param}-rank"
        if key_function and param:
            log.warning(
                f"Both a key function and param ({param}) are defined for trait "
                f"'{name}'. Using the key_function by default."
            )
        key_function = key_function or (lambda x: getattr(x, param))
        for idx, obj in enumerate(sorted(obj_list, key=key_function, reverse=reverse)):
            self.labels[obj.uid][name] = idx
