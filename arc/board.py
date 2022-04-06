import collections
from functools import cached_property

import numpy as np

from arc.comparisons import ObjectComparison, default_comparisons
from arc.util import logger
from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.processes import Process, default_processes
from arc.types import BoardData

log = logger.fancy_logger("Board", level=30)


class Board:
    """One 2D set of colored squares--the base unit of the ARC dataset.

    We use the recursive Object class to build a hierarchical representation
    of the Board that minimizes total properties used.

    Attributes:
        rep: The current representation of the Board via Objects.
        name: An auto-generated, descriptive name for the board.
        proc_q: A priority queue for holding decomposition candidates.
        bank: Any decompositions with no further possible operations.
    """

    def __init__(
        self, data: BoardData, name: str = "", processes: list[Process] | None = None
    ):
        self.name = name
        self.raw = Object.from_grid(grid=np.array(data))  # type: ignore
        self.processes = processes or default_processes

        # Used during decomposition process
        self.decomposed: Object | None = None
        self.proc_q = collections.deque([self.raw])
        self.bank: list[Object] = []
        self.inventory: Inventory = Inventory(Object())

    def __repr__(self) -> str:
        return self.rep.hier_repr()

    @property
    def rep(self) -> Object:
        if self.decomposed:
            return self.decomposed
        else:
            return self.raw

    def choose_representation(self) -> None:
        """Find the most compact representation from decomposition."""
        best_props = self.rep.props
        for obj in self.bank + list(self.proc_q):
            if obj.props < best_props:
                best_props = obj.props
                self.decomposed = obj.flatten()
                log.debug(f"Chose flattened object: {self.decomposed}")

    def decompose(
        self, batch: int = 10, max_iter: int = 10, init: bool = False
    ) -> None:
        """Determine the optimal representation of the Board.

        Args:
            batch: Number of candidates to keep each round. E.g. if batch=1, only the best
              candidate is retained.
            max_iter: Maximum number of iterations of decomposition.
        """
        if not self.proc_q or init:
            self.proc_q = collections.deque([self.raw])
            self.bank = []
        for ct in range(max_iter):
            log.info(f"== Begin decomposition round {ct+1}")
            log.debug("  Processing queue:")
            for obj in self.proc_q:
                log.debug(f"  - {obj}")
            self.batch_decomposition(batch=batch)
            log.info(f"== Decomposition at {self.rep.props}p after {ct+1} rounds")
            if not self.proc_q:
                log.info("==! Ending decomposition due to empty processing queue")
                break
        self.choose_representation()
        self.rep.info("info")

    def batch_decomposition(self, batch: int = 10) -> None:
        """Decompose the top 'batch' candidates."""
        ct = 0
        while self.proc_q and ct < batch:
            ct += 1
            obj = self.proc_q.popleft()
            log.debug(f" = Batch item {ct}/{batch}")
            obj.info(level="debug")
            new_objs = self._decomposition(obj)
            if not new_objs:
                self.bank.append(obj.flatten())
            self.proc_q.extend(new_objs)
            log.debug(
                f" - Item {ct}, proc_q: {len(self.proc_q)}, bank: {len(self.bank)}"
            )
            self.choose_representation()

    def _decomposition(self, obj: Object) -> list[Object]:
        """Attempts to find a more canonical or condensed way to represent the object"""
        # No children means nothing to simplify
        if len(obj.children) == 0:
            return []

        # Search for the first object that's not decomposed and apply decomposition
        # TODO Need to redo occlusion
        elif obj.traits.get("finished"):
            # NOTE: We run in reverse order to handle occlusion
            decompositions: list[Object] = []
            for rev_idx, child in enumerate(obj.children[::-1]):
                child_candidates = self._decomposition(child)
                if child_candidates:
                    # Each new decomposition needs a new top-level object
                    for new_child in child_candidates:
                        new_obj = obj.spawn()
                        new_obj.children[-(1 + rev_idx)] = new_child
                        decompositions.append(new_obj)
                    break
            return decompositions
        elif match := self.inventory.find_closest(obj, threshold=4):
            log.debug(f"Match at distance: {match.dist}")
            log.debug(f"  {obj} to")
            log.debug(f"  {match.right}")
            # TODO: Figure out full set of operations/links we need for use
            # of objects prescribed from context.
            linked = match.right.spawn(anchor=obj.anchor)
            linked.traits["decomp"] = "Ctxt"
            linked.traits["finished"] = True
            return [linked]

        candidates = self.generate_candidates(obj)
        for candidate in candidates:
            log.debug(f"  {candidate}")
        return candidates

    def generate_candidates(self, obj: Object) -> list[Object]:
        candidates: list[Object] = []
        for process in self.processes:
            if process.test(obj):
                candidate = process.run(obj)
                if candidate:
                    candidates.append(candidate)
            else:
                log.debug(f"{process.__class__.__name__} failed pre-run test")

        return candidates

    def set_inventory(self, obj: Object) -> None:
        self.inventory = Inventory(obj)


class Inventory:
    def __init__(
        self, obj: Object, comparisons: list[ObjectComparison] = default_comparisons
    ):
        self.inventory = self.create_inventory(obj)
        self.comparisons = comparisons

    @cached_property
    def all(self) -> list[Object]:
        return [obj for sized_objs in self.inventory.values() for obj in sized_objs]

    def create_inventory(self, obj: Object) -> dict[int, list[Object]]:
        """Recursively find all non-Dot objects in the hierarchy."""
        inventory: dict[int, list[Object]] = collections.defaultdict(list)
        if obj.category == "Dot":
            return {}
        inventory[obj.size].append(obj)
        for kid in obj.children:
            child_inv = self.create_inventory(kid)
            for key, obj_list in child_inv.items():
                inventory[key].extend(obj_list)
        return inventory

    def find_closest(self, obj: Object, threshold: float = 4) -> ObjectDelta | None:
        # NOTE temporary, filtering by size assumes we can't add expand a Generator
        # to create the object.
        # candidates = self.inventory.get(obj.size, [])
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
