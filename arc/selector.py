from typing import Any
from arc.object import Object

from arc.labeler import Labeler, all_traits
from arc.util import dictutil, logger

log = logger.fancy_logger("Selector", level=30)


class Selector:
    """Find the set of traits that distinguish the selection from the rest of the inventory."""

    def __init__(
        self,
        obj_groups: list[list[Object]],
        selection: list[list[Object]],
    ) -> None:
        # TODO: For now this is based on single trait values. However, for
        # the general case, trait combinations would need consideration.
        # E.g. Select blue rectangles

        flat_selection = [obj for group in selection for obj in group]
        log.debug("Choosing criteria for the following inputs, selection:")
        log.debug(obj_groups)
        log.debug(flat_selection)
        labeler = Labeler(obj_groups)
        self.criteria: dict[str, Any] = dictutil.dict_and_group(
            [labeler.labels[obj.uid] for obj in flat_selection]
        )
        log.debug(f"Initial Criteria: {self.criteria}")
        # Remove any traits present in the other Objects
        for group in obj_groups:
            for obj in group:
                if obj in flat_selection:
                    continue
                dictutil.dict_sub(self.criteria, labeler.labels[obj.uid])
        log.debug(f"Filter other objects: {self.criteria}")
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
        labeler = Labeler([group])
        for key, val in self.criteria.items():
            group = [
                obj
                for obj in group
                if (
                    labeler.labels[obj.uid].get(key) == val
                    or getattr(obj, key, None) == val
                )
            ]
        return group
