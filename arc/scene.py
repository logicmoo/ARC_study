from collections import defaultdict
from typing import TypeAlias

from arc.board import Board, Inventory
from arc.contexts import SceneContext
from arc.definitions import Constants as cst
from arc.object import Object
from arc.object_delta import ObjectDelta, ObjectPath
from arc.types import SceneData
from arc.util import logger

log = logger.fancy_logger("Scene", level=20)


# We use "Link" for the usage of ObjectDelta when comparing input to output
# where it will also have the 'path' property set
Link: TypeAlias = ObjectDelta
LinkMap: TypeAlias = dict[str, list[Link]]
LinkResult: TypeAlias = tuple[int, list[ObjectDelta]]


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
        self._dist: int | None = None
        self._depth: int | None = None
        self.link_map: LinkMap = {}

    @property
    def props(self) -> int:
        """Sum of total properties used to define the input and output boards."""
        return self.input.rep.props + self.output.rep.props

    @property
    def dist(self) -> int | None:
        """Transformational distance measured between input and output"""
        return self._dist

    @property
    def depth(self) -> int | None:
        """Transformational distance measured between input and output"""
        return self._depth

    def clean(self, decomp_tree_only: bool = False) -> None:

        if not decomp_tree_only:
            self._dist: int | None = None
            self._depth: int | None = None
            del self.link_map
            self.link_map: LinkMap = {}

        self.input.clean()
        self.output.clean()

    def decompose(
        self,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        init: bool = False,
    ) -> None:
        """Determine a compact representation of the input and output Boards."""
        self.input.decompose(max_iter=max_iter, init=init)
        log.info(f"Scene {self.idx} input rep | props {self.input.rep.props}:")
        log.info(self.input.rep)

        inventory = Inventory(self.input.rep)
        self.output.decompose(max_iter=max_iter, inventory=inventory, init=init)
        log.info(f"Scene {self.idx} output rep | props {self.output.rep.props}:")
        log.info(self.output.rep)

    def match(self):
        """Identify the minimal transformation set needed from input -> output Board."""
        # TODO Handle inventory
        self._dist, deltas = self.recreate(self.output.rep, Inventory(self.input.rep))

        # Group the inputs to the match by the Generator characteristic
        self.link_map = defaultdict(list)
        depths: set[int] = set([])
        for delta in deltas:
            self.link_map[delta.transform.char].append(delta)
            if delta.left.depth is not None:
                depths.add(delta.left.depth)

        log.info(f"Depths during match: {depths}")
        if len(depths) == 1:
            self._depth = depths.pop()

        log.info(f"Scene {self.idx} links | distance ({self.dist}):")
        for char, deltas in self.link_map.items():
            log.info(f"  Transform Characteristic: {char or 'None'}")
            for delta in deltas:
                obj1, obj2, trans = delta.left, delta.right, delta.transform
                log.info(f"    {delta.path}, {trans} | {obj1.id} -> {obj2.id}")

    # @logger.log_call(log, ignore_idxs={0, 2})
    def recreate(
        self, obj: Object, inventory: Inventory, path: ObjectPath = tuple()
    ) -> LinkResult:
        """Recursively tries to most easily create the given object"""
        result: LinkResult = (cst.MAX_DIST, [])
        delta = inventory.find_scene_match(obj)
        if delta:
            # TODO Find a more holistic way to track "Object paths"
            delta.path = path
            # TODO We add the scene index to the deltas to avoid heavy structuring later on
            # (i.e. avoid dicts of lists of lists)
            delta.tag = self.idx
            result = (delta.dist, [delta])

        total_dist = 0
        all_deltas: list[ObjectDelta] = []
        for idx, kid in enumerate(obj.children):
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            kid_dist, kid_deltas = self.recreate(kid, inventory, path + (idx,))
            log.debug(f"{idx} {kid} -> {obj} is distance {kid_dist} via {kid_deltas}")
            total_dist += kid_dist + cst.CHILD_DIST
            all_deltas.extend(kid_deltas)
        if all_deltas and total_dist < result[0]:
            return (total_dist, all_deltas)
        else:
            return result
