from collections import defaultdict
from typing import TypeAlias
from arc.actions import Action, pair_actions, subs
from arc.board import Inventory
from arc.generator import ActionType
from arc.labeler import Labeler, all_traits
from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.scene import Scene
from arc.selector import Selector
from arc.util import logger

log = logger.fancy_logger("Solution", level=20)

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
    ) -> None:
        # TODO: For now, just consider one generation of SolutionNodes.
        # Thus, assume no children.
        # self.children: list[SolutionNode] = []
        self.selector = selector
        self.action = action
        self.args = args

    def __repr__(self) -> str:
        return f"{self.selector} -> {self.action.__name__}({self.args})"

    @classmethod
    def from_path_node(
        cls, cases: list[Scene], keys: list[str], action: ActionType
    ) -> list["SolutionNode"]:
        inputs = [Inventory(case.input.rep).all for case in cases]

        # The path node is a list of lists of ObjectDeltas related to the transform
        path_node = [case.path.get(key, []) for case in cases for key in keys]

        # The selection is every object that will be transformed
        selection = [[delta.left for delta in group] for group in path_node]
        deltas = [delta for group in path_node for delta in group]
        selector = Selector(inputs, selection)

        args: tuple[ActionArg, ...] = ()

        if action == Action.identity:
            # TODO Expand upon group subdivision. For now, identity is the most likely
            # transform to be affected by it.
            if not selector.criteria:
                # TODO Hack, divide by color for now
                colors: dict[int, list[list[Object]]] = defaultdict(list)
                for case in selection:
                    color_case: dict[int, list[Object]] = defaultdict(list)
                    for obj in case:
                        color_case[obj.color].append(obj)
                    for color, obj_list in color_case.items():
                        colors[color].append(obj_list)

                nodes: list[SolutionNode] = []
                for color, color_groups in colors.items():
                    selector = Selector(inputs, color_groups)
                    nodes.append(cls(selector, action, args))
                return nodes
        elif action in pair_actions:
            log.debug(f"Determining selector for {action}")
            secondaries: list[Object] = []
            for delta, candidates in zip(deltas, inputs):
                for obj in candidates:
                    if action(delta.left, obj) == delta.right:
                        log.debug(f"Choosing secondary: {obj}")
                        secondaries.append(obj)
                        break
            if len(secondaries) < len(deltas):
                log.warning(f"Insufficient secondaries: {len(secondaries)}")
            args = (Selector(inputs, [secondaries]),)
            log.info(f"Pairwise selector for {action.__name__}: {args[0]}")
        else:
            # now check the arguments
            transforms = [delta.transform for delta in deltas]
            all_args = set([transform.args[0] for transform in transforms])
            if len(all_args) > 1:
                # Non-constant action arguments means we should look for a mapping
                labeler = Labeler(selection)
                args = (cls.determine_map(deltas, labeler),)
            else:
                args = all_args.pop()

        return [cls(selector, action, args)]

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
                    case Selector():
                        args.append(arg.select(input)[0])
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
        self.nodes: list[SolutionNode] = []

    def __repr__(self) -> str:
        msg: list[str] = []
        for node in self.nodes:
            msg.append(str(node))
        return "\n".join(msg)

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle object transforms together.

        In many cases, a Solution will involve nodes with unique transforms. E.g.
        there will be only one node that performs a recoloring. This is sufficient
        to handle most tasks. One must still consider whether the transform identified
        during Matching is the best choice, or should it be replaced by a higher-order
        transform."""
        self.transform_map: dict[str, list[str]] = defaultdict(list)
        for case in cases:
            self.transform_map.update({key: [key] for key in case.path})

        # TODO WIP
        # For now, use a substitution if it reduces the size of transforms
        for left, right in subs:
            log.debug(f"Checking subsitution: {left} -> {right}")
            # Check for double transforms ("ws", "fp") and map to pairwise action
            if left in self.transform_map:
                self.transform_map[right].extend(self.transform_map.pop(left))
            # Check for non-constant transforms among "wsfp" and map to pairwise action
            elif set(left) & set(self.transform_map.keys()):
                for char in left:
                    present = any([char in case.path for case in cases])
                    complete = all([char in case.path for case in cases])
                    if present and not complete:
                        self.transform_map[right].extend(self.transform_map.pop(char))

        log.debug(f"Transform mapping: {self.transform_map}")

    def create_nodes(self, cases: list[Scene]) -> None:
        self.nodes = []
        for node in self.transform_map:
            action = Action()[node]
            self.nodes.extend(
                SolutionNode.from_path_node(cases, self.transform_map[node], action)
            )

    def generate(self, test_scene: Scene) -> Object:
        test_scene.decompose()
        input = Inventory(test_scene.input.rep).all
        log.debug(f"Test case input_group: {input}")

        output_children: list[Object] = []
        # NOTE: Just depth-1 solution graphs for now
        for node in self.nodes:
            output_children.extend(node.apply(input))

        # TODO HACK To handle layering of transformed objects, sort by size for now
        # This should ideally be some information passed through via the Inventory
        # And noted by the SolutionNodes
        output_children = sorted(output_children, key=lambda x: x.size, reverse=True)
        return Object(children=output_children)
