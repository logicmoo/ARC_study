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
        return [obj for sized_objs in self.inventory.values() for obj in sized_objs]

    @cached_property
    def depth(self) -> list[tuple[int, Object]]:
        return [
            (depth, obj)
            for depth, obj_list in self.inventory.items()
            for obj in obj_list
        ]

    def less(self, mask: list[Object]) -> list[Object]:
        """Return the inventory without the objects in the mask."""
        return [obj for obj in self.all if obj not in mask]

    def create_inventory(self, obj: Object, depth: int = 0) -> dict[int, list[Object]]:
        """Recursively find all non-Dot objects in the hierarchy."""
        inventory: dict[int, list[Object]] = collections.defaultdict(list)
        # TODO Make sure to handle when to inventory Dots
        if obj.category == "Dot":
            return {}
        inventory[depth].append(obj)
        for kid in obj.children:
            dictutil.merge(inventory, self.create_inventory(kid, depth=depth + 1))
        return inventory

    def find_closest(self, obj: Object, threshold: float = 4) -> ObjectDelta | None:
        # TODO Use object generation to prune search?
        candidates = self.all

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
