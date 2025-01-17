from dataclasses import dataclass
from functools import cached_property
from typing import Any

from arc.labeler import Labeler, all_traits
from arc.node import Node
from arc.object import Object, sort_layer
from arc.object_types import ObjectCache, ObjectGroup, VarCache
from arc.util import logger

log = logger.fancy_logger("Selector", level=30)


@dataclass
class Criterion:
    trait: str
    values: set[str | int]
    negated: bool = False

    @cached_property
    def props(self) -> int:
        return len(self.values) * 2 + int(self.negated)

    def __lt__(self, other: "Criterion") -> bool:
        return self.props < other.props


class SelectionNode(Node):
    """Choose Objects from a set of inputs, based on criteria."""

    def __init__(
        self,
        criteria: list[Criterion],
        parents: set["Node"] | None = None,
        children: set["Node"] | None = None,
        null: bool = False,
    ) -> None:
        super().__init__(parents or set(), children or set())
        self.criteria: list[Criterion] = criteria
        self.null = null

    @property
    def name(self) -> str:
        return f"Selection"

    @property
    def specs(self) -> list[str]:
        msg: list[str] = []
        for crit in self.criteria:
            neg = "not " if crit.negated else ""
            msg.append(f"'{crit.trait}' {neg}in {crit.values}")
        return msg

    def __bool__(self) -> bool:
        return not self.null

    @property
    def props(self) -> int:
        return sum([crit.props for crit in self.criteria])

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

    def apply(self, object_cache: ObjectCache, var_cache: VarCache) -> list[Object]:
        input_objects, _ = self.fetch_inputs(object_cache)
        selection = self.select(input_objects)
        object_cache[self.uid] = selection
        return selection

    @classmethod
    def from_data(cls, inputs: ObjectGroup, selection: ObjectGroup) -> "SelectionNode":
        null = True
        flat_selection = [obj for group in selection for obj in group]
        flat_complement = [
            obj for group in inputs for obj in group if obj not in flat_selection
        ]
        log.debug("Choosing criteria for the following inputs, selection:")
        log.debug(inputs)
        log.debug(flat_selection)

        if len(flat_complement) == 0:
            log.debug("Trivial selection, no criteria")
            return cls([])

        labels = Labeler(inputs).labels
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
                pos_criterion = Criterion(trait, in_set)
                neg_criterion = Criterion(trait, out_set, negated=True)
                if pos_criterion.props < best_score:
                    best_score = pos_criterion.props
                    best = [pos_criterion]
                if neg_criterion.props < best_score:
                    # NOTE: Try only allowing single-value negations
                    if len(out_set) > 1:
                        continue
                    best_score = neg_criterion.props
                    best = [neg_criterion]

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
                base_criterion = Criterion(trait_1, in_1)
            else:
                base_criterion = Criterion(trait_1, out_1, negated=True)

            for trait_2 in splits:
                if trait_1 == trait_2:
                    continue
                in_set = {labels[obj.uid][trait_2] for obj in confused_in}
                out_set = {labels[obj.uid][trait_2] for obj in confused_out}
                pos_criterion = Criterion(trait_2, in_set)
                neg_criterion = Criterion(trait_2, out_set, negated=True)
                if in_set and out_set and (not in_set & out_set):
                    if (
                        score := (base_criterion.props + pos_criterion.props)
                    ) < best_score:
                        best_score = score
                        best = [base_criterion, pos_criterion]
                    if (
                        score := (base_criterion.props + neg_criterion.props)
                    ) < best_score:
                        if len(out_set) > 1:
                            continue
                        best_score = score
                        best = [base_criterion, neg_criterion]

        criteria: list[Criterion] = best
        if len(best) > 0:
            null = False
        log.info(f"Criteria: {criteria}")
        return cls(criteria, null=null)
