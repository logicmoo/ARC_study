import itertools
import sys
import traceback
from traceback import FrameSummary
from typing import Any, Iterable


# From https://docs.python.org/3/library/itertools.html#itertools-recipes
def all_equal(iterable: Iterable[Any]):
    "Returns True if all the elements are equal to each other"
    group = itertools.groupby(iterable)
    return next(group, True) and not next(group, False)


def get_characteristic(input: str | list[str]) -> str:
    """Return the unique, sorted characters in the string."""
    return "".join(sorted(set(input)))


def process_exception() -> tuple[str, str, list[FrameSummary]]:
    exc_type, exc_value, exc_tb = sys.exc_info()
    exc_name = getattr(exc_type, "__name__", "")
    tb = traceback.extract_tb(exc_tb)
    return (exc_name, str(exc_value), tb)
