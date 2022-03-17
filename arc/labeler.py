from typing import Callable

from arc.object import Object
from arc.util import logger

log = logger.fancy_logger("Description", level=30)

intrinsic_properties = ["anchor", "category", "color"]


class Labeler:
    def __init__(self, obj_list: list[Object]) -> None:
        self.label_intrinsic_properties(obj_list, intrinsic_properties)

        self.obj_rank(obj_list, param="size")
        self.obj_rank(obj_list, param="width")

    def label_intrinsic_properties(
        self, obj_list: list[Object], intrinsic_properties: list[str]
    ) -> None:
        for obj in obj_list:
            for property in intrinsic_properties:
                obj.traits[property] = getattr(obj, property)

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
            obj.traits[name] = idx
