from collections import defaultdict
from typing import TypeAlias

from arc.board import Board, Inventory
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
RequestTree: TypeAlias = dict[int, "RequestTree"]


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

        # A Scene aims to create a 'transformation path' between the inputs and
        # outputs that minimizes the required parameters.
        self.link_maps: dict[str, LinkMap] = {}
        self.current: str = ""

    @property
    def props(self) -> int:
        """Sum of total properties used to define the input and output boards."""
        return self.input.rep.props + self.output.rep.props

    @property
    def link_map(self) -> LinkMap:
        return self.link_maps.get(self.current, {})

    @property
    def dist(self) -> int | None:
        """Transformational distance measured between input and output"""
        return sum(link.dist for group in self.link_map.values() for link in group)

    @property
    def depth(self) -> int | None:
        """Transformational distance measured between input and output"""
        depths = {link.left.depth for group in self.link_map.values() for link in group}
        if len(depths) == 1:
            return depths.pop()
        return None

    def clean(self, decomp_tree_only: bool = False) -> None:
        if not decomp_tree_only:
            del self.link_maps
            self.link_maps: dict[str, LinkMap] = {}

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

    def paths_to_tree(self, request: set[ObjectPath]) -> RequestTree:
        tree: RequestTree = {}
        for path in request:
            curr = tree
            for idx in path:
                if idx not in curr:
                    curr[idx] = {}
                curr = curr[idx]
        return tree

    def match(self, decomp_char: str, match_request: set[ObjectPath]) -> None:
        """Identify the minimal transformation set needed from input -> output Board."""
        request_tree: RequestTree = self.paths_to_tree(match_request)
        _, links = self.recreate(
            self.output.rep, Inventory(self.input.rep), request_tree
        )

        link_map: LinkMap = defaultdict(list)
        for delta in links:
            # Group the inputs to the match by the Generator characteristic
            link_map[delta.transform.char].append(delta)
        self.link_maps[decomp_char] = link_map
        self.current = decomp_char

        log.info(f"Scene {self.idx} links | distance ({self.dist}):")
        for char, deltas in link_map.items():
            log.info(f"  Transform Characteristic: {char or 'None'}")
            for delta in deltas:
                obj1, obj2, trans = delta.left, delta.right, delta.transform
                log.info(f"    {delta.path}, {trans} | {obj1.id} -> {obj2.id}")

    # @logger.log_call(log, ignore_idxs={0, 2})
    def recreate(
        self,
        obj: Object,
        inventory: Inventory,
        request_tree: RequestTree,
        path: ObjectPath = tuple([]),
    ) -> LinkResult:
        """Recursively tries to most easily create the given object"""
        log.debug(f"Finding scene match at path: {path}")
        result: LinkResult = (cst.MAX_DIST, [])
        delta = inventory.find_scene_match(obj)
        if delta:
            delta.path = path
            # TODO We add the scene index to the deltas to avoid heavy structuring later on
            # (i.e. avoid dicts of lists of lists)
            delta.tag = self.idx
            result = (delta.dist, [delta])
            log.debug(f"Found node match: {result}")

        total_dist = 0
        all_deltas: list[ObjectDelta] = []
        for idx, kid in enumerate(obj.children):
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            # Skip any children for which we don't need a match
            if idx not in request_tree:
                continue
            kid_dist, kid_deltas = self.recreate(
                kid, inventory, request_tree[idx], path + (idx,)
            )
            log.debug(f"{idx} {kid} -> {obj} is distance {kid_dist} via {kid_deltas}")
            total_dist += kid_dist + cst.CHILD_DIST
            all_deltas.extend(kid_deltas)
        if all_deltas and total_dist < result[0]:
            log.debug(f"Choosing children with distance: {total_dist}")
            for delta in all_deltas:
                log.debug(f"  {delta}")
            return (total_dist, all_deltas)
        else:
            return result
