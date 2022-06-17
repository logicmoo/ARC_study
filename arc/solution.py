import uuid
from collections import defaultdict
from typing import Any, TypeAlias

import numpy as np

from arc.actions import Action, Actions, Pairwise
from arc.board import Inventory
from arc.labeler import Labeler, all_traits
from arc.link import ObjectDelta, VariableLink
from arc.node import Node, RootNode, SelectionNode, TerminalNode, TransNode, VarNode
from arc.object import Object, ObjectPath, sort_layer
from arc.object_types import Cache, LinkGroup, ObjectCache, ObjectGroup, VarCache
from arc.scene import Scene
from arc.selector import Selector, subdivide_groups
from arc.template import Template
from arc.types import Args
from arc.util import logger

log = logger.fancy_logger("Solution", level=20)

ActionArg: TypeAlias = int | Selector | tuple[str, None | dict[int, int]]


class SolutionNode:
    """A single object operation

    The Solution nodes form a directed graph that convert the input signal
    to the appropriate output. It takes two forms:
      - Variable: Assigning a property at a Path based on a selection.
      - Transform: Transform selected input Objects and insert at Paths.
    """

    def __init__(
        self,
        selector: Selector,
        paths: set[ObjectPath] = set([]),
    ) -> None:
        # TODO: For now, only depth-1 Solutions, so assume no children.
        # self.children: list[SolutionNode] = []
        self.selector = selector
        self.paths = paths

    def apply(self, input: list[Object]) -> list[Object] | int | None:
        return None

    @property
    def props(self) -> int:
        return 0


class VariableNode(SolutionNode):
    def __init__(
        self, selector: Selector, property: str, paths: set[ObjectPath] = set([])
    ) -> None:
        super().__init__(selector, paths)
        self.property = property

    def __repr__(self) -> str:
        return f"Select {self.selector}.{self.property} -> {self.paths}"

    @classmethod
    def from_variable(
        cls,
        inputs: list[list[Object]],
        links: list[VariableLink],
        path: ObjectPath,
    ) -> "SolutionNode | None":
        link_node: list[list[Object]] = [[link.left] for link in links]

        if not all(len(group) == 1 for group in link_node):
            log.warning("VariableNode can't handle multi-groups")
            return None

        selector = Selector(inputs, link_node)
        property = links[0].property

        return cls(selector, property, {path})

    def apply(self, input: list[Object]) -> int | None:
        selection = self.selector.select(input)
        if len(selection) > 1:
            log.warning("VariableNode produced more than one object")
            return None
        elif not selection:
            log.warning(f"Unable to select {self.selector} from {input}")
            return None

        return selection[0].get_value(ObjectPath(property=self.property))


