import glob
import json
import logging
import pickle
import time
import traceback
from pathlib import Path
from typing import Any, TypeAlias
from collections import Counter

from arc.definitions import Constants as cst
from arc.task import Task
from arc.task_analysis import TaskTraits, all_solved, all_eval_solved, blocklist
from arc.util import logger
from arc.util import profile
from arc.util.common import process_exception

log = logger.fancy_logger("ARC", level=20)

Index: TypeAlias = int | str | tuple[int, int] | tuple[int, int, str]
Traceback: TypeAlias = list[traceback.FrameSummary]
ErrorReport: TypeAlias = tuple[str, str, Traceback]


class ARC:
    """Load and operate on a collection of Tasks.

    This is the generic starting point for interacting with the ARC dataset and
    the solution process contained in this codebase. It handles loading the data
    and offering high-level control methods.

    Tasks are given an integer index (1+) based on the sorted input filenames.

    Attributes:
        N: The number of loaded tasks in the instance. If passed as an argument,
           ARC will load the first N indices, [1-N].
        idxs: The task indices to load. If passed as argument, overrides 'N'.
        selection: The Task indices to consider for operations. Defaults to 'idxs',
           and can be focused further through calls to select()
        tasks: The mapping of Task index to Task objects.
    """

    def __init__(
        self,
        N: int = cst.N_TRAIN,
        idxs: set[int] | None = None,
        folder: str = cst.FOLDER_TRAIN,
        quiet: bool = False,
    ):
        if not idxs:
            idxs = set(range(1, N + 1))
        self.N: int = len(idxs)
        self.selection: set[int] = idxs
        self.tasks: dict[int, Task] = {}
        self.load_tasks(idxs=idxs, folder=folder, quiet=quiet)

        self.default_log_levels: dict[str, int] = self.get_log_levels()
        self.blocklist: set[int] = blocklist
        self.stats: dict[str, int] = Counter()

        # Utility
        self.eval: bool = folder == cst.FOLDER_EVAL

    @staticmethod
    def load(pid: str | int) -> "ARC":
        """Create an ARC instance from a pickled checkpoint."""
        with open(f"{pid}.pkl", "rb") as fh:
            return pickle.load(fh)

    def dump(self, pid: str | int) -> None:
        """Pickle the current state of the ARC instance."""
        with open(f"{pid}.pkl", "wb") as fh:
            pickle.dump(self, fh)

    def __getitem__(self, index: Index) -> Any:
        """Convenience method so the user has easy access to ARC elements."""
        match index:  # pragma: no cover
            case int(task_idx):
                return self.tasks[task_idx]
            case (task_idx, scene_idx):
                return self.tasks[task_idx][scene_idx]
            case (task_idx, scene_idx, attribute):
                return getattr(self.tasks[task_idx][scene_idx], attribute)
            case str(partial_uid):
                for task in self.tasks.values():
                    if partial_uid in task.uid:
                        return task
                log.warning(f"Couldn't find a task with uid matching {partial_uid}")
                return None

    def load_tasks(
        self, idxs: set[int] = set(), folder: str = ".", quiet: bool = False
    ) -> None:
        """Load indicated task(s) from the ARC dataset."""
        curr_idx, boards, tests = 1, 0, 0
        for filename in sorted(glob.glob(f"{folder}/*.json")):
            if curr_idx in idxs:
                with open(filename, "r") as fh:
                    task = Task(json.load(fh), idx=curr_idx, uid=Path(filename).stem)
                    self.tasks[curr_idx] = task
                    boards += task.n_boards
                    tests += len(task.tests)
            curr_idx += 1
        if not quiet:
            log.info(
                f"Loaded {len(self.tasks)} Tasks, with {boards} boards and {tests} tests."
            )

    def get_log_levels(self) -> dict[str, int]:
        """Get all of the defined loggers and their current level.

        This is used to easily re-initialize during debugging.
        """
        levels: dict[str, int] = {}
        for logger_name in logging.root.manager.loggerDict:
            if (level := logging.getLogger(logger_name).level) > 0:
                levels[logger_name] = level
        return levels

    def set_log(self, arg: int | dict[str, int] | None = None) -> None:
        """Set the logging level for ARC, or any named logger.

        Supply {"logger_name": <level int>, ...} as a convenient way to alter log content
        for your use case.
        """
        match arg:  # pragma: no cover
            case int(level):
                for logger_name in logging.root.manager.loggerDict:
                    logging.getLogger(logger_name).setLevel(level)
            case {**levels}:
                for name, loglevel in levels.items():
                    logging.getLogger(name).setLevel(loglevel)
            case None:
                self.set_log(self.default_log_levels)
            case _:
                log.warning(f"Unhandled 'arg' value {arg}")

    def scan(self, methods: list[str] = TaskTraits.methods) -> None:
        """Analyze each task based on a set of pre-coded traits.

        These traits can be used to alter the current selection, via the select()
        method. See 'task_analysis.py' for trait details.
        """
        self.stats = Counter()
        for task in self.tasks.values():
            for method in methods:
                getattr(TaskTraits, method)(task)
            self.stats.update(task.traits)

    def select(
        self, selector: set[str] | None = None, selection: set[int] | None = None
    ) -> None:
        """Choose which tasks will be active, by direct selection or by a set of traits."""
        all_idxs = set(self.tasks.keys())
        self.selection = (selection or all_idxs) & all_idxs
        # The selector will sub-select from any included selection
        if selector is not None:
            self.selection = self._select_traits(selector)

    def _select_traits(self, selector: set[str]) -> set[int]:
        """Choose tasks that match the given set of traits in the selector."""
        selection = set([])
        for idx in self.selection:
            if selector.issubset(self.tasks[idx].traits):
                selection.add(idx)
        remove = selection & self.blocklist
        if remove:
            log.info(f"Removing {len(remove)} tasks based on blocklist")
            selection -= remove
        log.info(f"Selected {len(selection)} based on Selector: {selector}")
        return selection

    def solve_task(
        self, idx: int, quiet: bool = False
    ) -> tuple[bool, ErrorReport | None]:
        """Run a single task with exception handling and general reporting."""
        task = self.tasks[idx]
        task_start = time.time()
        solved: bool = False
        error: ErrorReport | None = None
        timeout: bool = False

        try:
            task.solve()
        except profile.TimeoutException:
            timeout = True
            if not quiet:
                log.error(f"Timeout during solve of Task {idx}")
        except Exception as _:
            exception = process_exception()
            if not quiet:
                log.error(f"{exception[0]} during solve of Task {idx}")
                log.error(logger.pretty_traceback(*exception))
        finally:
            task.clean(decomp_tree_only=True)
            mem_mb = profile.get_mem() / 1000
            task_seconds = time.time() - task_start
            if "Solved" in task.traits:
                solved_set = all_eval_solved if self.eval else all_solved
                mark: str = "*" if task.idx not in solved_set else ""
                status = logger.color_text(f"{mark}Passed   ", "green")
                solved = True
            elif timeout:
                status = logger.color_text("Timeout  ", "purple")
            elif error is not None:
                status = logger.color_text("Exception", "red")
            else:
                status = logger.color_text("Failed   ", "yellow")
            log.info(
                f"Task {idx:>3} | {status} | runtime: {task_seconds:.3f}s"
                f" memory: {mem_mb:.2f}Mb"
            )
        return (solved, error)

    def solve_tasks(self, quiet: bool = False) -> dict[int, ErrorReport]:
        """Solve all tasks in the selection, catching errors and run info."""
        queue = sorted(self.selection)
        n = len(queue)
        errors: dict[int, ErrorReport] = {}
        passed = 0

        start = time.time()
        queue_str = (
            queue if len(queue) < 30 else f"[{','.join(map(str, queue[:30]))} ...]"
        )
        log.info(f"Running tasks ({n}): {queue_str}")
        for idx in queue:
            solved, error = self.solve_task(idx, quiet=quiet)
            if solved:
                passed += 1
            if error is not None:
                errors[idx] = error

        seconds = time.time() - start
        log.info(
            f"{n} tasks run in {seconds:.3f}s ({seconds/n:.2f}s per task) |"
            f" {passed} passed ({100*passed/n:.1f}%), {len(errors)} errors "
        )
        return errors
