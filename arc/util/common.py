import itertools
from typing import Any, Iterable


# From https://docs.python.org/3/library/itertools.html#itertools-recipes
def all_equal(iterable: Iterable[Any]):
    "Returns True if all the elements are equal to each other"
    group = itertools.groupby(iterable)
    return next(group, True) and not next(group, False)


def get_characteristic(input: str) -> str:
    """Return the unique, sorted characters in the string."""
    return "".join(sorted(set(input)))
