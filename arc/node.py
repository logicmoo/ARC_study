import uuid
from copy import deepcopy
from functools import cached_property
from typing import TypeAlias

from arc.actions import Action
from arc.inventory import Inventory
from arc.labeler import Labeler, all_traits
from arc.link import ObjectDelta
from arc.object import Object, ObjectPath, sort_layer
from arc.object_types import LinkGroup, ObjectCache, ObjectGroup, PathMap, VarCache
from arc.selector import Selector
from arc.template import StructureDef, Template
from arc.types import Args
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

    def __repr__(self) -> str:
        return f"{self.parents} -> Node -> {self.children}"

    def __getitem__(self, key: int) -> "Node":
        return list(sorted(self.children, key=lambda x: x.uid))[key]

    @cached_property
    def uid(self) -> uuid.UUID:
        """Generate a unique ID for the node, for storing results in cache."""
        return uuid.uuid4()

    @property
    def name(self) -> str:
        return "Node"

    @property
    def depth(self) -> int:
        if not self.parents:
            return 0
        return max(inp.depth for inp in self.parents) + 1

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
        return {f"{mark}({idx}) {self.name}": child_dict}

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


class SelectionNode(Node):
    """Choose Objects from a set of inputs, based on criteria."""

    def __init__(
        self,
        selector: Selector,
        parents: set["Node"] | None = None,
        children: set["Node"] | None = None,
    ) -> None:
        super().__init__(parents or set(), children or set())
        self.selector = selector

    def __repr__(self) -> str:
        return f"Select {self.selector}"

    @property
    def name(self) -> str:
        return f"S {self.selector}"

    def apply(self, object_cache: ObjectCache, var_cache: VarCache) -> list[Object]:
        input_objects, _ = self.fetch_inputs(object_cache)
        selection = self.selector.select(input_objects)
        object_cache[self.uid] = selection
        return selection

    @property
    def props(self) -> int:
        return self.selector.props

    @classmethod
    def from_data(cls, inputs: ObjectGroup, selection: ObjectGroup) -> "SelectionNode":
        return cls(Selector(inputs, selection))


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
        return f"V {self.property}"

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


class TransNode(Node):
    def __init__(
        self,
        action: type[Action],
        arg_info: ArgInfo = tuple(),
        parents: set["Node"] | None = None,
        children: set["Node"] | None = None,
        secondary: "Node | None" = None,
    ) -> None:
        super().__init__(parents or set(), children or set(), secondary)
        self.action = action
        self.arg_info = arg_info

    @property
    def props(self) -> int:
        return 1 + len(self.arg_info)

    def __repr__(self) -> str:
        return f"{self.action}({self.arg_info})"

    @property
    def name(self) -> str:
        return f"T {self.action}"

    def apply(
        self, object_cache: ObjectCache, var_cache: VarCache
    ) -> list[Object] | None:
        input_objects, labeler = self.fetch_inputs(object_cache)

        result: list[Object] = []
        for object in input_objects:
            args: TransformArgs = tuple([])
            if self.secondary:
                if isinstance(self.secondary, VarNode):
                    args = (var_cache[self.secondary.uid],)
                else:
                    args = (object_cache[self.secondary.uid][0],)
            else:
                for arg in self.arg_info:
                    if isinstance(arg, tuple):
                        trait, mapping = arg
                        trait_value = labeler.labels[object.uid].get(trait)
                        log.debug(
                            f"Transforming using {self.action}({trait} mapping {mapping})"
                        )
                        try:
                            # Seems like structural pattern matching confuses type checking
                            args += (mapping[trait_value],)  # type: ignore
                        except KeyError as _:
                            log.info(f"Mapping {mapping} doesn't contain {trait_value}")
                            return None
                    else:
                        args += (arg,)

            result.append(self.action.act(object, *args))

        object_cache[self.uid] = result
        return result

    @classmethod
    def from_action(
        cls,
        action: type[Action],
        link_node: LinkGroup,
    ) -> "TransNode | None":

        args: ArgInfo = tuple([])
        deltas = [delta for group in link_node for delta in group]
        selection = [[delta.left for delta in group] for group in link_node]

        # TODO NOTE We have a single transform (code len == 1)
        raw_args: set[Args] = set()
        for delta in deltas:
            d_args = delta.transform.args
            if not d_args:
                raw_args.add(tuple([]))
            else:
                raw_args.add(action.rearg(delta.left, *(d_args[0])))

        if len(raw_args) > 1:
            if len(list(raw_args)[0]) > 1:
                log.warning(f"Cannot map multi-args")
                return None
            # Non-null, non-constant action arguments means we need a mapping
            # or a secondary object to provide the value.
            labeler = Labeler(selection)
            arg_mapping = cls.determine_map(deltas, labeler)
            if not arg_mapping[0]:
                return None
            args = (arg_mapping,)
        else:
            if None in raw_args:
                return None
            args = tuple(map(int, raw_args.pop()))

        if args is None or None in args or len(args) > action.n_args:
            return None

        return cls(action, args)

    @staticmethod
    def determine_map(
        delta_list: list[ObjectDelta],
        labeler: Labeler,
    ) -> tuple[str, dict[int, int]]:
        result: tuple[str, dict[int, int]] = ("", {})
        for trait in all_traits:
            trial_map: dict[int, int] = {}
            for delta in delta_list:
                inp = labeler.labels[delta.left.uid][trait]
                # TODO We're assuming a single action with a single arg for now
                if not delta.transform.args or not delta.transform.args[0]:
                    return result
                out = delta.transform.args[0][0]

                if inp in trial_map:
                    # TODO: Handle Labeling with type safety, non-mutation
                    if trial_map[inp] != out:  # type: ignore
                        log.debug(
                            f"Trait {trait} fails at {inp} -> {out} | {trial_map}"
                        )
                        trial_map = {}
                        break
                    else:
                        continue
                trial_map[inp] = out  # type: ignore

            if trial_map:
                log.debug(f"Trait {trait}: {trial_map}")
                if not result[0] or len(trial_map) < len(result[1]):
                    result = (trait, trial_map)
        return result

    @classmethod
    def from_pairwise_action(
        cls,
        action: type[Action],
        link_node: LinkGroup,
        inputs: ObjectGroup,
    ) -> "TransNode | None":
        log.debug(f"Determining selector for {action}")
        secondaries: list[Object] = []
        for delta_group, candidates in zip(link_node, inputs):
            for delta in delta_group:
                for obj in candidates:
                    # TODO Figure out a better way for an object to not be
                    # matched up with its children
                    if obj in delta.left.children:
                        continue
                    if action.act(delta.left, obj) == delta.right:
                        log.debug(f"Choosing secondary: {obj}")
                        secondaries.append(obj)
                        break
        if len(secondaries) < len(link_node):
            log.info(f"Insufficient secondaries found for {action}")
            return None
        selection_node = SelectionNode.from_data(inputs, [secondaries])
        log.info(f"Pairwise selector for {action}: {selection_node}")
        trans_node = cls(action, arg_info=tuple(), secondary=selection_node)
        selection_node.adopt(trans_node)
        return trans_node
