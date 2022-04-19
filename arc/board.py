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
        self.proc_q: list[str] = [""]
        self.tree: dict[str, Object] = {"": self.raw}

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
        for obj in list(self.tree.values()):
            if obj.props < best_props:
                best_props = obj.props
                self.decomposed = obj.flatten()
                log.debug(f"Chose flattened object: {self.decomposed}")

    def decompose(
        self,
        batch: int = 10,
        max_iter: int = 100,
        inventory: Inventory | None = None,
        init: bool = False,
    ) -> None:
        """Determine the optimal representation of the Board.

        Args:
            batch: period, in iterations, before choosing a new representation.
            max_iter: Maximum number of iterations of decomposition.
        """

        inventory = inventory or Inventory()
        if not self.proc_q or init:
            self.proc_q = [""]
            self.tree = {"": self.raw}

        log.info(f"== Begin decomposition")
        for ct in range(1, max_iter + 1):
            key = self.proc_q.pop(0)
            obj = self.tree[key]
            candidates = self._decomposition(obj, inventory)
            for code, obj in candidates:
                new_key = key + code
                self.tree[new_key] = obj.flatten()
                self.proc_q.append(new_key)
            if ct % batch == 0:
                self.choose_representation()
                log.info(f"== {ct}: {self.rep}")
            if not self.proc_q:
                log.info(f"==! {ct}: Ending due to empty processing queue.")
                break
        self.choose_representation()

    def _decomposition(
        self, obj: Object, inventory: "Inventory"
    ) -> list[tuple[str, Object]]:
        """Attempts to find a more canonical or condensed way to represent the object"""
        # No children means nothing to simplify
        if len(obj.children) == 0:
            return []

        # Search for the first object that's not decomposed and apply decomposition
        # TODO Need to redo occlusion
        elif obj.leaf:
            # NOTE: We run in reverse order to handle occlusion
            decompositions: list[tuple[str, Object]] = []
            for rev_idx, child in enumerate(obj.children[::-1]):
                child_candidates = self._decomposition(child, inventory=inventory)
                if child_candidates:
                    # Each new decomposition needs to replace any parents
                    for code, new_child in child_candidates:
                        new_obj = obj.copy()
                        new_obj.children[-(1 + rev_idx)] = new_child
                        decompositions.append((code, new_obj))
                    break
            return decompositions
        elif match := inventory.find_closest(obj, threshold=4):
            log.debug(f"Match at distance: {match.dist}")
            # TODO: Figure out full set of operations/links we need for use
            # of objects prescribed from context.
            linked = match.left.copy(anchor=obj.anchor, leaf=True, process="Inv")
            return [("Inv", linked)]

        candidates = self.generate_candidates(obj)
        log.debug(f"Generated {len(candidates)} candidates")
        return candidates

    def generate_candidates(self, obj: Object) -> list[tuple[str, Object]]:
        candidates: list[tuple[str, Object]] = []
        for process in self.processes:
            if process.test(obj):
                candidate = process.run(obj)
                if candidate:
                    candidates.append((process.code, candidate))
            else:
                log.debug(f"{process.__class__.__name__} failed pre-run test")

        return candidates
