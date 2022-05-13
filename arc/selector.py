from dataclasses import dataclass
from typing import Any
from arc.object import Object

from arc.labeler import Labeler, all_traits
from arc.util import logger

log = logger.fancy_logger("Selector", level=30)


@dataclass
class Criterion:
    trait: str
    values: set[str | int]
    negated: bool = False


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
        best_score = 1000
        best: list[Criterion] = []
        splits: dict[str, tuple[set[Any], set[Any]]] = {}
        for trait in all_traits:
            in_set = {labeler.labels[obj.uid][trait] for obj in flat_selection}
            out_set = {labeler.labels[obj.uid][trait] for obj in flat_complement}
            splits[trait] = (in_set, out_set)
            if not in_set & out_set:
                if (score := len(in_set)) < best_score:
                    best_score = score
                    best = [Criterion(trait, in_set)]

        self.criteria: list[Criterion] = best
        log.info(f"Criteria: {self.criteria}")

    def __repr__(self) -> str:
        return str(self.criteria)

    def select(self, group: list[Object]) -> list[Object]:
        # TODO Handle the timing of Labeling traits, vs intrinsic traits
        # Here, we must access traits before we've selected into groups. But,
        # only when we have groups can we do ranked labeling.
        labels = Labeler([group]).labels
        selection: list[Object] = []
        for obj in group:
            match = True
            for crit in self.criteria:
                if (labels[obj.uid].get(crit.trait) in crit.values) == crit.negated:
                    match = False
                    break
            if match:
                selection.append(obj)
        return selection
