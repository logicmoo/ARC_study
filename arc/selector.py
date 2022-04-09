from typing import Any
from arc.object import Object

from arc.labeler import all_traits
from arc.util import dictutil, logger

log = logger.fancy_logger("Selector", level=30)

# TODO Right now, perhaps the traits dict contains two types of entities,
# and these should be separated. However, it's unclear whether the process
# used to generate an object (the 'decomp' trait) might be useful for
# distinguishing objects
ignored_traits = ["decomp", "finished"]


class Selector:
    """Find the set of traits that distinguish the selection from the rest of the inventory."""

    def __init__(
        self,
        input: list[Object],
        selection: list[Object],
        ignore: list[str] = ignored_traits,
    ) -> None:
        # TODO: For now this is based on single trait values. However, for
        # the general case, trait combinations would need consideration.
        # E.g. Select blue rectangles
        self.criteria: dict[str, Any] = dictutil.dict_and_group(
            [obj.traits for obj in selection]
        )
        for trait in ignore:
            self.criteria.pop(trait, None)
        # Remove any traits present in the other Objects
        for obj in input:
            if obj in selection:
                continue
            dictutil.dict_sub(self.criteria, obj.traits)
        # Choose the highest priority trait of remaining traits
        for trait in all_traits:
            if trait in self.criteria:
                # NOTE: Requires fixing for multi-trait
                # We would flatten out the trait group...
                self.criteria = {trait: self.criteria[trait]}
                break
        log.info(f"Criteria: {self.criteria}")

    def __repr__(self) -> str:
        return str(self.criteria)

    def select(self, group: list[Object]) -> list[Object]:
        # TODO Handle the timing of Labeling traits, vs intrinsic traits
        # Here, we must access traits before we've selected into groups. But,
        # only when we have groups can we do ranked labeling.
        for key, val in self.criteria.items():
            group = [
                obj
                for obj in group
                if (obj.traits.get(key) == val or getattr(obj, key, None) == val)
            ]
        return group
