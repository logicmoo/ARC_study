from arc.actions import Action
from arc.board import Inventory
from arc.labeler import Labeler, all_traits
from arc.object import Object
from arc.object_delta import ObjectDelta
from arc.scene import Scene
from arc.selector import Selector
from arc.util import logger, dictutil

log = logger.fancy_logger("Solution", level=30)


class Solution:
    """Contain the information needed to convert an input board to a correct output.

    Starting from a raw input board, this involves the following stages:
      - Decomposition: A deterministic decomposition based on a provided Context (TBD).
      - Description: Labeling all objects resulting from decomposition.
      - Selection: Assigning objects into groups based on their labels.
      - Transformation: Apply transforms to input objects based on learned mappings.
      - Generation: Create any required new objects based on variables from the inputs.
    """

    def __init__(self) -> None:
        self.input_groups: dict[str, list[Object]] = {}
        self.transform_groups: dict[str, list[ObjectDelta]] = {}
        self.selector = None
        self.maps: dict[str, dict[int, int]] = {}
        self.traits: dict[str, str] = {}

    def bundle(self, cases: list[Scene]) -> None:
        """Bundle objects together in order to identify a proper Selector."""
        for scene in cases:
            dictutil.merge(self.transform_groups, scene.path)
            scene_inputs = {
                char: [delta.left for delta in group]
                for char, group in scene.path.items()
            }
            dictutil.merge(self.input_groups, scene_inputs)
        log.debug(self.input_groups)

    def label(self, cases: list[Scene]):
        for scene in cases:
            for char, group in scene.path.items():
                log.debug(f"Labeling scene: {scene.idx} group: {char}")
                Labeler([delta.left for delta in group])

    def create_selector(self, input_groups: dict[str, list[Object]]) -> None:

        # TODO CHECKPOINT
        # input_group = Inventory(test_scene.input.rep).all
        self.selector = Selector(input_groups)

    def determine_maps(self) -> None:
        for trans, delta_list in self.transform_groups.items():
            # TODO Determine number of args for the transform
            if trans in ["", "z"]:
                continue
            for trait in all_traits:
                trial_map = {}
                for delta in delta_list:
                    inp = delta.left.traits[trait]
                    # TODO We're assuming a single action with a single arg for now
                    out = delta.transform.args[0][0]
                    if inp in trial_map:
                        if trial_map[inp] != out:
                            log.debug(
                                f"Trait {trait} fails at {inp} -> {out} | {trial_map}"
                            )
                            trial_map = {}
                            break
                        else:
                            continue
                    trial_map[inp] = out

                if trial_map:
                    log.debug(f"Trait {trait}: {trial_map}")
                    if trans not in self.maps or len(trial_map) < len(self.maps[trans]):
                        self.maps[trans] = trial_map
                        self.traits[trans] = trait

    def generate(self, test_scene: Scene) -> Object:
        if not self.selector:
            log.warning("No selector defined yet")
            return Object()
        test_scene.decompose()
        input_group = Inventory(test_scene.input.rep).all
        log.debug(f"Test case input_group: {input_group}")
        bundle = self.selector.bundle(input_group)
        log.debug("Test case bundle:")
        log.debug(bundle)

        output_children: list[Object] = []
        for char, group in bundle.items():
            log.debug(f"labeling test case bundle group '{char}'")
            Labeler(group)

            for obj in group:
                if char in self.traits:
                    trait = self.traits[char]
                    args = [self.maps[char][obj.traits.get(trait)]]  # type: ignore
                    log.debug(f"Transforming objects with {trait} via '{char}'({args})")
                    output_children.append(Action()[char](obj, *args))
                elif char == "":
                    log.debug(f"Reusing object: {obj}")
                    output_children.append(obj.spawn())
                else:
                    log.debug(f"Transforming obj: {obj} via '{char}'")
                    output_children.append(Action()[char](obj))

        return Object(children=output_children)
