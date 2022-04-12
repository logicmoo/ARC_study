from arc import ARC

from arc.util import logger
from arc.util import profile

log = logger.fancy_logger("Profiler", level=20)


@profile.time_limit(seconds=3)
def scene_decomposition(arc: ARC, task_idx: int) -> bool:
    try:
        arc.tasks[task_idx][0].decompose()
        return True
    except Exception as exc:
        log.warning(f"Uncaught exception: {exc}")
        return False


@profile.time_limit(seconds=5)
def task_solution(arc: ARC, task_idx: int) -> bool:
    try:
        arc.tasks[task_idx].solve()
        return True
    except Exception as exc:
        log.warning(f"Uncaught exception: {exc}")
        return False


@profile.profile(threshold=0.00, dump_file="arc.prof")
def decomposition(arc: ARC) -> None:
    log.info(f"Profiling execution on first scene from {arc.N} tasks")
    runtime: float = 0
    errors: int = 0
    for idx in arc.selection:
        log.info(f"Decomposing task {idx}:")
        result, seconds = scene_decomposition(arc, idx)
        if not result:
            errors += 1
        log.info(f" ... ran for {seconds:.3f} seconds")
        runtime += seconds
    log.info(f"=== Total runtime: {runtime:.2f}s, ({errors}/{arc.N}) errors ===")


@profile.profile(threshold=0.00, dump_file="arc.prof")
def solution(arc: ARC) -> None:
    log.info(f"Profiling full solution for {arc.N} tasks")
    runtime: float = 0
    errors: int = 0
    for idx in arc.selection:
        log.info(f"Solving task {idx}:")
        result, seconds = task_solution(arc, idx)
        if not result:
            errors += 1
        log.info(f" ... ran for {seconds:.3f} seconds")
        runtime += seconds
    arc.select({"Solved"})
    solved = len(arc.selection)
    log.info(
        f"=== Total runtime: {runtime:.2f}s, {errors} errors ({solved}/{arc.N}) solved ==="
    )


if __name__ == "__main__":
    arc = ARC(N=400)
    arc.set_log(
        {
            "Task": 30,
            "Scene": 30,
        }
    )
    # decomposition(arc)
    solution(arc)
