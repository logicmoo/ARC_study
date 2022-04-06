from arc.contexts import TaskContext
from arc.definitions import Constants as cst
from arc.object import Object
from arc.scene import Scene
from arc.solution import Solution
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

    def info(self) -> None:
        """Display a set of key info about the task to the user."""
        log.info(f"Task {self.idx} UID = {self.uid} | First input board:")
        log.info(self.raw["train"][0]["input"], extra={"fmt": "bare"})

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

    def solve(self) -> None:
        """Execute every step of the solution pipeline for the Task."""
        self.decompose()
        self.match()
        self.infer()
        self.test()

    def decompose(
        self, batch: int = cst.BATCH, max_iter: int = cst.MAX_ITER, init: bool = False
    ) -> None:
        """Apply decomposition across all cases, learning context and iterating."""
        # TODO apply context
        log.info(f" + Decomposition")
        for scene in self.cases:
            scene.decompose(batch=batch, max_iter=max_iter, init=init)
        scene_ppps = [round(scene.ppp, 2) for scene in self.cases]
        log.info(f"Scene PpPs {scene_ppps} -> avg {self.ppp:.3f}")

    def match(self) -> None:
        """Match input and output objects for each case."""
        log.info(f" + Matching")
        for scene in self.cases:
            scene.match()
        scene_dists = [scene.dist for scene in self.cases]
        log.info(f"Scene distances {scene_dists} -> avg {self.dist:.1f}")

    def infer(self):
        self.solution.bundle(self.cases)
        self.solution.label(self.cases)
        self.solution.create_selector(self.solution.input_groups)
        self.solution.determine_maps()

    def generate(self, test_idx: int = 0) -> Object:
        return self.solution.generate(self.tests[test_idx])

    def test(self):
        success = 0
        log.info("Testing:")
        for test_idx, scene in enumerate(self.tests):
            if scene.output.rep == self.generate(test_idx):
                success += 1
            else:
                log.warning(f"  Failed test {test_idx}")
        if success == len(self.tests):
            self.traits.add("Solved")
        log.info(f"Passed {success} / {len(self.tests)} tests")
