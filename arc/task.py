import collections
from copy import deepcopy

from arc.board import Board
from arc.definitions import Constants as cst
from arc.inventory import Inventory
from arc.object import Object
from arc.scene import Scene
from arc.solution import Solution, TransformNode, VariableNode
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
        traits: Single-word descriptors of the Task. Used for analytics, grouping.
    """

    def __init__(self, task_data: TaskData, idx: int = 0, uid: str = ""):
        self.raw: TaskData = task_data
        self.idx: int = idx
        self.uid: str = uid
        self.cases: list[Scene] = []
        self.tests: list[Scene] = []

        # A solve run will create a Solution instance
        self.solution: Solution = Solution()

        # Utility
        self.traits: set[str] = set([])
        self.template_map: dict[str, Template] = {}
        self.validation_map: dict[str, list[Object]] = collections.defaultdict(list)
        self.fail: str = ""

        # Load scenes, cases ("train" data) and tests
        for scene_idx, scene_data in enumerate(task_data["train"]):
            self.cases.append(Scene(idx=scene_idx, data=scene_data))

        for scene_idx, scene_data in enumerate(task_data["test"]):
            self.tests.append(Scene(idx=scene_idx, data=scene_data))

    def __getitem__(self, arg: int | str) -> Scene:
        """Retrieve a Scene by index.  (Convenience method)"""
        match arg:  # pragma: no cover
            case int(idx):
                return self.cases[idx]
            case str(test_code):
                # Use 'T1' to access a test (or any leading char...)
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
        """Remove extra material used during solutioning.

        Once a Solution is created, this method can be called to remove items like
        the unused nodes of the decomposition tree, freeing memory. This can help
        ensure a full run on ARC doesn't hit system memory constraints.
        """
        for scene in self.cases + self.tests:
            scene.clean(decomp_tree_only=decomp_tree_only)

    def run(self) -> None:
        """Execute every step of the solution pipeline for the Task."""
        if (input_char := self.decompose()) is None:
            log.warning("Solution failed during decomposition.")
            self.fail = "Decomposition"
            return

        if (output_char := self.link()) is None:
            log.warning("No valid template and matches found.")
            self.fail = "Link"
            return

        if (solution := self.solve(input_char, output_char)) is None:
            log.warning("No solution found passing validation.")
            self.fail = "Solution"
            return

        self.solution = solution
        self.test()

    def decompose(
        self,
        max_iter: int = cst.DEFAULT_MAX_ITER,
        init: bool = False,
    ) -> str | None:
        """Apply decomposition across all cases, learning context and iterating."""
        log.info(" --- Decomposition")
        inputs = [case.input for case in self.cases]
        outputs = [case.output for case in self.cases]

        for idx, input in enumerate(inputs):
            input.decompose(max_iter=max_iter, init=init)
            log.info(f"Scene {idx} input rep | props {input.rep.props}: {input.rep}")
            input.rep.debug()

        # Choose the best-performing input characteristic
        # This helps the output decomposition by providing a more uniform
        # Inventory across the cases
        best: str | None = None
        if input_stats := self.rank_characteristics(inputs):
            best = input_stats[0][1]
            self.align_boards(inputs, best)

        for idx, (input, output) in enumerate(zip(inputs, outputs)):
            inventory = Inventory(input.rep)
            output.decompose(max_iter=max_iter, inventory=inventory, init=init)
            log.info(f"Scene {idx} output rep | props {output.rep.props}: {output.rep}")
            output.rep.debug()

        return best

    def rank_characteristics(self, boards: list[Board]) -> list[tuple[int, str]]:
        """Sort the characteristics used in representations by total properties."""
        char_stats: list[tuple[int, str]] = []

        common_chars: set[str] = set(boards[0].characteristic_map.keys())
        for board in boards[1:]:
            common_chars &= board.characteristic_map.keys()

        for char in common_chars:
            score = sum(
                board.tree[board.characteristic_map[char]].props for board in boards
            )
            char_stats.append((score, char))

        return sorted(char_stats)

    def align_boards(self, boards: list[Board], char: str) -> None:
        """Match the characteristics of the decompositions across scenes."""
        # Set the new representation
        log.info(f" * Aligning representation on characteristic: {char}")
        for board in boards:
            key = board.characteristic_map[char]
            board.current = key

    def link(self) -> str | None:
        """Link input and output objects for each case.

        This identifies likely connections between the input and output boards.
        """
        log.info(f" --- Linking")
        outputs = [case.output for case in self.cases]
        top_chars = self.rank_characteristics(outputs)[: cst.TOP_K_CHARS]
        log.info(f"Top characteristics: {top_chars}")

        best: str | None = None
        best_score: float = cst.MAX_DIST
        best_rep = top_chars[0][0]
        for rep_score, char in top_chars:
            self.align_boards(outputs, char)
            template = self.determine_template(char)
            self.template_map[char] = template
            for scene in self.cases:
                scene.link(char, template.variables)

            if not self.validate_links(template, char):
                continue

            scene_dists = [scene.dist for scene in self.cases if scene.dist is not None]
            depths = {scene.depth for scene in self.cases}
            depth = None
            if len(depths) == 1:
                depth = depths.pop()
            log.info(f"Scene depth: {depth}, distances {scene_dists}")

            # TODO WIP Find a reasonable tradeoff between the different metrics
            # regarding the input to output match:
            #  representation compactness, match distance, template variables
            score = (rep_score / best_rep) + sum(scene_dists)
            if score < best_score:
                best_score = score
                best = char
                log.info(
                    f" > Output characteristic: {best} at distance {best_score:.2f}"
                )

        return best

    def determine_template(self, char: str) -> Template:
        """Determine any common elements in the output Grids.

        This also provides a basic frame on which to build the test case outputs."""
        output_reps = [case.output.rep for case in self.cases]
        template = Template.from_outputs(output_reps)
        log.debug(f"Template: {template}")
        return template

    def validate_links(self, template: Template, char: str) -> bool:
        """Check if a template can generate the cases."""
        for case_idx, scene in enumerate(self.cases):
            if (
                val_rep := template.validate_link_map(scene.link_maps[char])
            ) != scene.output.rep:
                log.info(f" x Scene {case_idx} failed validation under {char}")
                self.validation_map[char].append(val_rep)
                return False
        return True

    def solve(self, input_char: str, output_char: str) -> Solution:
        solution = self.init_solution(input_char, output_char)
        solution.bundle(self.cases)
        solution.create_nodes(self.cases)
        self.validate_nodes(solution)

        log.info(f" + Candidate Solution:\n{solution}", extra={"max_lines": 50})
        return solution

    def init_solution(self, input_char: str, output_char: str) -> Solution:
        """Initialize a Solution instance from the characteristic info."""
        template = self.template_map[output_char]
        log.debug(f"Template chosen: {template}")
        for scene in self.cases:
            scene.current = output_char

        outputs = [case.output for case in self.cases]
        self.align_boards(outputs, output_char)

        # Determine attention from depth
        depth: int | None = None
        depths = {scene.depth for scene in self.cases}
        if len(depths) == 1:
            depth = depths.pop()

        return Solution(
            characteristic=input_char,
            attention=depth,
            template=template,
        )

    def validate_nodes(self, solution: Solution) -> None:
        """Check if the solution nodes yield matching results for cases."""

        to_remove: set[int] = set([])
        log.info("Validating nodes against test scene inputs")
        # First, test if nodes function on test inputs.
        for test_scene in self.tests:
            # TODO Re-engineer timing of test decomposition
            test_scene.input.decompose(characteristic=solution.characteristic)
            input = solution.inventory(test_scene)
            for idx, node in enumerate(solution.nodes):
                if solution.apply_node(node, input) is None:
                    log.info(f"Removing invalid node {node}")
                    to_remove.add(idx)

        for idx in sorted(to_remove, reverse=True):
            solution.nodes.pop(idx)

        log.info("Validating nodes against case outputs")
        template = solution.template
        flags: list[list[bool]] = [[True] * len(self.cases)] * len(solution.nodes)
        for case_idx, scene in enumerate(self.cases):
            log.info(f"Validating scene {case_idx}")
            input = solution.inventory(scene)
            frame = deepcopy(template.structure)
            for idx, node in enumerate(solution.nodes):
                if isinstance(node, TransformNode):
                    flags[idx] = [False]
                    if (generated := solution.apply_node(node, input)) is not None:
                        for path, item in generated:
                            if isinstance(item, int):
                                continue
                            frame = template.apply_object(frame, path, item)

            # If the solution is purely transformational, we are done
            if template.generate(frame) == scene.output.rep:
                continue

            for idx, node in enumerate(solution.nodes):
                if isinstance(node, VariableNode):
                    path = list(node.paths)[0]
                    frame_val = Template.get_value(path, frame)
                    scene_val = scene.output.rep.get_value(path)
                    variable_val = node.apply(input)
                    log.debug(
                        f"{path} in Scene: {scene_val}, Frame: {frame_val}, Var: {variable_val}"
                    )
                    if frame_val == scene_val:
                        pass
                    elif variable_val == scene_val:
                        log.info(f"  Variable Needed {node}")
                        flags[idx][case_idx] = False
                    else:
                        log.info(f"  Unchecked val: {path}")

        to_remove: set[int] = set([])
        for idx, truth in enumerate(flags):
            if all(truth):
                to_remove.add(idx)
                log.info(f"Unneeded SolutionNode: {solution.nodes[idx]}")

        for idx in sorted(to_remove, reverse=True):
            solution.nodes.pop(idx)

    def test(self) -> bool:
        """Test all test cases for correctness."""
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

    def generate(self, test_idx: int = 0) -> Object:
        """Generate a test output by index, using the current Solution."""
        return self.solution.generate2(self.tests[test_idx])
        # return self.solution.generate(self.tests[test_idx])
