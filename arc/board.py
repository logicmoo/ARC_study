import collections

from arc.inventory import Inventory
from arc.object import Object
from arc.processes import Process, default_processes
from arc.types import BoardData
from arc.util import logger

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
        self.raw = Object.from_grid(grid=data)
        self.processes = processes or default_processes

        # Used during decomposition process
        self.decomposed: Object | None = None
        self.proc_q = collections.deque([self.raw])
        self.bank: list[Object] = []

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
        self,
        batch: int = 10,
        max_iter: int = 10,
        inventory: Inventory | None = None,
        init: bool = False,
    ) -> None:
        """Determine the optimal representation of the Board.

        Args:
            batch: Number of candidates to keep each round. E.g. if batch=1, only the best
              candidate is retained.
            max_iter: Maximum number of iterations of decomposition.
        """
        inventory = inventory or Inventory()
        if not self.proc_q or init:
            self.proc_q = collections.deque([self.raw])
            self.bank = []
        for ct in range(max_iter):
            log.info(f"== Begin decomposition round {ct+1}")
            self.batch_decomposition(inventory, batch=batch)
            log.info(f"== Decomposition at {self.rep.props}p after {ct+1} rounds")
            if not self.proc_q:
                log.info("==! Ending decomposition due to empty processing queue")
                break
        self.choose_representation()

    def batch_decomposition(self, inventory: Inventory, batch: int = 10) -> None:
        """Decompose the top 'batch' candidates."""
        ct = 0
        while self.proc_q and ct < batch:
            ct += 1
            obj = self.proc_q.popleft()
            log.debug(f" = Batch item {ct}/{batch}")
            obj.info(level="debug")
            new_objs = self._decomposition(obj, inventory)
            if not new_objs:
                self.bank.append(obj.flatten())
            self.proc_q.extend(new_objs)
            log.debug(
                f" - Item {ct}, proc_q: {len(self.proc_q)}, bank: {len(self.bank)}"
            )
            self.choose_representation()

    def _decomposition(self, obj: Object, inventory: "Inventory") -> list[Object]:
        """Attempts to find a more canonical or condensed way to represent the object"""
        # No children means nothing to simplify
        if len(obj.children) == 0:
            return []

        # Search for the first object that's not decomposed and apply decomposition
        # TODO Need to redo occlusion
        elif obj.leaf:
            # NOTE: We run in reverse order to handle occlusion
            decompositions: list[Object] = []
            for rev_idx, child in enumerate(obj.children[::-1]):
                child_candidates = self._decomposition(child, inventory=inventory)
                if child_candidates:
                    # Each new decomposition needs to replace any parents
                    for new_child in child_candidates:
                        new_obj = obj.copy()
                        new_obj.children[-(1 + rev_idx)] = new_child
                        decompositions.append(new_obj)
                    break
            return decompositions
        elif match := inventory.find_closest(obj, threshold=4):
            log.debug(f"Match at distance: {match.dist}")
            # TODO: Figure out full set of operations/links we need for use
            # of objects prescribed from context.
            linked = match.left.copy(anchor=obj.anchor, leaf=True, process="Ctxt")
            return [linked]

        candidates = self.generate_candidates(obj)
        log.debug(f"Generated {len(candidates)} candidates")
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
