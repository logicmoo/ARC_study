import collections
from functools import cached_property

from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.comparisons import (
    ObjectComparison,
    default_comparisons,
    decomposition_comparisons,
)
from arc.util import dictutil, logger

log = logger.fancy_logger("Inventory", level=30)


class Inventory:
    def __init__(
        self,
        obj: Object | None = None,
        comparisons: list[ObjectComparison] = default_comparisons,
    ):
        # TODO WIP Refactor
        self.depth: dict[int, list[Object]] = collections.defaultdict(list)
        self.inventory = self.create_inventory(obj) if obj else {}
        self.comparisons = comparisons

    @cached_property
    def all(self) -> list[Object]:
        return [obj for ranked_objs in self.inventory.values() for obj in ranked_objs]

    def create_inventory(self, obj: Object, depth: int = 0) -> dict[str, list[Object]]:
        """Recursively find all objects, index them by their generator."""
        inventory: dict[str, list[Object]] = collections.defaultdict(list)
        inventory[obj.generator.char].append(obj)
        self.depth[depth].append(obj)
        obj.depth = depth

        # If an object is a single-color blob, we shouldn't need to pick out children
        if obj.meta == "Blob" and len(obj.c_rank) == 1 and not obj.generator:
            return inventory

        for kid in obj.children:
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            dictutil.merge(inventory, self.create_inventory(kid, depth=depth + 1))
        return inventory

    def find_decomposition_match(self, obj: Object) -> ObjectDelta | None:
        candidates = self.all
        threshold = 2

        if not candidates:
            return None
        best = threshold + 0.5
        match = None
        for candidate in candidates:
            delta = ObjectDelta(candidate, obj, comparisons=decomposition_comparisons)
            if delta.dist < best:
                match = delta
                best = delta.dist
        if not match:
            log.debug(f"No matches meeting threshold: {threshold}")
            return None
        return match

    def find_scene_match(self, obj: Object) -> ObjectDelta | None:
        # We prune the search for transformation matches by generator characteristic
        # as there (currently) is no presumption of dynamic generators--we assume
        # that if the output contains objects with generators, their characteristics
        # are constant across cases.
        candidates = self.inventory.get(obj.generator.char, [])
        threshold = 8

        if not candidates:
            return None
        best = threshold + 0.5
        match = None
        for candidate in candidates:
            delta = ObjectDelta(candidate, obj, comparisons=self.comparisons)
            if delta.dist < best:
                match = delta
                best = delta.dist
        if not match:
            log.debug(f"No matches meeting threshold: {threshold}")
            return None
        return match
