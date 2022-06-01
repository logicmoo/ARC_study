from dataclasses import dataclass
from typing import Any, TypeAlias
from arc.object import Object, sort_layer
from arc.object_delta import ObjectDelta

from arc.labeler import Labeler, all_traits
from arc.util import logger

log = logger.fancy_logger("Selector", level=30)

# Represents a list of objects per case that will be grouped
# as a transform.
Selection: TypeAlias = list[list[ObjectDelta]]


def subdivide_groups(selection: Selection) -> list[Selection]:
    if not all([len(group) >= 2 for group in selection]):
        log.info("Insufficient group sizes to subdivide selection")
        return []
    if len(set([len(group) for group in selection])) != 1:
        log.info("Different group sizes in selection, won't subdivide")
        return []

    # Begin with a single element per group, nucleated from the first group
    new_selections: list[Selection] = [[[delta]] for delta in selection[0]]
    for src_group in selection[1:]:
        # TODO Try greedily minimizing distance from obj to target group for now
        for delta in src_group:
            best_dist = 1000
            chosen = 0
            for idx, target in enumerate(new_selections):
                dist = sum(
                    [
                        ObjectDelta(delta.left, tgt_delta.left).dist
                        for group in target
                        for tgt_delta in group
                    ]
                )
                if dist < best_dist:
                    best_dist = dist
                    chosen = idx
            new_selections[chosen].append([delta])

    return new_selections


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
        # Whether this is a valid Selector
        self.null: bool = True
        self.criteria: list[Criterion] = []

        flat_selection = [obj for group in selection for obj in group]
        flat_complement = [
            obj for group in obj_groups for obj in group if obj not in flat_selection
        ]
        log.debug("Choosing criteria for the following inputs, selection:")
        log.debug(obj_groups)
        log.debug(flat_selection)

        if len(flat_complement) == 0:
            log.debug("Trivial selection, no criteria")
            self.null = False
            return

        coeff = 3

        labels = Labeler(obj_groups).labels
        best_score = 1000
        best: list[Criterion] = []
        splits: dict[str, tuple[set[Any], set[Any]]] = {}
        for trait in all_traits:
            in_set = {labels[obj.uid][trait] for obj in flat_selection}
            out_set = {labels[obj.uid][trait] for obj in flat_complement}
            # We prohibit using a trait if a None value is in the inclusions.
            # E.g. if a trait ranking contains a tie, the tie and later values
            # will take None.
            if None in in_set:
                continue
            splits[trait] = (in_set, out_set)
            if in_set and out_set and (not in_set & out_set):
                if (score := (len(in_set) - 1) * coeff) < best_score:
                    best_score = score
                    best = [Criterion(trait, in_set)]
                if (score := (len(out_set) - 1) * coeff) < best_score:
                    # NOTE: Try only allowing single-value negations
                    if len(out_set) > 1:
                        continue
                    best_score = score
                    best = [Criterion(trait, out_set, negated=True)]

        # Also search for two-trait combos
        for trait_1, (in_1, out_1) in splits.items():
            overlap = in_1 & out_1
            confused_in = [
                obj for obj in flat_selection if labels[obj.uid][trait_1] in overlap
            ]
            confused_out = [
                obj for obj in flat_complement if labels[obj.uid][trait_1] in overlap
            ]
            if len(in_1) <= len(out_1):
                base_len = len(in_1)
                base_criterion = Criterion(trait_1, in_1)
            else:
                base_len = len(out_1)
                base_criterion = Criterion(trait_1, out_1, negated=True)

            for trait_2 in splits:
                if trait_1 == trait_2:
                    continue
                in_set = {labels[obj.uid][trait_2] for obj in confused_in}
                out_set = {labels[obj.uid][trait_2] for obj in confused_out}
                if in_set and out_set and (not in_set & out_set):
                    if (score := (len(in_set) + base_len - 2) * coeff) < best_score:
                        best_score = score
                        best = [base_criterion, Criterion(trait_2, in_set)]
                    if (score := len(out_set) + base_len - 2) * coeff < best_score:
                        if len(out_set) > 1:
                            continue
                        best_score = score
                        best = [
                            base_criterion,
                            Criterion(trait_2, out_set, negated=True),
                        ]

        self.criteria: list[Criterion] = best
        if len(best) > 0:
            self.null = False
        log.info(f"Criteria: {self.criteria}")

    def __repr__(self) -> str:
        return str(self.criteria)

    def __bool__(self) -> bool:
        return not self.null

    def select(self, group: list[Object]) -> list[Object]:
        # TODO Handle the timing of Labeling traits, vs intrinsic traits
        # Here, we must access traits before we've selected into groups. But,
        # only when we have groups can we do ranked labeling.
        labels = Labeler([group]).labels
        selection: list[Object] = group
        for crit in self.criteria:
            new_selection: list[Object] = []
            for obj in selection:
                if (labels[obj.uid].get(crit.trait) in crit.values) != crit.negated:
                    new_selection.append(obj)
            selection = new_selection
        return sort_layer(selection)
