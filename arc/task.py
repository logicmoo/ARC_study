from typing import Any
from arc.board import Board
from arc.definitions import Constants as cst
from arc.inventory import Inventory
from arc.object import Object
from arc.scene import Scene
from arc.solution import Solution
from arc.template import Template
from arc.types import TaskData
from arc.util import logger

log = logger.fancy_logger("Task", level=20)


class Task:
    """One 'problem' within the ARC dataset: contains and operates on Scenes.

    Attributes:
        raw: The unprocessed data from the input JSON. Used for resetting state.
        idx: The rank of the Task when sorted alphabetically by filename.
        uid: The stem of the filename (e.g. 'path/to/{uid}.json')
        cases: All 'training' scenes for the task.
        tests: All 'test' scenes for the task.
        solution: The process to transform the input to the output.
        context: Additional information that might come from Task-level study.
        traits: Single-word descriptors of the Task. Used for analytics, grouping.
    """

    def __init__(self, task_data: TaskData, idx: int = 0, uid: str = ""):
        self.raw: TaskData = task_data
        self.idx: int = idx
        self.uid: str = uid
        self.cases: list[Scene] = []
        self.tests: list[Scene] = []

        # Utility
        self.traits: set[str] = set([])

        # Used for solutioning
        self.context: dict[str, Any] = {}
        self.solution: Solution = Solution()

        # Load scenes, cases ("train" data) and tests
        for scene_idx, scene_data in enumerate(task_data["train"]):
            self.cases.append(Scene(idx=scene_idx, data=scene_data))

        for scene_idx, scene_data in enumerate(task_data["test"]):
            self.tests.append(Scene(idx=scene_idx, data=scene_data))

    def __getitem__(self, arg: int | str) -> Scene:
        match arg:  # pragma: no cover
            case int(idx):
                return self.cases[idx]
            case str(test_code):
                try:
                    return self.tests[int(test_code[1:])]
                except KeyError:
                    log.error(f"Unable to index a Task using '{test_code}'")
                    raise

    @property
    def n_boards(self) -> int:
        """Number of total boards in the Task."""
        return 2 * (len(self.cases) + len(self.tests))

    def info(self) -> None:
        """Display a set of key info about the task to the user."""
        log.info(f"Task {self.idx} UID = {self.uid} | First input board:")
        log.info(self.raw["train"][0]["input"], extra={"fmt": "bare"})

    def clean(self, decomp_tree_only: bool = False) -> None:
        for scene in self.cases + self.tests:
            scene.clean(decomp_tree_only=decomp_tree_only)

    def solve(self) -> None:
        """Execute every step of the solution pipeline for the Task."""
        self.decompose()

        outputs = [case.output for case in self.cases]
        output_stats = self.rank_characteristics(outputs)
        # Loop over the best characteristics in the output
        # TODO Find a way to use the information in the Template to
        # help determine likely solutions before attempting
        for _, char in output_stats[:3]:
            self.align_representation(outputs, char)
            self.determine_template(char)
            self.match()
            self.solution = Solution(**self.context)
            self.solution.bundle(self.cases)
            if self.solution.create_nodes(self.cases):
                break
        self.test()

    def determine_template(self, char: str):
        """Determine any common elements in the output Grids.

        This also provides a basic frame on which to build the test case outputs."""
        outputs = [case.output for case in self.cases]

        # Search the most efficient decomp characteristics for the most stable Template
        # for _, char in output_stats:
        #     best: int = outputs[0].rep.props  # Set an arbitrary high goal that can't be met
        objs = [board.rep for board in outputs]
        self.context["template"] = Template.from_outputs(objs)

        # if candidate and candidate.props < best:
        #     best = candidate.props
        #     self.solution.template = candidate
        log.info(f"Template: {self.context['template']}")

    def decompose(
        self,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        init: bool = False,
    ) -> None:
        """Apply decomposition across all cases, learning context and iterating."""
        log.info(" + Decomposition")
        inputs = [case.input for case in self.cases]
        outputs = [case.output for case in self.cases]

        for idx, board in enumerate(inputs):
            board.decompose(max_iter=max_iter, init=init)
            log.info(f"Scene {idx} input rep | props {board.rep.props}:")
            log.info(board.rep)

        # Choose the best-performing input characteristic
        # This helps the output decomposition by providing a more uniform
        # Inventory across the cases
        input_stats = self.rank_characteristics(inputs)
        if input_stats:
            self.context["characteristic"] = input_stats[0][1]
            self.align_representation(inputs, input_stats[0][1])

        for idx, (inp, out) in enumerate(zip(inputs, outputs)):
            inventory = Inventory(inp.rep)
            out.decompose(max_iter=max_iter, inventory=inventory, init=init)
            log.info(f"Scene {idx} input rep | props {out.rep.props}:")
            log.info(out.rep)

    def rank_characteristics(self, boards: list[Board]) -> list[tuple[int, str]]:
        char_stats: list[tuple[int, str]] = []

        common_chars: set[str] = set(boards[0].characteristic_map.keys())
        for board in boards[1:]:
            common_chars &= board.characteristic_map.keys()

        for char in common_chars:
            score = 0
            for board in boards:
                score += board.tree[board.characteristic_map[char]].props
            char_stats.append((score, char))

        return sorted(char_stats)

    def align_representation(self, boards: list[Board], char: str) -> None:
        """Match the characteristics of the decompositions across scenes."""
        # Set the new representation
        log.info(f" === Choosing representation characteristic: {char}")
        for board in boards:
            key = board.characteristic_map[char]
            board.current = key

    def match(self) -> None:
        """Match input and output objects for each case."""
        log.info(f" + Matching")
        for scene in self.cases:
            scene.match()
        scene_dists = [scene.dist for scene in self.cases]
        depths = {scene.depth for scene in self.cases}
        depth = None
        if len(depths) == 1:
            depth = depths.pop()
            self.context["attention"] = depth
        log.info(f"Scene depth: {depth}, distances {scene_dists}")

    def generate(self, test_idx: int = 0) -> Object:
        return self.solution.generate(self.tests[test_idx])

    def test(self) -> bool:
        success = 0
        log.info("Testing:")
        for test_idx, scene in enumerate(self.tests):
            if scene.output.rep == self.generate(test_idx):
                success += 1
            else:
                log.warning(f"  Failed test {test_idx}")
        log.info(f"Passed {success} / {len(self.tests)} tests")
        if success == len(self.tests):
            self.traits.add("Solved")
            return True
        else:
            return False
