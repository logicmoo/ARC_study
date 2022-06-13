import collections
from functools import cached_property

from arc.actions import Action
from arc.comparisons import ObjectComparison, default_comparisons
from arc.definitions import Constants as cst
from arc.link import ObjectDelta
from arc.object import Object
from arc.transform import Transform
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
        """Recursively find all objects, index them by generating characteristic."""
        inventory: dict[str, list[Object]] = collections.defaultdict(list)
        inventory[obj.char].append(obj)
        self.depth[depth].append(obj)
        obj.depth = depth

        # If an object is a single-color blob, we shouldn't need to pick out children
        if obj.meta == "Blob" and len(obj.c_rank) == 1 and not obj.generating:
            return inventory

        for kid in obj.children:
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            dictutil.merge(inventory, self.create_inventory(kid, depth=depth + 1))
        return inventory

    @classmethod
    def invert(cls, left: Object, right: Object) -> ObjectDelta:
        transform = Transform([])
        log.debug("Comparing:")
        log.debug(f"  {left}")
        log.debug(f"  {right}")
        if left == right:
            return ObjectDelta(left, right, transform)

        for core_action in Action.__subclasses__():
            log.debug(f"  Checking core action: {core_action}")
            if (args := core_action.inv(left, right)) == tuple([]):
                continue
            else:
                transform = transform.concat(Transform([core_action], [args]))
                log.debug(f"    ->{args}")

        if not transform:
            return ObjectDelta(left, right, transform, null=True)

        log.debug(f"Inversion yielded Transform: {transform}")
        if null := (transform.apply(left) != right):
            log.debug("  Failed validity check")
        return ObjectDelta(left, right, transform, null=null)

    @classmethod
    def find_match(
        cls, candidates: list[Object], target: Object, dist_threshold: int
    ) -> ObjectDelta | None:
        if not candidates:
            log.debug(f"No candidates")
            return None

        best: int = dist_threshold + 1
        match: ObjectDelta | None = None
        log.debug(f"Matching {target} against {len(candidates)} candidates")
        for candidate in candidates:
            if delta := cls.invert(candidate, target):
                # if delta := ObjectDelta.from_comparisons(candidate, target):
                log.debug(f"Candidate has delta: {delta}")
                if delta.dist < best:
                    best = delta.dist
                    match = delta
        if not match:
            log.debug(f"No matches meeting threshold: {dist_threshold}")

        return match

    def find_decomposition_match(self, target: Object) -> ObjectDelta | None:
        candidates = self.all
        threshold = 8

        return self.find_match(candidates, target, dist_threshold=threshold)

    def find_scene_match(self, target: Object) -> ObjectDelta | None:
        # We prune the search for transformation matches by generating characteristic
        # as there (currently) is no presumption of dynamic generators--we assume
        # that if the output contains objects with generators, their characteristics
        # are constant across cases.
        candidates = self.inventory.get(target.char, [])
        return self.find_match(
            candidates, target, dist_threshold=cst.LINK_DIST_THRESHOLD
        )
