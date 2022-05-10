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
        flat_complement = [
            obj for group in obj_groups for obj in group if obj not in flat_selection
        ]
        log.debug("Choosing criteria for the following inputs, selection:")
        log.debug(obj_groups)
        log.debug(flat_selection)

        labeler = Labeler(obj_groups)

        base_criteria: dict[str, set[int | str]] = dictutil.dict_val2set(
            [labeler.labels[obj.uid] for obj in flat_selection]
        )
        log.debug(f"Initial Criteria: {base_criteria}")

        # Remove any traits present in the other Objects
        dictutil.dict_popset(
            base_criteria, [labeler.labels[obj.uid] for obj in flat_complement]
        )

        # Try single traits first, then pairs, etc.
        # for rank in (1,):
        # current: dict[str, Any] = set(itertools.combinations(base_criteria, rank))

        self.criteria = base_criteria
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
                    labeler.labels[obj.uid].get(key) in val
                    or getattr(obj, key, None) in val
                )
            ]
        return group
