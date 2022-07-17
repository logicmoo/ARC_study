import argparse
import multiprocessing as mp
import time
from multiprocessing.context import Process
from queue import Queue

from arc.arc import ARC
from arc.definitions import Constants as cst
from arc.task_analysis import all_eval_solved, all_solved, blocklist, fast_solved
from arc.util import logger

log = logger.fancy_logger("Script", level=20)


def solve_task(folder: str, idxs: Queue[int], results: Queue[bool]) -> None:
    """Worker method that draws from an index Queue."""
    for idx in iter(idxs.get, -1):
        _arc = ARC(idxs={idx}, quiet=True, folder=folder)
        _arc.set_log(40)
        _arc.set_log({"ARC": 20})
        solved, _ = _arc.solve_task(idx, quiet=True)
        if solved:
            results.put(True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run ARC Tasks--by default, only those known to be solved."
    )
    parser.add_argument(
        "-a", "--all", help="Run all train tasks (~90s on 6 cores)", action="store_true"
    )
    parser.add_argument(
        "-e", "--evaluation", help="Run all evaluation tasks", action="store_true"
    )
    parser.add_argument(
        "-f",
        "--fast",
        help="Run only fast solved tasks (~8s on 1 core)",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--n_procs",
        help="How many processes to run (~CPU cores)",
        type=int,
        default=6,
    )
    args = parser.parse_args()

    folder = cst.FOLDER_TRAIN
    tasks_to_run = all_solved
    if args.evaluation:
        folder = cst.FOLDER_EVAL
        tasks_to_run = all_eval_solved

    if args.fast:
        if args.evaluation:
            log.warning("Cannot use 'fast' with evaluation dataset")
        else:
            tasks_to_run = fast_solved
    elif args.all:
        tasks_to_run = {i for i in range(1, 401)}

    if not args.evaluation:
        initial = len(tasks_to_run)
        tasks_to_run -= blocklist
        n_blocked = initial - len(tasks_to_run)
        if n_blocked > 0:
            log.info(f"Removing {n_blocked} tasks from blocklist")

    n = len(tasks_to_run)
    idxs: Queue[int] = mp.Queue()
    results: Queue[bool] = mp.Queue()
    for idx in sorted(tasks_to_run):
        idxs.put(idx)

    log.info(f"Running {n} tasks on {args.n_procs} processes")
    start = time.time()

    jobs: list[Process] = []
    for core in range(args.n_procs):
        idxs.put(-1)  # Add the sentinel to tell the workers to stop
        proc = mp.Process(target=solve_task, args=(folder, idxs, results))
        proc.start()
        jobs.append(proc)

    while any(job.is_alive() for job in jobs):
        pass

    seconds = time.time() - start
    passed = 0
    while not results.empty():
        if results.get():
            passed += 1

    log.info(
        f"{n} tasks run in {seconds:.3f}s ({seconds/n:.2f}s per task) |"
        f" {passed} passed ({100*passed/n:.1f}%)"
    )
