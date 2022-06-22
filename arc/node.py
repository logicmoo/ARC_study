import uuid
from copy import deepcopy
from functools import cached_property
from typing import TypeAlias

from arc.inventory import Inventory
from arc.labeler import Labeler
from arc.object import Object, ObjectPath, sort_layer
from arc.object_types import ObjectCache, ObjectGroup, PathMap, VarCache
from arc.template import StructureDef, Template
from arc.util import logger

log = logger.fancy_logger("Solution", level=20)

try:
    from asciitree import LeftAligned  # type: ignore
except:
    log.warning("Python pkg 'asciitree' not found, falling back to ugly trees.")


NodeTree: TypeAlias = dict[str, "NodeTree"]


# TODO Find a better naming system
Info: TypeAlias = int | tuple[str, None | dict[int, int]]
ArgInfo: TypeAlias = tuple[Info, ...]
ActionArg: TypeAlias = int | Object
TransformArgs: TypeAlias = tuple[ActionArg, ...]


class Node:
    """Base class for a graph with bi-directional traversal."""

    def __init__(
        self,
        parents: set["Node"],
        children: set["Node"],
        secondary: "Node | None" = None,
    ) -> None:
        self.parents: set["Node"] = parents
        self.children: set["Node"] = children
        self.secondary: "Node | None" = secondary

    @property
    def name(self) -> str:
        return "Node"

    @property
    def args(self) -> list[str]:
        return []

    def __repr__(self) -> str:
        return f"{self.name} | {''.join(self.args)}"

    def __getitem__(self, key: int) -> "Node":
        return list(sorted(self.children, key=lambda x: x.uid))[key]

    @property
    def info(self) -> str:
        return f"{self.name}\n{chr(10).join(self.args)}"  # chr(10) is \n

    @cached_property
    def uid(self) -> uuid.UUID:
        """Generate a unique ID for the node, for storing results in cache."""
        return uuid.uuid4()

    @property
    def level(self) -> int:
        if not self.parents:
            return 0
        return max(inp.level for inp in self.parents) + 1

    @property
    def props(self) -> int:
        return 0

    def _get_tree(self, idx: int = 0, secondary: bool = False) -> NodeTree:
        """Return nested dicts as a tree approximation of the Solution.

        This splits any merges (e.g. diamonds) in the directed graph.
        """
        child_dict: NodeTree = {}
        for c_idx, child in enumerate(self.children):
            child_dict.update(child._get_tree(c_idx, child.secondary == self))
        mark = "*" if secondary else ""
        return {f"{mark}({idx}) {self}": child_dict}

    def tree(self) -> str:
        return LeftAligned()(self._get_tree())

    def adopt(self, child: "Node") -> None:
        self.children.add(child)
        child.parents.add(self)

    def disown(self, child: "Node") -> None:
        self.children.remove(child)
        child.parents.remove(self)

    def test_inputs(self, object_cache: ObjectCache, var_cache: VarCache) -> bool:
        for in_node in self.parents:
            if in_node.uid not in object_cache and in_node.uid not in var_cache:
                return False
        return True

    def fetch_inputs(self, object_cache: ObjectCache) -> tuple[list[Object], Labeler]:
        input_objects: list[Object] = []
        for in_node in self.parents:
            if in_node == self.secondary:
                continue
            input_objects.extend(object_cache[in_node.uid])

        labeler = Labeler([input_objects])
        return input_objects, labeler

    def apply(
        self, object_cache: ObjectCache, var_cache: VarCache
    ) -> list[Object] | int | None:
        return None

    def propagate(self, object_cache: ObjectCache, var_cache: VarCache) -> None:
        if not self.test_inputs(object_cache, var_cache):
            return
        if self.uid not in object_cache and self.uid not in var_cache:
            self.apply(object_cache, var_cache)
        for child in self.children:
            child.propagate(object_cache, var_cache)


class RootNode(Node):
    def __init__(
        self,
        level_attention: int | None = None,
        children: set["Node"] | None = None,
    ) -> None:
        super().__init__(parents=set(), children=children or set())
        self.level_attention = level_attention

    @property
    def name(self) -> str:
        return "Root"

    @property
    def args(self) -> list[str]:
        return [f"Attention: {self.level_attention}"]

    def apply(self, object_cache: ObjectCache, var_cache: VarCache) -> list[Object]:
        _, input_objects = object_cache.popitem()
        input_rep = input_objects[0]
        output: list[Object] = []
        if self.level_attention is not None:
            log.info(f"  Using level attention: {self.level_attention}")
            output = Inventory(input_rep).depth[self.level_attention]
        else:
            log.info(f"  No level attention")
            output = Inventory(input_rep).all
        log.debug(f"  input_group: {output}")
        object_cache[self.uid] = output
        return output

    @property
    def props(self) -> int:
        if self.level_attention is not None:
            return 1
        else:
            return 0


class TerminalNode(Node):
    def __init__(
        self,
        structure: StructureDef,
        path_map: PathMap,
        parents: set["Node"] | None = None,
    ) -> None:
        super().__init__(parents=parents or set(), children=set())
        self.structure = structure
        self.path_map = path_map

    @property
    def name(self) -> str:
        return "Terminus"

    def apply(self, object_cache: ObjectCache, var_cache: VarCache) -> list[Object]:
        frame = deepcopy(self.structure)
        for parent in self.parents:
            paths: set[ObjectPath] = self.path_map[parent.uid]
            if isinstance(parent, VarNode):
                path = list(paths)[0]
                Template.apply_variable(frame, path, var_cache[parent.uid])
            else:
                objs = sort_layer(object_cache[parent.uid])
                for (path, obj) in zip(sorted(paths), objs):
                    frame = Template.apply_object(frame, path, obj)
        output = [Template.generate(frame)]
        object_cache[self.uid] = output
        return output

    @property
    def props(self) -> int:
        return len(self.path_map)


class VarNode(Node):
    def __init__(
        self,
        property: str,
        parents: set["Node"] | None = None,
        children: set["Node"] | None = None,
    ) -> None:
        super().__init__(parents or set(), children or set())
        self.property = property

    @property
    def name(self) -> str:
        return "Variable"

    @property
    def args(self) -> list[str]:
        return [f"Property: {self.property}"]

    @classmethod
    def from_property(
        cls,
        property: str,
        object_node: ObjectGroup,
    ) -> "VarNode | None":
        if not all(len(group) == 1 for group in object_node):
            log.warning("VariableNode can't handle multi-groups")
            return None

        return cls(property)

    def apply(self, object_cache: ObjectCache, var_cache: VarCache) -> int | None:
        input_objects, _ = self.fetch_inputs(object_cache)
        if len(input_objects) > 1:
            log.warning(f"VarNode {self.uid} got more than one input Object")
        value = input_objects[0].get_value(ObjectPath(property=self.property))
        if value:
            var_cache[self.uid] = value
        return value
