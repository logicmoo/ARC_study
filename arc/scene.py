from arc.board import Board, Inventory
from arc.contexts import SceneContext
from arc.definitions import Constants as cst
from arc.object import Object, ObjectDelta
from arc.types import SceneData
from arc.util import logger

log = logger.fancy_logger("Scene", level=30)


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

        # Initially, we start at shallow representations and proceed outward
        self._dist = -1
        self._path = []

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

    def decompose(self, batch: int = cst.BATCH, max_iter: int = cst.MAX_ITER) -> None:
        """Determine a compact representation of the input and output Boards."""
        self.input.decompose(batch=batch, max_iter=max_iter)
        log.info(f"Input decomposition at {self.input.rep.props}")
        if self.output:
            self.output.set_inventory(self.input.rep)
            self.output.decompose(batch=batch, max_iter=max_iter)
            # TODO Handle inventories
            # self.output.decompose(batch=batch, max_iter=max_iter, source=self.input)
            log.info(f"Output decomposition at {self.output.rep.props}")

    # TODO Below needs review/updating
    def match(self):
        """Identify the minimal transformation set needed from input -> output Board."""
        # TODO Handle inventory
        self._dist, self._path = self.recreate(
            self.output.rep, Inventory(self.input.rep)
        )
        log.info(f"Minimal distance transformation ({self.dist}):")
        for delta in self._path:
            obj1, obj2, gen = delta.right, delta.left, delta.generator
            log.info(f"Gen {gen} | {obj1._id} -> {obj2._id}")

    def recreate(
        self, obj: Object, inventory: Inventory
    ) -> tuple[int, list[ObjectDelta]]:
        """Recursively tries to most easily create the given object"""
        delta = inventory.find_closest(obj, threshold=8)
        result = (cst.MAX_DIST, []) if delta is None else (delta.dist, [delta])

        total_dist = 0
        total_deltas = []
        for kid in obj.children:
            kid_dist, kid_deltas = self.recreate(kid, inventory)
            total_dist += kid_dist + cst.CHILD_DIST
            total_deltas.extend(kid_deltas)
        if total_deltas and total_dist < result[0]:
            return (total_dist, total_deltas)
        else:
            return result