class TransformNode(SolutionNode):
    def __init__(
        self,
        selector: Selector,
        action: type[Action] = Action,
        args: tuple[ActionArg, ...] = tuple(),
        paths: set[ObjectPath] = set([]),
    ) -> None:
        super().__init__(selector, paths)
        self.action = action
        self.args = args

    def __repr__(self) -> str:
        return f"({self.props})Select {self.selector} -> {self.action}{self.args} -> {self.paths}"

    @property
    def props(self) -> int:
        total_props = 0
        for arg in self.args:
            if isinstance(arg, Selector):
                total_props += arg.props
            elif isinstance(arg, int):
                total_props += 1
            else:
                total_props += 1
                try:
                    if arg[1] is None:
                        total_props += 100
                    else:
                        total_props += 2 * len(arg[1])
                except:
                    log.warning(f"Node on {self.action} has arg issue: {self.args}")
        return total_props

    @classmethod
    def from_action(
        cls,
        inputs: list[list[Object]],
        link_node: list[list[ObjectDelta]],
        action: type[Action] = Action,
    ) -> list["TransformNode | None"]:
        selectors: list[Selector] = []

        # Try a single selector first
        selection = [[delta.left for delta in group] for group in link_node]
        bundle: list[list[list[ObjectDelta]]] = [link_node]
        selector = Selector(inputs, selection)
        if not selector:
            log.info("Single Selection failed, trying to split")
            # Attempt to divide the link node into groups based on similarity
            bundle = subdivide_groups(link_node)
            for subnode in bundle:
                subselection = [[delta.left for delta in group] for group in subnode]
                selector = Selector(inputs, subselection)
                if not selector:
                    log.info("Failed to yield selectors")
                    return [None]
                selectors.append(selector)
            if not selectors:
                log.info("Failed to yield selectors")
                return [None]
        else:
            selectors = [selector]

        nodes: list[TransformNode | None] = []
        for selector, subnode in zip(selectors, bundle):
            args: tuple[ActionArg, ...] = tuple([])
            deltas = [delta for group in subnode for delta in group]
            paths = {ObjectPath(delta.base) for delta in deltas}

            if issubclass(action, Pairwise):
                log.debug(f"Determining selector for {action}")
                secondaries: list[Object] = []
                for delta_group, candidates in zip(subnode, inputs):
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
                    return [None]
                args = (Selector(inputs, [secondaries]),)
                log.info(f"Pairwise selector for {action}: {args[0]}")
            else:
                # now check the arguments
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
                        return [None]
                    # Non-null, non-constant action arguments means we need a mapping
                    # or a secondary object to provide the value.
                    labeler = Labeler(selection)
                    arg_mapping = cls.determine_map(deltas, labeler)
                    if not arg_mapping[0]:
                        return [None]
                    args = (arg_mapping,)
                else:
                    if None in raw_args:
                        return [None]
                    args = tuple(map(int, raw_args.pop()))

            if args is None or None in args or len(args) > action.n_args:
                return [None]
            nodes.append(cls(selector, action, args, paths))

        return nodes

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

    def apply(self, input: list[Object]) -> list[Object] | None:
        selection = self.selector.select(input)
        result: list[Object] = []
        labeler = Labeler([selection])
        for obj in selection:
            args: list[Object | int] = []
            for arg in self.args:
                match arg:
                    case int(value):
                        args.append(value)
                    # TODO Ideally, we avoid this type entirely. We should find all
                    # points of entry for np.int64 and cast to int.
                    case np.int64():
                        args.append(arg)
                    case Selector():
                        log.debug(f"Transforming using {self.action}(arg)")
                        if selection := arg.select(input):
                            args.append(selection[0])
                        else:
                            log.warning(f"No object selected for Selector({arg})")
                            args.append(obj)
                    case (str(trait), None):
                        log.debug(f"Transforming using {self.action}({trait})")
                        trait_value = labeler.labels[obj.uid].get(trait)
                        args.append(trait_value)  # type: ignore
                    case (str(trait), {**mapping}):
                        log.debug(
                            f"Transforming using {self.action}({trait} mapping {mapping})"
                        )
                        trait_value = labeler.labels[obj.uid].get(trait)
                        try:
                            # Seems like structural pattern matching confuses type checking
                            args.append(mapping[trait_value])  # type: ignore
                        except KeyError as _:
                            log.info(f"Mapping {mapping} doesn't contain {trait_value}")
                            return None
                    case _:
                        log.warning(f"Unhandled action arg: {arg}")

            result.append(self.action.act(obj, *args))
        return result


