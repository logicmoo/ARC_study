from typing import Any
from arc.object import Object

from arc.util import dictutil, logger

log = logger.fancy_logger("Selector", level=30)

# TODO Right now, perhaps the traits dict contains two types of entities,
# and these should be separated. However, it's unclear whether the process
# used to generate an object (the 'decomp' trait) might be useful for
# distinguishing objects
ignored_traits = ["decomp", "finished"]


class Selector:
    """Select certain objects from the inputs and assign them to groups."""

    def __init__(self, input_groups: dict[str, list[Object]]) -> None:
        self.selectors: dict[str, dict[str, Any]] = self.create_selectors(input_groups)

    def __repr__(self) -> str:
        return str(self.selectors)

    def create_selectors(
        self, input_groups: dict[str, list[Object]], ignore: list[str] = ignored_traits
    ) -> dict[str, dict[str, Any]]:
        trait_groups: dict[str, dict[str, Any]] = {}
        for char, group in input_groups.items():
            distinct_traits = dictutil.dict_and_group([obj.traits for obj in group])
            # TODO see Line 8
            for trait in ignore:
                distinct_traits.pop(trait, None)
            for other_char, other_group in input_groups.items():
                if other_char == char:
                    continue
                for obj in other_group:
                    dictutil.dict_sub(distinct_traits, obj.traits)
            log.info(f"Distinct -- {char}: {distinct_traits}")
            trait_groups[char] = distinct_traits  # type: ignore
        return trait_groups

    def select(self, char: str, group: list[Object]) -> list[Object]:
        if char not in self.selectors:
            return []
        for key, val in self.selectors[char].items():
            group = [obj for obj in group if obj.traits.get(key) == val]
        return group

    def bundle(self, group: list[Object]) -> dict[str, list[Object]]:
        return {char: self.select(char, group) for char in self.selectors}
