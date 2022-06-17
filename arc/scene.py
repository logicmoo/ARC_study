from typing import TypeAlias

from arc.board import Board, Inventory
from arc.definitions import Constants as cst
from arc.link import ObjectDelta, VariableLink
from arc.object import Object, ObjectPath
from arc.types import BaseObjectPath, PrefixTree, SceneData
from arc.util import logger

log = logger.fancy_logger("Scene", level=20)

# We use "Link" for the usage of ObjectDelta when comparing input to output
# where it will also have the 'path' property set
Link: TypeAlias = ObjectDelta | VariableLink
LinkMap: TypeAlias = dict[ObjectPath, Link]
LinkResult: TypeAlias = tuple[int, LinkMap]
Variables: TypeAlias = set[ObjectPath]


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
        """Remove temporary material used during linking.

        Take out the extra link maps that were explored, but not used for the
        end result.
        """
        if not decomp_tree_only:
            current = None
            if self.current:
                current = self.link_maps[self.current]
            del self.link_maps
            if current is not None:
                self.link_maps: dict[str, LinkMap] = {self.current: current}

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

    def paths_to_tree(self, variables: Variables) -> PrefixTree:
        """Create a prefix tree for the Variable paths.

        Each variable has a BaseObjectPath (e.g. (0, 3, 1)) that points to an Object
        in the hierarchy. One can create a prefix tree from these where a node exists
        if any variable has a path that includes that value at that position.
        """
        tree: PrefixTree = {}
        for path in variables:
            curr = tree
            for idx in path:
                if idx not in curr:
                    curr[idx] = {}
                curr = curr[idx]
        return tree

    def search_tree(self, tree: PrefixTree, path: ObjectPath) -> bool:
        for idx in path.base:
            if idx not in tree:
                return False
            tree = tree[idx]
        return True

    def link(self, decomp_char: str, variables: Variables) -> None:
        """Identify the minimal transformation set needed from input -> output Board."""
        # Begin by checking for transformable Objects
        link_tree: PrefixTree = self.paths_to_tree(variables)
        log.debug(link_tree)
        _, link_map = self.recreate(
            self.output.rep, Inventory(self.input.rep), link_tree
        )

        # Then determine links due to variables insertion
        log.debug(link_tree)
        link_map.update(self.variable_link(decomp_char, variables, link_tree))

        self.link_maps[decomp_char] = link_map
        self.current = decomp_char

        log.info(f"Scene {self.idx} links | distance ({self.dist}):")
        for _, link in link_map.items():
            log.info(f"    {link}")

    def variable_link(
        self, decomp_char: str, variables: Variables, link_tree: PrefixTree
    ) -> LinkMap:
        """Identify objects + properties that can fill a variable."""
        inputs: list[Object] = Inventory(self.input.rep).all
        log.debug(f"Looking for variable links from {len(inputs)} objects:")
        for obj in inputs:
            log.debug(obj)

        link_map: LinkMap = {}
        for obj_path in variables:
            if obj_path.property is None:
                continue

            if not self.search_tree(link_tree, obj_path):
                continue

            log.debug(f"Searching for link to {obj_path}")
            output_rep = self.output.tree[self.output.characteristic_map[decomp_char]]
            target = self.output.rep.get_path(obj_path.base)
            value = output_rep.get_value(obj_path)
            if target is None or value is None:
                log.warning(f"Couldn't find {obj_path}")
                continue

            # TODO Just check the same property among the inputs for now
            # E.g. if we need a 'color' input, use 'color' from an Inventory object.
            prop = obj_path.property
            for obj in inputs:
                if value == obj.get_value(ObjectPath(property=prop)):
                    log.debug(f"Candidate: {obj}")
                    link_map[obj_path] = VariableLink(
                        obj, target, obj_path.base, prop, value
                    )

        return link_map

    # @logger.log_call(log, ignore_idxs={0, 2})
    def recreate(
        self,
        obj: Object,
        inventory: Inventory,
        link_tree: PrefixTree,
        base: BaseObjectPath = tuple([]),
    ) -> LinkResult:
        """Recursively tries to most easily create the given object"""
        log.debug(f"Finding scene match at path: {base}")
        result: LinkResult = (cst.MAX_DIST, {})
        delta = inventory.find_scene_match(obj)
        if delta:
            delta.base = base
            # TODO We add the scene index to the deltas to avoid heavy structuring later on
            # (i.e. avoid dicts of lists of lists)
            delta.tag = self.idx
            result = (delta.dist, {ObjectPath(base): delta})
            log.debug(f"Found node match: {result}")

        total_dist = 0
        link_map: LinkMap = {}
        for idx, kid in enumerate(obj.children):
            # TODO Handle Cutout in a better way?
            # It currently can't be used as an object on it's own because self.points is empty.
            if kid.category == "Cutout":
                continue
            # Skip any children for which we don't need a match based on the Template
            if idx not in link_tree:
                continue
            kid_dist, kid_map = self.recreate(
                kid, inventory, link_tree[idx], base + (idx,)
            )
            log.debug(f"{idx} {kid} -> {obj} is distance {kid_dist} via {kid_map}")
            total_dist += kid_dist
            link_map.update(kid_map)

        if link_map and total_dist < result[0]:
            log.debug(f"{base} Choosing children: {total_dist} < {result[0]}")
            for link in link_map.values():
                log.debug(f"  {link}")
            link_tree.clear()
            return (total_dist, link_map)
        elif result[0] != cst.MAX_DIST:
            log.debug(f"{base} Choosing parent: {result[0]} < {total_dist}")
            link_tree.clear()
            return result
        else:
            log.debug(f"{base} No linkable Object found")
            return result
