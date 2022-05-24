import cProfile
import functools
import pstats
import resource
import signal
import time
from typing import Any, Callable


# This list is passed to @profile() which aggregates the cumulative runtime
# into these functions, which represent the primary stages of task solutioning.
PROFILE_BREAKOUT_STD: list[str] = [
    "Task:decompose",
    "Task:determine_template",
    "Task:match",
    "Solution:create_nodes",
    "Task:test",
]


def profile(
    threshold: float = 0.0, names: list[str] | None = None, dump_file: str | None = None
) -> Callable[[Any], Any]:
    """Measure where cumulative time is spent.

    Args:
        threshold: minimum total cumulative time to display a function
        names: only display functions containing one of these substrings
    """

    def inner(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, list[tuple[str, float]]]:
            # Begin profiling by enabling the profiler
            pr = cProfile.Profile()
            pr.enable()

            # The call we are profiling
            result = func(*args, **kwargs)

            # Stop profiling and analyze the results
            pr.disable()
            ps = pstats.Stats(pr)
            ps.strip_dirs()
            if dump_file:
                ps.dump_stats(dump_file)
            # NOTE: PStats doesn't appear to use typing, thus the ignores
            tot_time: float = max([row[3] for row in ps.stats.values()])  # type: ignore
            stats: list[tuple[str, float]] = []
            for func_triple, data in ps.stats.items():  # type: ignore
                filename = f"{func_triple[0].replace('.py', '').capitalize()}"  # type: ignore
                func_name = f"{filename}:{func_triple[2]}"
                cum_frac: float = round(data[3] / tot_time, 6)  # type: ignore
                if cum_frac > threshold and (
                    names is None or any([name in func_name for name in names])
                ):
                    stats.append((func_name, cum_frac))

            return result, stats

        return wrapper

    return inner


def get_mem() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


class TimeoutException(Exception):
    pass


def time_limit(seconds: int = 5) -> Callable[[Any], Any]:
    """Limit the runtime of the function to the specified number of seconds"""

    def signal_handler(signum: int, frame: Any):
        raise TimeoutException("Timed out!")

    def inner(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        """Wraps a function and throws a Timeout exception if it runs too long"""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, float]:
            # Begin a signal alarm (
            signal.signal(signal.SIGALRM, signal_handler)
            signal.alarm(seconds)
            start = time.time()

            # The call we are limiting
            try:
                result = func(*args, **kwargs)
            except TimeoutException as exc:
                print(f"{exc}: Timed out after {seconds}s")
                return None, seconds

            return result, time.time() - start

        return wrapper

    return inner
