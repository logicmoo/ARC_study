from collections import defaultdict
from typing import TypeAlias
from arc.actions import Action, subs
from arc.board import Inventory
from arc.generator import ActionType
from arc.labeler import Labeler, all_traits
from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.scene import Scene
from arc.selector import Selector
from arc.util import logger, dictutil

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
        input: list[Object],
        output: list[Object],
        selection: list[Object],
        action: ActionType = Action.identity,
        args: tuple[ActionArg, ...] = tuple(),
    ) -> None:
        # TODO: For now, just consider one generator of SolutionNodes.
        # Thus, assume no children.
        # self.children: list[SolutionNode] = []
        self.selector = Selector(input, selection)
        self.action = action
        self.args = args

        # TODO Include a means to process missing transform args
        self.output = output

    @classmethod
    def from_transform_group(
        cls, input: list[Object], group: list[ObjectDelta]
    ) -> "SolutionNode":
        selection = [delta.left for delta in group]
        output = [delta.right for delta in group]
        action: ActionType = Action.identity
        args: tuple[ActionArg, ...] = ()

        transforms = [delta.transform for delta in group]
        actions: set[ActionType] = set(
            [action for delta in group for action in delta.transform.actions]
        )
        if len(actions) == 0:
            pass
        elif len(actions) > 1:
            log.debug(f"Multiple actions for transform group: {actions}")
            # TODO Handle action substitution
        else:
            # A single, common action is present in the transforms
            action = actions.pop()
            # now check the arguments
            all_args = set([transform.args[0] for transform in transforms])
            if len(all_args) > 1:
                # Non-constant action arguments means we should look for a mapping
                args = (cls.determine_map(group),)
            else:
                # The args are a constant value
                args = all_args.pop()

        return cls(input, output, selection, action, args)

    @staticmethod
    def determine_map(delta_list: list[ObjectDelta]) -> tuple[str, dict[int, int]]:
        result: tuple[str, dict[int, int]] = ("", {})
        for trait in all_traits:
            trial_map: dict[int, int] = {}
            for delta in delta_list:
                inp = delta.left.traits[trait]
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
        Labeler(selection)
        for obj in selection:
            args: list[Object | int] = []
            for arg in self.args:
                match arg:
                    case int(value):
                        args.append(value)
                    case Selector():
                        continue
                    case (str(trait), None):
                        log.debug(f"Transforming using {self.action}({trait})")
                        trait_value = obj.traits.get(trait)
                        args.append(trait_value)  # type: ignore
                    case (str(trait), {**mapping}):
                        log.debug(
                            f"Transforming using {self.action}({trait} mapping {mapping})"
                        )
                        trait_value = obj.traits.get(trait)
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
        self.inputs: list[Object] = []
        self.transform_groups: dict[str, list[ObjectDelta]] = {}
        self.nodes: list[SolutionNode] = []

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle objects together in order to identify a proper Selector."""
        for scene in cases:
            self.inputs.extend(scene.input.inventory.all)
            dictutil.merge(self.transform_groups, scene.path)
        log.debug(self.transform_groups)

        # TODO WIP
        # For now, use a substitution if it reduces the size of the transform group dict
        new_tg: dict[str, list[ObjectDelta]] = defaultdict(list)
        for char, group in self.transform_groups.items():
            key = char
            for left, right in subs:
                log.debug(f"Checking subsitution: {left} -> {right}")
                # Check if any transforms are in both the substitution input and group
                if set(left) & set(char):
                    log.debug(f"  Overlap: {left}, {char}")
                    key = right
            new_tg[key].extend(group)
        log.debug(f"New TG: {new_tg.keys()}")
        if len(dictutil.key_concat(new_tg)) < len(
            dictutil.key_concat(self.transform_groups)
        ):
            log.debug(
                f"Replacing TG {self.transform_groups.keys()} with {new_tg.keys()}"
            )
            self.transform_groups = new_tg

    def create_nodes(self) -> None:
        self.nodes = []
        for group in self.transform_groups.values():
            self.nodes.append(SolutionNode.from_transform_group(self.inputs, group))

    def label(self, cases: list[Scene]):
        for scene in cases:
            for char, group in scene.path.items():
                log.debug(f"Labeling scene: {scene.idx} group: {char}")
                Labeler([delta.left for delta in group])

    def generate(self, test_scene: Scene) -> Object:
        test_scene.decompose()
        input = Inventory(test_scene.input.rep).all
        log.debug(f"Test case input_group: {input}")

        output_children: list[Object] = []
        # NOTE: Just depth-1 solution graphs for now
        for node in self.nodes:
            output_children.extend(node.apply(input))

        return Object(children=output_children)
