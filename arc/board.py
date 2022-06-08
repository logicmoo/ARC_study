from functools import cached_property

from arc.definitions import Constants as cst
from arc.grid_methods import shift_locs
from arc.inventory import Inventory
from arc.object import Object
from arc.processes import Process, Processes
from arc.types import BoardData, PositionSet
from arc.util import logger, common

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

    def __init__(self, data: BoardData, name: str = ""):
        self.name = name
        self.raw = Object.from_grid(grid=data)

        self._decomp_init()

    def _decomp_init(self) -> None:
        """Initialize all decomposition-related attributes."""
        self.tree: dict[str, Object] = {"": self.raw}
        self.current: str = ""
        self.processes: list[type[Process]] = list(Processes.map.values())
        self.proc_q: list[str] = [""]

    def __repr__(self) -> str:
        return self.rep.hier_repr()

    @property
    def rep(self) -> Object:
        return self.tree[self.current]

    def clean(self) -> None:
        current = self.tree[self.current]
        del self.tree
        self.tree: dict[str, Object] = {"": self.raw, self.current: current}

        del self.proc_q
        self.proc_q: list[str] = [""]

    @cached_property
    def characteristic_map(self) -> dict[str, str]:
        """Find the best representation for each characteristic."""
        result: dict[str, str] = {}
        for key, rep in self.tree.items():
            char = common.get_characteristic(key)
            if char not in result:
                result[char] = key
            elif rep.props < self.tree[result[char]].props:
                result[char] = key
        return result

    def decompose(
        self,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        inventory: Inventory | None = None,
        characteristic: str = "",
        init: bool = False,
    ) -> None:
        """Determine the optimal representation of the Board.

        Args:
            max_iter: Maximum number of iterations of decomposition.
        """
        inventory = inventory or Inventory()
        if not self.proc_q or init:
            self._decomp_init()

        if characteristic:
            self.processes = [Processes.map[char] for char in characteristic]

        log.info(f"  Begin decomposition")
        for ct in range(1, max_iter + 1):
            key = self.proc_q.pop(0)
            obj = self.tree[key]
            candidates = self._decomposition(obj, inventory, set([]))
            for code, obj in candidates:
                if obj.props > cst.PRUNE_PROPS_COEFF * self.rep.props:
                    continue
                new_key = key + code
                flat_obj = obj.flatten()
                if flat_obj.props <= obj.props:
                    obj = flat_obj
                self.tree[new_key] = obj
                self.proc_q.append(new_key)
                self.choose_representation()
                self.prune_queue()
            if not self.proc_q:
                log.info(f"  i{ct}: Ending due to empty processing queue.")
                break
        self.choose_representation()

    def choose_representation(self) -> None:
        """Find the most compact representation from decomposition."""
        best_props = self.rep.props
        for key, obj in self.tree.items():
            if obj.props < best_props:
                best_props = obj.props
                self.current = key

    def prune_queue(self) -> None:
        """Clean out any low-priority branches from decomposition."""
        threshold = cst.PRUNE_PROPS_COEFF * self.rep.props
        to_prune: list[int] = []
        for idx, key in enumerate(self.proc_q):
            baseline = self.tree[key[: -cst.PRUNE_SKIP_GEN]].props
            if len(key) <= cst.PRUNE_SAFE_GEN:
                continue
            # Prune if the overall compactness isn't competitive
            if self.tree[key].props > threshold:
                to_prune.append(idx)
            # Prune if the compactness isn't improving
            elif self.tree[key].props > baseline:
                to_prune.append(idx)

        for idx in to_prune[::-1]:
            self.proc_q.pop(idx)

    def _decomposition(
        self, obj: Object, inventory: "Inventory", occlusion: PositionSet
    ) -> list[tuple[str, Object]]:
        """Attempts to find a more canonical or condensed way to represent the object"""
        # No children means nothing to simplify
        if len(obj.children) == 0:
            return []
        # Search for the first object that's not decomposed and apply decomposition
        elif not obj.leaf and (match := inventory.find_decomposition_match(obj)):
            # TODO How to incorporate occlusion here?
            log.info(f"Match at distance: {match.dist} to {match.left}")
            linked = match.transform.apply(match.left)
            linked.leaf = True
            linked.process = "Inv"
            return [("I", linked)]
        elif obj.leaf:
            # TODO Need to redo occlusion
            decompositions: list[tuple[str, Object]] = []
            cumulative_occlusion: PositionSet = set([])
            for rev_idx, child in enumerate(obj.children[::-1]):
                relative_occlusion = set(shift_locs(cumulative_occlusion, child.loc))
                child_candidates = self._decomposition(
                    child, inventory=inventory, occlusion=relative_occlusion
                )
                if child_candidates:
                    # Each new decomposition needs to replace any parents
                    for code, new_child in child_candidates:
                        new_obj = obj.copy()
                        new_obj.children[-(1 + rev_idx)] = new_child
                        decompositions.append((code, new_obj))
                    break
                cumulative_occlusion.update(child.locs_abs)
            return decompositions

        log.debug(f"Decomposing {obj} with occ: {occlusion}")
        candidates = self.generate_candidates(obj, occlusion)
        log.debug(f"Generated {len(candidates)} candidates")
        return candidates

    def generate_candidates(
        self, obj: Object, occlusion: PositionSet
    ) -> list[tuple[str, Object]]:
        candidates: list[tuple[str, Object]] = []
        for process_class in self.processes:
            process = process_class()
            if process.test(obj):
                candidate = process.run(obj, occlusion)
                if candidate:
                    candidates.append((process.code, candidate))
            else:
                log.debug(f"{process.__class__.__name__} failed pre-run test")

        return candidates
