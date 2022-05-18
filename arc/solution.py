from collections import defaultdict
from typing import Any, TypeAlias

import numpy as np

from arc.actions import Action, pair_actions, degeneracies, subs
from arc.board import Inventory
from arc.comparisons import compare_rotation
from arc.object_relations import compare_structure
from arc.generator import ActionType
from arc.labeler import Labeler, all_traits
from arc.object import Object
from arc.object_delta import ObjectDelta, ObjectTarget
from arc.scene import Scene
from arc.selector import Selector, subdivide_groups
from arc.util import logger
from arc.util import dictutil

log = logger.fancy_logger("Solution", level=30)

ActionArg: TypeAlias = int | Selector | tuple[str, None | dict[int, int]]


class SolutionNode:
    """A single object operation, with Objects and Context as inputs.

    The Solution nodes form a directed graph that convert the input signal
    to the appropriate output. It involves 3 concepts:
      - Description: Labeling all objects present in the inputs or selection.
      - Selection: Assigning objects into groups based on their labels.
      - Transformation: Modify selected objects in ways determined by accessory
          information (contained in the args attribute).
    """

    def __init__(
        self,
        selector: Selector,
        action: ActionType = Action.identity,
        args: tuple[ActionArg, ...] = tuple(),
        target: ObjectTarget = tuple(),
    ) -> None:
        # TODO: For now, only depth-1 Solutions, so assume no children.
        # self.children: list[SolutionNode] = []
        self.selector = selector
        self.action = action
        self.args = args
        self.target = target

    def __repr__(self) -> str:
        return f"Select {self.selector} -> {self.action.__name__}{self.args} -> {self.target}"

    @classmethod
    def from_action(
        cls,
        inputs: list[list[Object]],
        path_node: list[list[ObjectDelta]],
        action: ActionType = Action.identity,
    ) -> list["SolutionNode | None"]:
        selectors: list[Selector] = []

        # Try a single selector first
        selection = [[delta.left for delta in group] for group in path_node]
        path: Any = [path_node]
        selector = Selector(inputs, selection)
        if not selector:
            log.info("Single Selection failed, trying to split")
            # Attempt to divide the path node into groups based on similarity
            path = subdivide_groups(path_node)
            for subnode in path:
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

        nodes: list[SolutionNode | None] = []
        for selector, subnode in zip(selectors, path):

            args: tuple[ActionArg, ...] = ()

            deltas = [delta for group in subnode for delta in group]

            # TODO This is a simple starting implementation for structuring
            # 'Target' should be developed further
            # target represents the location in the output structure for the result
            target = min([delta.target for delta in deltas])

            if action in pair_actions:
                log.debug(f"Determining selector for {action.__name__}")
                secondaries: list[Object] = []
                for delta_group, candidates in zip(subnode, inputs):
                    for delta in delta_group:
                        for obj in candidates:
                            # TODO Figure out a better way for an object to not be
                            # matched up with its children
                            if obj in delta.left.children:
                                continue
                            if action(delta.left, obj) == delta.right:
                                log.debug(f"Choosing secondary: {obj}")
                                secondaries.append(obj)
                                break
                if len(secondaries) < len(path_node):
                    log.info(f"Insufficient secondaries found for {action.__name__}")
                    return [None]
                args = (Selector(inputs, [secondaries]),)
                log.info(f"Pairwise selector for {action.__name__}: {args[0]}")
            elif action == Action.identity:
                # Identity actions won't have args, so skip the next block
                pass
            else:
                # now check the arguments
                transforms = [delta.transform for delta in deltas]
                all_args: set[tuple[int, ...]] = set()
                # TODO HACK This messily handles finding the args that might belong
                # to the desired transform node from a multi-action delta.
                for transform in transforms:
                    matched_args = [
                        d_args
                        for d_act, d_args in zip(transform.actions, transform.args)
                        if d_act == action
                    ]
                    # TODO Add arg count matching
                    if matched_args:
                        all_args.add(matched_args[0])
                    else:
                        all_args.add(transform.args[0])

                if all(all_args) and len(all_args) > 1:
                    # Non-null, non-constant action arguments means we need a mapping
                    labeler = Labeler(selection)
                    arg_mapping = cls.determine_map(deltas, labeler)
                    if not arg_mapping[0]:
                        return [None]
                    args = (arg_mapping,)
                else:
                    args = all_args.pop()

            nodes.append(cls(selector, action, args, target))

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

    def apply(self, input: list[Object]) -> list[Object]:
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
                        args.append(mapping.get(trait_value, trait_value))  # type: ignore
                    case _:
                        log.warning(f"Unhandled action arg: {arg}")

            result.append(self.action(obj, *args))
        return result


