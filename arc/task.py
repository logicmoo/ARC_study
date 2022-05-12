from arc.board import Board
from arc.contexts import TaskContext
from arc.definitions import Constants as cst
from arc.inventory import Inventory
from arc.object import Object
from arc.scene import Scene
from arc.solution import Solution
from arc.types import TaskData
from arc.util import logger
from arc.util import strutil

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

        self.solution: Solution = Solution()
        self.traits: set[str] = set([])

        # WIP
        self.context = TaskContext()

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
    def ppp(self) -> float:
        """Average properties-per-point across cases."""
        return sum([scene.ppp for scene in self.cases]) / len(self.cases)

    @property
    def dist(self) -> float:
        """Average transformational distance across cases."""
        return sum([scene.dist for scene in self.cases]) / len(self.cases)

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
        self.match()
        self.infer()
        self.test()

    def decompose(
        self,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        init: bool = False,
    ) -> None:
        """Apply decomposition across all cases, learning context and iterating."""
        inputs = [case.input for case in self.cases]
        outputs = [case.output for case in self.cases]

        # TODO apply context
        for idx, board in enumerate(inputs):
            board.decompose(max_iter=max_iter, init=init)
            log.info(f"Scene {idx} input rep | props {board.rep.props}:")
            log.info(board.rep)

        self.align_representation(inputs)

        for idx, (inp, out) in enumerate(zip(inputs, outputs)):
            inventory = Inventory(inp.rep)
            out.decompose(max_iter=max_iter, inventory=inventory, init=init)
            log.info(f"Scene {idx} input rep | props {out.rep.props}:")
            log.info(out.rep)

        self.align_representation(outputs)

    def align_representation(self, boards: list[Board]) -> None:
        """Match the characteristics of the decompositions across scenes."""
        # Identify candidate characteristics
        candidates: list[str] = [
            strutil.get_characteristic(board.current) for board in boards
        ]
        log.info(f"Candidate characteristics: {candidates}")

        # Choose the characteristic giving the minimal representation
        best_props: int = 4 * 900 * len(boards)
        best_rep: list[str] = [board.current for board in boards]
        log.info(f"Current rep {best_rep}")
        for characteristic in candidates:
            new_rep: list[str] = []
            new_props = 0
            for board in boards:
                # Find the minimal representation matching the candidate characteristic
                best_score = 4 * 900
                best_scene_rep = ""
                for key, object in board.tree.items():
                    if (
                        strutil.get_characteristic(key) == characteristic
                        and object.props < best_score
                    ):
                        best_scene_rep = key
                        best_score = object.props
                new_rep.append(best_scene_rep)
                new_props += best_score
            if new_props < best_props:
                best_props = new_props
                best_rep = new_rep

        # Set the new representation
        log.info(f"Choosing rep {best_rep}")
        for rep, board in zip(best_rep, boards):
            board.current = rep

    def match(self) -> None:
        """Match input and output objects for each case."""
        log.info(f" + Matching")
        for scene in self.cases:
            scene.match()
        scene_dists = [scene.dist for scene in self.cases]
        log.info(f"Scene distances {scene_dists} -> avg {self.dist:.1f}")

    def infer(self):
        self.solution.bundle(self.cases)
        self.solution.create_structure(self.cases)
        self.solution.create_nodes(self.cases)

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
