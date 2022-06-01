from typing import TypeAlias

from arc.board import Board, Inventory
from arc.definitions import Constants as cst
from arc.object import Object, ObjectPath
from arc.object_delta import ObjectDelta, VariableLink
from arc.template import Variables
from arc.types import BaseObjectPath, SceneData
from arc.util import logger

log = logger.fancy_logger("Scene", level=20)

# We use "Link" for the usage of ObjectDelta when comparing input to output
# where it will also have the 'path' property set
Link: TypeAlias = ObjectDelta | VariableLink
LinkMap: TypeAlias = dict[ObjectPath, Link]
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
        return sum(link.dist for link in self.link_map.values())

    @property
    def depth(self) -> int | None:
        """Transformational distance measured between input and output"""
        depths = {link.left.depth for link in self.link_map.values()}
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

    def paths_to_tree(self, variables: Variables) -> RequestTree:
        tree: RequestTree = {}
        for path in variables:
            curr = tree
            for idx in path:
                if idx not in curr:
                    curr[idx] = {}
                curr = curr[idx]
        return tree

    def link(self, decomp_char: str, variables: Variables) -> None:
        """Identify objects + properties that can fill a variable."""
        inputs: list[Object] = Inventory(self.input.rep).all
        log.debug(f"Looking for variable links from {len(inputs)} objects:")
        for obj in inputs:
            log.debug(obj)

        candidates: LinkMap = {}
        for obj_path in variables:
            # TODO Skip Generator links for now
            if not isinstance(obj_path.property, str):
                continue
            log.debug(f"Searching for link to {obj_path}")
            output_rep = self.output.tree[self.output.characteristic_map[decomp_char]]
            value = output_rep.get_value(obj_path)
            if value is None:
                log.warning(f"Couldn't find {obj_path}")
                continue

            # TODO Just check the same property among the inputs for now
            # E.g. if we need a 'color' input, use 'color' from an Inventory object.
            prop = obj_path.property
            for obj in inputs:
                if value == getattr(obj, prop):
                    log.debug(f"Candidate: {obj}")
                    candidates[obj_path] = VariableLink(obj, prop, value)

        self.link_maps[decomp_char].update(candidates)

    def match(self, decomp_char: str, variables: Variables) -> None:
        """Identify the minimal transformation set needed from input -> output Board."""
        request_tree: RequestTree = self.paths_to_tree(variables)
        _, links = self.recreate(
            self.output.rep, Inventory(self.input.rep), request_tree
        )

        link_map: LinkMap = {}
        for delta in links:
            # Group the inputs to the match by the Generator characteristic
            link_map[ObjectPath(delta.path)] = delta
        self.link_maps[decomp_char] = link_map
        self.current = decomp_char

        log.info(f"Scene {self.idx} links | distance ({self.dist}):")
        for path, link in link_map.items():
            if isinstance(link, ObjectDelta):
                obj1, obj2, trans = link.left, link.right, link.transform
                log.info(f"    {path}, {trans} | {obj1.id} -> {obj2.id}")
            else:
                log.info(f"    {path} | {link.left.id} -> {link.property}")

    # @logger.log_call(log, ignore_idxs={0, 2})
    def recreate(
        self,
        obj: Object,
        inventory: Inventory,
        request_tree: RequestTree,
        path: BaseObjectPath = tuple([]),
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
