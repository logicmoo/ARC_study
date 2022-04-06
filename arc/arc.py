import glob
import json
import logging
import pickle
from pathlib import Path
from typing import Any, TypeAlias
from collections import Counter

from arc.definitions import Constants as cst
from arc.task import Task
from arc.task_analysis import TaskTraits
from arc.util import logger

log = logger.fancy_logger("ARC", level=20)

Index: TypeAlias = int | str | tuple[int, int] | tuple[int, int, str]


class FailedSolve(Exception):
    pass


class ARC:
    """Load and operate on a collection of Tasks.

    This is the generic starting point for interacting with the ARC dataset and
    the solution process contained in this codebase. It handles loading the data
    and offering high-level control methods.

    Tasks are given an integer index based on the sorted input filenames.

    Attributes:
        N: The number of loaded tasks in the instance.
        selection: The Task indices to consider for operations.
        tasks: The mapping of Task index to Task objects.
    """

    def __init__(
        self,
        N: int = cst.N_TRAIN,
        idxs: set[int] | None = None,
        folder: str = cst.FOLDER_TRAIN,
    ):
        if not idxs:
            idxs = set(range(1, N + 1))
        self.N: int = len(idxs)
        self.selection: set[int] = idxs

        self.tasks: dict[int, Task] = {}
        self.load_tasks(idxs=idxs, folder=folder)

        # TODO find a way to incorporate using blacklist coherently
        self.blacklist: set[int] = set([])
        self.stats: dict[str, int] = Counter()

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

    def load_tasks(self, idxs: set[int] = set(), folder: str = ".") -> None:
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
        log.info(
            f"Loaded {len(self.tasks)} Tasks, with {boards} boards and {tests} tests."
        )

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
            case _:
                log.warning(f"Unhandled 'arg' value {arg}")

    def scan(self, methods: list[str] = TaskTraits.methods) -> None:
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
            self.selection = self._select(selector)

    def _select(self, selector: set[str]) -> set[int]:
        selection = set([])
        for idx in self.selection:
            if selector.issubset(self.tasks[idx].traits):
                selection.add(idx)
        remove = selection & self.blacklist
        if remove:
            log.info(f"Removing {len(remove)} tasks based on blacklist")
            selection -= remove
        log.info(f"Selected {len(selection)} based on Selector: {selector}")
        return selection

    def solve_tasks(self, N: int = 0) -> None:
        """TODO needs updating"""
        for idx in self.selection:
            log.info(f"Solving Task {idx}")
            try:
                self.tasks[idx].solve()
            except Exception as exc:
                msg = f"{type(exc).__name__} {exc}"
                log.warning(f"Error during solve of task {idx} {msg}")
                raise FailedSolve from exc