class Solution:
    """Contain the information needed to convert an input board to a correct output.

    A solution is a directed graph of transformation nodes that takes a raw input board
    and can create the correct output board. Each solution is presumed to have
    decomposition as the first node/step in the process. The result of decomposition
    is then fed into 1+ nodes organized in 1+ layers.
    """

    def __init__(
        self,
        characteristic: str = "",
        attention: int | None = None,
        template: Template | None = None,
    ) -> None:
        self.characteristic: str = characteristic
        self.template: Template = template or Template()

        # Create during 'create_nodes'
        self.nodes: list[SolutionNode] = []
        self.node2: dict[uuid.UUID, Node] = {}
        self.root: RootNode = RootNode(attention)
        self.terminus: TerminalNode = TerminalNode(self.template.init_structure(), {})

    def __repr__(self) -> str:
        msg: list[str] = [f"Decomposition characteristic: {self.characteristic}"]
        msg += [f"Level attention: {self.root.level_attention}"]
        for node in self.nodes:
            msg.append(str(node))
        msg.append(str(self.template))
        return "\n".join(msg)

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle object transforms together from the Scene link maps.

        This aims to approximately identify the SolutionNodes we need.
        """
        self.bundled: dict[str, list[ObjectDelta]] = defaultdict(list)
        self.var_targets: dict[ObjectPath, list[VariableLink]] = defaultdict(list)
        for case in cases:
            for path, link in case.link_map.items():
                if isinstance(link, ObjectDelta):
                    self.bundled[link.transform.char].append(link)
                else:
                    self.var_targets[path].append(link)

    def create_nodes(self, cases: list[Scene]) -> bool:
        self.nodes = []
        inputs = [
            self.root.apply({uuid.uuid4(): [case.input.rep]}, {}) for case in cases
        ]
        caches: list[tuple[ObjectCache, VarCache]] = []

        self.terminus: TerminalNode = TerminalNode(self.template.structure, {})
        self.node2 = {self.root.uid: self.root, self.terminus.uid: self.terminus}

        for path, links in self.var_targets.items():
            raw_node = VariableNode.from_variable(inputs, links, path)
            if raw_node:
                self.nodes.append(raw_node)
            selection: ObjectGroup = [[link.left] for link in links]
            if selection_node := SelectionNode.from_data(inputs, selection):
                self.root.adopt(selection_node)
                self.node2[selection_node.uid] = selection_node
            property = links[0].property
            if var_node := VarNode.from_property(property, selection):
                selection_node.adopt(var_node)
                var_node.adopt(self.terminus)
                self.terminus.path_map[var_node.uid] = {path}

        for code, transform_group in self.bundled.items():
            if len(code) > 1:
                log.info(
                    f"Skipping (code > 1) Link {transform_group[0].transform.char}"
                )
                continue

            # The link node is a list of lists of ObjectDeltas related to the transform
            link_node: list[list[ObjectDelta]] = []
            for case in cases:
                case_node = [
                    delta for delta in transform_group if delta.tag == case.idx
                ]
                link_node.append(case_node)
            link_node = list(filter(None, link_node))
            selection = [[delta.left for delta in group] for group in link_node]
            if selection_node := SelectionNode.from_data(inputs, selection):
                self.root.adopt(selection_node)
                self.node2[selection_node.uid] = selection_node
                caches: list[tuple[ObjectCache, VarCache]] = []
                for case in cases:
                    obj_cache: ObjectCache = {uuid.uuid4(): [case.input.rep]}
                    var_cache: VarCache = {}
                    self.root.apply(obj_cache, var_cache)
                    selection_node.apply(obj_cache, var_cache)
                    caches.append((obj_cache, var_cache))
            else:
                return False

            candidate_nodes: list[TransformNode] = []
            v2_nodes: list[TransNode] = []
            base_action = Actions.map[code]
            paths = {ObjectPath(delta.base) for delta in transform_group}
            action_queue = [base_action]
            while action_queue:
                action = action_queue.pop(0)
                # NOTE In general, we cannot have a situation where an action with more
                # args non-trivially replaces an action with fewer.
                if action.n_args > base_action.n_args:
                    continue
                log.debug(f"Attempting Solution node for action '{action}'")
                raw_nodes = TransformNode.from_action(inputs, link_node, action)
                raw = raw_nodes[0]
                if raw:
                    candidate_nodes.append(raw)

                if issubclass(action, Pairwise):
                    if trans_node := TransNode.from_pairwise_action(
                        action, link_node, inputs
                    ):
                        v2_nodes.append(trans_node)
                else:
                    if trans_node := TransNode.from_action(action, link_node):
                        v2_nodes.append(trans_node)

                action_queue.extend(action.__subclasses__())

            node2 = self.choose_node(v2_nodes, selection_node, caches, link_node)
            if node2:
                node2.adopt(self.terminus)
                self.terminus.path_map[node2.uid] = paths
                self.node2[node2.uid] = node2
                if node2.secondary:
                    self.node2[node2.secondary.uid] = node2.secondary
            if node := self.choose_node_old(candidate_nodes, inputs, link_node):
                self.nodes.append(node)
            else:
                return False
        return True

    def choose_node(
        self,
        candidate_nodes: list[TransNode],
        selection_node: SelectionNode,
        caches: list[tuple[ObjectCache, VarCache]],
        link_node: LinkGroup,
    ) -> TransNode | None:
        log.info(" --- Candidate nodes:")
        for node in candidate_nodes:
            log.info(node)
        for trans in sorted(candidate_nodes, key=lambda x: x.props):
            valid = True
            selection_node.adopt(trans)
            if trans.secondary:
                self.root.adopt(trans.secondary)
            for cache, deltas in zip(caches, link_node):
                self.root.propagate(*cache)
                result = cache[0].get(trans.uid, None)
                if not result:
                    valid = False
                    selection_node.disown(trans)
                    if trans.secondary:
                        self.root.disown(trans.secondary)
                    break
                result = sorted(result)
                rights = sorted([delta.right for delta in deltas])
                if result != rights:
                    log.info("Mismatch between inputs and ouptuts:")
                    log.info(result)
                    log.info(rights)
                    valid = False
                    selection_node.disown(trans)
                    if trans.secondary:
                        self.root.disown(trans.secondary)
                    break
            if valid:
                log.info(f"Choosing: {trans}")
                return trans

    def choose_node_old(
        self,
        candidate_nodes: list[Any],
        inputs: ObjectGroup,
        link_node: LinkGroup,
    ) -> TransformNode | None:
        for node in candidate_nodes:
            log.info(node)
        for trans in sorted(candidate_nodes, key=lambda x: x.props):
            valid = True
            for input_group, deltas in zip(inputs, link_node):
                result = trans.apply(input_group)
                if not result:
                    valid = False
                    break
                result = sorted(result)
                rights = sorted([delta.right for delta in deltas])
                if result != rights:
                    log.info("Mismatch between inputs and ouptuts:")
                    log.info(result)
                    log.info(rights)
                    valid = False
                    break
            if valid:
                log.info(f"Choosing: {trans}")
                return trans

    def apply_node(
        self, node: SolutionNode, input: list[Object]
    ) -> list[tuple[ObjectPath, Object | int]] | None:
        results: list[tuple[ObjectPath, Object | int]] = []
        if isinstance(node, VariableNode):
            if (value := node.apply(input)) is not None:
                path = min(node.paths)
                results.append((path, value))
            else:
                return None
        elif isinstance(node, TransformNode):
            if (objs := node.apply(input)) is not None:
                for path, obj in zip(sorted(node.paths), sort_layer(objs)):
                    results.append((path, obj))
            else:
                return None
        else:
            log.warning(f"Unsupported SolutionNode type: {node}")
        return results

    def inventory(self, scene: Scene) -> list[Object]:
        if self.root.level_attention is not None:
            log.info(f"  Using level attention: {self.root.level_attention}")
            input = Inventory(scene.input.rep).depth[self.root.level_attention]
        else:
            log.info(f"  No level attention")
            input = Inventory(scene.input.rep).all
        log.debug(f"  input_group: {input}")
        return input

    def generate2(self, scene: Scene) -> Object:
        """Create the test output."""
        log.info(f"Generating scene: {scene.idx}")
        if self.characteristic:
            log.info(f"  Decomposing with characteristic: {self.characteristic}")
            scene.input.decompose(characteristic=self.characteristic)
        else:
            log.info(f"  Decomposing without characteristic")
            scene.input.decompose()

        self.cache: Cache = ({uuid.uuid4(): [scene.input.rep]}, {})
        self.root.propagate(*self.cache)
        return self.cache[0][self.terminus.uid][0]

    def generate(self, scene: Scene) -> Object:
        """Create the test output."""
        log.info(f"Generating scene: {scene.idx}")
        if self.characteristic:
            log.info(f"  Decomposing with characteristic: {self.characteristic}")
            scene.input.decompose(characteristic=self.characteristic)
        else:
            log.info(f"  Decomposing without characteristic")
            scene.input.decompose()

        input = self.inventory(scene)

        # NOTE: Just depth-1 solution graphs for now
        outputs: list[tuple[ObjectPath, Object | int]] = []
        for node in self.nodes:
            if result := self.apply_node(node, input):
                outputs.extend(result)

        return self.template.create_output(outputs)

    # def root_gen(self, scene: Scene) -> Object:
    #     nodes: list[Node] = [self.root]
    #     object_cache: ObjectCache = {}
    #     var_cache: VarCache = {}
    #     while nodes:
    #         curr = nodes.pop(0)
    #         if isinstance(curr, VarNode):
    #             if (value := curr.apply(object_cache)) is not None:
    #                 var_cache[curr.uid] = value
    #         else:
    #             if (objects := curr.apply(object_cache, var_cache)) is not None:
    #             object_cache[curr.uid] = curr.apply(object_cache, var_cache)

    #     return output
