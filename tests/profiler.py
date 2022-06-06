import argparse

# Guppy provides a breakdown of data structures and their mem usage
# which can be useful occasionally.
# from guppy import hpy  # type: ignore

from arc.arc import ARC
from arc.definitions import Constants as cst
from arc.util import logger
from arc.util import profile

log = logger.fancy_logger("Profiler", level=20)


@profile.profile(threshold=0.05, dump_file="arc.prof")
def decompose(_arc: ARC, time_limit: int) -> None:
    log.info(f"Profiling execution on first scene from {_arc.N} tasks")
    runtime: float = 0
    errors: int = 0

    @profile.time_limit(seconds=time_limit)
    def timed_decomposition(_arc: ARC, task_idx: int) -> bool:
        try:
            _arc.tasks[task_idx][0].decompose()
            return True
        except Exception as exc:
            log.warning(f"Uncaught exception: {exc}")
            return False

    for idx in _arc.selection:
        log.info(f"Decomposing task {idx}:")
        result, seconds = timed_decomposition(_arc, idx)
        if not result:
            errors += 1
        log.info(f" ... ran for {seconds:.3f} seconds")
        runtime += seconds
    log.info(f"=== Total runtime: {runtime:.2f}s, ({errors}/{_arc.N}) errors ===")


@profile.profile(names=profile.PROFILE_BREAKOUT_STD, dump_file="arc.prof")
def solve(_arc: ARC, time_limit: int) -> None:
    log.info(f"Profiling full solution for {_arc.N} tasks")
    runtime: float = 0
    errors: int = 0
    # hp = hpy()

    @profile.time_limit(seconds=time_limit)
    def timed_solve(_arc: ARC, task_idx: int) -> None:
        _arc.solve_task(task_idx, quiet=True)

    for idx in _arc.selection:
        _, seconds = timed_solve(_arc, idx)
        # print(hp.heap())
        _arc[idx].clean()
        runtime += seconds
    _arc.select({"Solved"})
    solved = len(_arc.selection)
    log.info(
        f"=== Total runtime: {runtime:.2f}s, {errors} errors ({solved}/{_arc.N}) solved ==="
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ")
    parser.add_argument(
        "-d", "--decompose", help="Run decomposition only", action="store_true"
    )
    parser.add_argument(
        "-e", "--evaluation", help="Run evaluation tasks", action="store_true"
    )
    parser.add_argument(
        "-q", "--quiet", help="Only show profiler logging", action="store_true"
    )
    parser.add_argument(
        "-s", "--single", help="Run a single task index (N = idx)", action="store_true"
    )
    parser.add_argument(
        "-t", "--time_limit", help="Maximum seconds per task", type=int, default=60
    )
    parser.add_argument(
        "-v", "--verbose", help="Show debug logging", action="store_true"
    )
    parser.add_argument("N", metavar="N", type=int, help="Total tasks to run")
    args = parser.parse_args()

    folder = cst.FOLDER_TRAIN
    if args.evaluation:
        folder = cst.FOLDER_EVAL

    if args.single:
        _arc = ARC(idxs={args.N}, folder=folder)
    else:
        _arc = ARC(N=args.N, folder=folder)

    if args.quiet:
        _arc.set_log(50)
        _arc.set_log({"Profiler": 20, "ARC": 20})
    elif args.verbose:
        _arc.set_log(10)
    else:
        _arc.set_log(
            {
                "Task": 30,
                "Scene": 30,
            }
        )

    stats: list[tuple[str, str]] = []
    if args.decompose:
        _, stats = decompose(_arc, args.time_limit)
    else:
        _, stats = solve(_arc, args.time_limit)

    for func, val in sorted(stats, key=lambda x: x[1], reverse=True):
        percentage = f"{100*val:.2f}%"
        log.info(f"{percentage: >6s} - {func}")
