from arc.board import Inventory
from arc.labeler import Labeler
from arc.object import Object
from arc.scene import Scene
from arc.selector import Selector
from arc.util import logger

log = logger.fancy_logger("Solution", level=30)


class Solution:
    """Contain the information needed to convert an input board to a correct output.

    Starting from a raw input board, this involves the following stages:
      - Decomposition: A deterministic decomposition based on a provided Context (TBD).
      - Description: Labeling all objects resulting from decomposition.
      - Selection: Assigning objects into groups based on their labels.
      - Transformation: Apply transforms to input objects to yield matched outputs.
      - Generation: Create any required new objects based on variables from the inputs.
    """

    def __init__(self) -> None:
        self.selector = None

    def label(self, input_groups: dict[str, list[Object]]):
        for char, group in input_groups.items():
            log.debug(f"Labeling group {char}")
            Labeler(group)

    def create_selector(self, input_groups: dict[str, list[Object]]) -> None:
        self.selector = Selector(input_groups)

    def solve(self, test_scene: Scene) -> Object:
        if not self.selector:
            log.warning("No selector defined yet")
            return Object()
        test_scene.decompose()
        input_group = Inventory(test_scene.input.rep).all
        bundle = self.selector.bundle(input_group)
        # TODO
        return Object()