class Solution:
    """Contain the information needed to convert an input board to a correct output.

    A solution is a directed graph of transformation nodes that takes a raw input board
    and can create the correct output board. Each solution is presumed to have
    decomposition as the first node/step in the process. The result of decomposition
    is then fed into 1+ nodes organized in 1+ layers.
    """

    def __init__(self) -> None:
        self.characteristic: str = ""
        self.nodes: list[SolutionNode] = []
        self.transform_map: dict[str, list[str]] = defaultdict(list)
        self.structure: dict[str, Any] = {}

    def __repr__(self) -> str:
        msg: list[str] = [f"Decomposition characteristic: {self.characteristic}"]
        for node in self.nodes:
            msg.append(str(node))
        msg.append(str(self.structure))
        return "\n".join(msg)

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle object transforms together from the Scene paths.

        This aims to approximately identify the SolutionNodes we need.
        """
        self.bundled: dict[str, list[ObjectDelta]] = defaultdict(list)
        for case in cases:
            self.bundled = dictutil.merge(self.bundled, case.path)

        # Attempt replacing degenerate transforms to reduce unique transforms used
        # E.g. Rotate 90 and Flipping could be equivalent for some objects
        for group in degeneracies:
            overlap = self.bundled.keys() & group
            # If we have two or more elements from the degeneracy group, try stuff
            if len(overlap) > 1:
                log.debug(f"Attempting to bundle {overlap}")
                results: dict[str, list[ObjectDelta]] = defaultdict(list)
                for target in overlap:
                    deltas = [
                        delta
                        for key in overlap - {target}
                        for delta in self.bundled[key]
                    ]
                    for delta in deltas:
                        # TODO WIP Just try rotational substitution manually
                        new_delta = ObjectDelta(
                            delta.left, delta.right, comparisons=[compare_rotation]
                        )
                        if not new_delta.null:
                            results[target].append(new_delta)
                        else:
                            results[target] = []
                            break
                if results:
                    best = sorted(results.items(), key=lambda x: len(x[1]))[0]
                    log.debug(f"Choosing smallest mapping: {best}")
                    for key in overlap - {best[0]}:
                        self.bundled.pop(key)
                    self.bundled[best[0]].extend(best[1])

        self.transform_map: dict[str, list[str]] = defaultdict(list)
        for key in self.bundled:
            self.transform_map[key] = [key]

        # TODO WIP
        # We check a few rules to know when we should attempt a higher-level transform
        for left, right in subs:
            log.debug(f"Checking subsitution: {left} -> {right}")

            # Case 1: Double transforms ("ws", "fp") -> map to pairwise action
            if left in self.transform_map:
                self.transform_map[right].extend(self.transform_map.pop(left))
            elif set(left) & set(self.transform_map.keys()):
                for char in left:
                    present = any([char in case.path for case in cases])
                    complete = all([char in case.path for case in cases])
                    # Case 2: Non-constant transforms across cases
                    if present and not complete:
                        self.transform_map[right].extend(self.transform_map.pop(char))
                    # Case 3: There's overlap in the subsitution key, but no other compelling
                    # evidence, so we just add the pairwise transforms as actions to attempt
                    # if the original action fails.
                    elif present and complete:
                        self.transform_map[char + right].extend(
                            self.transform_map.pop(char)
                        )

        log.debug(f"Transform mapping: {self.transform_map}")

    def create_structure(self, cases: list[Scene]):
        """Determine any common elements in the output Grids.

        This also provides a basic frame on which to build the test case outputs."""
        objs = [scene.output.rep for scene in cases]
        self.structure = compare_structure(objs)

    def create_nodes(self, cases: list[Scene]) -> None:
        self.nodes = []
        inputs = [Inventory(case.input.rep).all for case in cases]

        for codes, base_chars in self.transform_map.items():
            # The path node is a list of lists of ObjectDeltas related to the transform
            # path_node = [case.path.get(key, []) for case in cases for key in base_chars]
            path_node: list[list[ObjectDelta]] = []
            for case in cases:
                case_node = [
                    delta
                    for key in base_chars
                    for delta in self.bundled.get(key, [])
                    if delta.tag == case.idx
                ]
                path_node.append(case_node)
            # path_node = [self.bundled.get(key, []) for case in cases for key in base_chars]
            path_node = list(filter(None, path_node))

            if len(codes) <= 1:
                action = Action()[codes]
                raw_nodes = SolutionNode.from_action(inputs, path_node, action)
                nodes = filter(None, raw_nodes)
                if nodes:
                    self.nodes.extend(nodes)
            else:
                for char in codes:
                    log.info(f"Attempting Solution node for char '{char}'")
                    action = Action()[char]
                    raw_nodes = SolutionNode.from_action(inputs, path_node, action)
                    nodes = filter(None, raw_nodes)
                    if nodes:
                        self.nodes.extend(nodes)
                        break

    def generate(self, test_scene: Scene) -> Object:
        if self.characteristic:
            test_scene.input.decompose(characteristic=self.characteristic)
        else:
            test_scene.decompose()

        input = Inventory(test_scene.input.rep).all
        log.debug(f"Test case input_group: {input}")

        output: Object = Object.from_structure(**self.structure)
        # NOTE: Just depth-1 solution graphs for now
        for node in sorted(self.nodes, key=lambda x: x.target):
            objects = node.apply(input)
            if not objects:
                continue
            log.debug(f"Appending the following Objects at {node.target}:")
            for obj in objects:
                log.debug(obj)
            # An empty target means there's a single, root object
            if not node.target:
                return objects[0]
            # TODO Move this structure location code to its own functions
            loc = output
            for child_idx in node.target[:-1]:
                try:
                    loc = loc[child_idx]
                except:
                    log.warning(
                        f"Can't access target {node.target[:-1]}, trying last child"
                    )
                    try:
                        loc = loc[-1]
                    except:
                        log.warning(
                            "Failed adding to output. Common structure likely incorrect"
                        )
            loc.children.extend(objects)

        return output
