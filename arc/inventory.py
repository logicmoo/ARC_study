import collections
from functools import cached_property

from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.comparisons import ObjectComparison, default_comparisons
from arc.util import dictutil, logger

log = logger.fancy_logger("Inventory", level=30)


class Inventory:
    def __init__(
        self,
        obj: Object | None = None,
        comparisons: list[ObjectComparison] = default_comparisons,
    ):
        self.inventory = self.create_inventory(obj) if obj else {}
        self.comparisons = comparisons

    @cached_property
    def all(self) -> list[Object]:
        return [obj for ranked_objs in self.inventory.values() for obj in ranked_objs]
    
    @cached_property
    def depth(self) -> list[tuple[str, Object]]:
        return [
            (depth, obj)
            for depth, obj_list in self.inventory.items()
            for obj in obj_list
        ]

    def create_inventory(self, obj: Object, depth: int = 0) -> dict[str, list[Object]]:
        """Recursively find all objects, index them by their generator."""
        inventory: dict[str, list[Object]] = collections.defaultdict(list)
        obj_char = "" if obj.generator is None else obj.generator.char
        inventory[obj_char].append(obj)
        for kid in obj.children:
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            dictutil.merge(inventory, self.create_inventory(kid, depth=depth + 1))
        return inventory

    def find_closest(self, obj: Object, threshold: float = 8) -> ObjectDelta | None:
        # We prune the search for transformation matches by generator characteristic
        # as there (currently) is no presumption of dynamic generators--we assume
        # that if the output contains objects with generators, their characteristics
        # are constant across cases.
        obj_char = "" if obj.generator is None else obj.generator.char
        candidates = self.inventory.get(obj_char, [])

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
