import argparse

# Guppy provides a breakdown of data structures and their mem usage
# which can be useful occasionally.
# from guppy import hpy  # type: ignore

from arc.arc import ARC
from arc.util import logger
from arc.util import profile

log = logger.fancy_logger("Profiler", level=20)


@profile.time_limit(seconds=3)
def scene_decomposition(_arc: ARC, task_idx: int) -> bool:
    try:
        _arc.tasks[task_idx][0].decompose()
        return True
    except Exception as exc:
        log.warning(f"Uncaught exception: {exc}")
        return False


@profile.time_limit(seconds=10)
def task_solution(_arc: ARC, task_idx: int) -> bool:
    try:
        _arc.tasks[task_idx].solve()
        return True
    except Exception as exc:
        log.warning(f"Uncaught exception: {exc}")
        return False


@profile.profile(threshold=0.00, dump_file="arc.prof")
def decomposition(_arc: ARC) -> None:
    log.info(f"Profiling execution on first scene from {_arc.N} tasks")
    runtime: float = 0
    errors: int = 0
    for idx in _arc.selection:
        log.info(f"Decomposing task {idx}:")
        result, seconds = scene_decomposition(_arc, idx)
        if not result:
            errors += 1
        log.info(f" ... ran for {seconds:.3f} seconds")
        runtime += seconds
    log.info(f"=== Total runtime: {runtime:.2f}s, ({errors}/{_arc.N}) errors ===")


@profile.profile(threshold=0.00, dump_file="arc.prof")
def solution(_arc: ARC) -> None:
    log.info(f"Profiling full solution for {_arc.N} tasks")
    runtime: float = 0
    errors: int = 0
    # hp = hpy()
    for idx in _arc.selection:
        result, seconds = task_solution(_arc, idx)
        status = "Failed"
        if "Solved" in _arc.tasks[idx].traits:
            status = logger.color_text("Passed", "green")
        elif not result:
            errors += 1
            status = logger.color_text("Exception", "red")
        mem_mb = profile.get_mem() / 1000
        log.info(
            f"Task {idx:>3} | {status} | runtime: {seconds:.3f}s  memory: {mem_mb:.2f}Mb"
        )
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
        "-q", "--quiet", help="Only show profiler logging", action="store_true"
    )
    parser.add_argument(
        "-v", "--verbose", help="Show debug logging", action="store_true"
    )
    parser.add_argument("N", metavar="N", type=int, help="Total tasks to run")
    args = parser.parse_args()

    _arc = ARC(N=args.N)

    if args.quiet:
        _arc.set_log(50)
        _arc.set_log({"Profiler": 20})
    elif args.verbose:
        _arc.set_log(10)
    else:
        _arc.set_log(
            {
                "Task": 30,
                "Scene": 30,
            }
        )

    # decomposition(arc)
    solution(_arc)
