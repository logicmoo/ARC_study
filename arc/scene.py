from collections import defaultdict
from arc.board import Board, Inventory
from arc.contexts import SceneContext
from arc.definitions import Constants as cst
from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.types import SceneData
from arc.util import logger

log = logger.fancy_logger("Scene", level=20)


class Scene:
    """One pair of Boards defining a 'case' or a 'test' for the Task.

    Attributes:
      idx: Numerical index of the scene as presented in the data.
      input: the input Board.
      output: the output Board.
      context: A learned set of variables that might influence operations.
    """

    def __init__(self, data: SceneData, idx: int = 0):
        self.idx = idx
        self.input = Board(data["input"], name=f"Input {idx}")
        self.output = Board(data["output"], name=f"Output {idx}")

        # Context is built between input/output, and might influence a redo
        self.context = SceneContext()

        # A Scene aims to create a 'transformation path' between the inputs and
        # outputs that minimizes the required parameters.
        self._dist: float = -1
        self.path: dict[str, list[ObjectDelta]] = {}

    @property
    def props(self) -> int:
        """Sum of total properties used to define the input and output boards."""
        return self.input.rep.props + self.output.rep.props

    @property
    def ppp(self) -> float:
        """Properties per Point: a measure of representation compactness."""
        return self.props / (self.input.rep.size + self.output.rep.size)

    @property
    def dist(self) -> float:
        """Transformational distance measured between input and output"""
        return self._dist

    def decompose(
        self,
        batch: int = cst.DEFAULT_BATCH,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        init: bool = False,
    ) -> None:
        """Determine a compact representation of the input and output Boards."""
        self.input.decompose(batch=batch, max_iter=max_iter, init=init)
        log.info(f"Scene {self.idx} input rep | props {self.input.rep.props}:")
        log.info(self.input.rep)

        inventory = Inventory(self.input.rep)
        self.output.decompose(batch, max_iter, inventory=inventory, init=init)
        log.info(f"Scene {self.idx} output rep | props {self.output.rep.props}:")
        log.info(self.output.rep)

    def match(self):
        """Identify the minimal transformation set needed from input -> output Board."""
        # TODO Handle inventory
        self._dist, deltas = self.recreate(self.output.rep, Inventory(self.input.rep))

        # Group the inputs to the match by the Generator characteristic
        self.path = defaultdict(list)
        for delta in deltas:
            self.path[delta.transform.char].append(delta)

        log.info(f"Scene {self.idx} path | distance ({self.dist}):")
        for char, deltas in self.path.items():
            log.info(f"  Generator Characteristic: {char or 'None'}")
            for delta in deltas:
                obj1, obj2, trans = delta.left, delta.right, delta.transform
                log.info(f"    {trans} | {obj1.id} -> {obj2.id}")

    # TODO: Simplify the return here
    def recreate(
        self, obj: Object, inventory: Inventory
    ) -> tuple[int, list[ObjectDelta]]:
        """Recursively tries to most easily create the given object"""
        result: tuple[int, list[ObjectDelta]] = (cst.MAX_DIST, [])
        delta = inventory.find_closest(obj, threshold=8)
        if delta:
            result = (delta.dist, [delta])

        total_dist = 0
        total_deltas: list[ObjectDelta] = []
        for kid in obj.children:
            kid_dist, kid_deltas = self.recreate(kid, inventory)
            log.debug(f"{kid} -> {obj} is distance {kid_dist} via {kid_deltas}")
            total_dist += kid_dist + cst.CHILD_DIST
            total_deltas.extend(kid_deltas)
        if total_deltas and total_dist < result[0]:
            return (total_dist, total_deltas)
        else:
            return result
