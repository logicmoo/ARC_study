import collections
from typing import Any, TypeVar

_KeyT = TypeVar("_KeyT", bound=str | int | tuple[Any, ...])


def merge(d_base: dict[_KeyT, Any], d_in: dict[_KeyT, Any]) -> dict[_KeyT, Any]:
    """Adds leaves of nested dict d_in to d_base, keeping d_base where overlapping"""
    for key in d_in:
        if key in d_base:
            if isinstance(d_base[key], dict) and isinstance(d_in[key], dict):
                merge(d_base[key], d_in[key])
            elif isinstance(d_base[key], list) and isinstance(d_in[key], list):
                d_base[key].extend(d_in[key])
            elif d_base[key] != d_in[key]:
                d_base[key] = d_in[key]
        else:
            if isinstance(d_in[key], list | dict):
                d_base[key] = d_in[key].copy()
            else:
                d_base[key] = d_in[key]
    return d_base


def dict_sub(d_base: dict[_KeyT, Any], d_in: dict[_KeyT, Any]) -> None:
    for key, val in d_in.items():
        if key in d_base and d_base[key] == val:
            d_base.pop(key)


def dict_and(d_left: dict[_KeyT, Any], d_right: dict[_KeyT, Any]) -> dict[_KeyT, Any]:
    """Returns a dict with any key: val pair present in both."""
    return {key: val for key, val in d_left.items() if d_right.get(key) == val}


def dict_and_group(dict_group: list[dict[_KeyT, Any]]) -> dict[_KeyT, Any]:
    if not dict_group:
        return {}
    result = dict_group[0]
    for other in dict_group[1:]:
        result = dict_and(result, other)
    return result


def dict_val2set(
    dict_group: list[dict[_KeyT, int | str]]
) -> dict[_KeyT, set[int | str]]:
    if not dict_group:
        return {}
    result: dict[_KeyT, set[int | str]] = collections.defaultdict(set)
    for inp in dict_group:
        for key, val in inp.items():
            result[key].add(val)
    return result


def dict_popset(
    base: dict[_KeyT, set[int | str]], dict_group: list[dict[_KeyT, int | str]]
) -> dict[_KeyT, set[int | str]]:
    if not base:
        return {}
    for inp in dict_group:
        for key, val in inp.items():
            if key not in base:
                continue
            base[key].discard(val)
            if not base[key]:
                base.pop(key)
    return base


def dict_xor(d_left: dict[_KeyT, Any], d_right: dict[_KeyT, Any]) -> dict[_KeyT, Any]:
    """Returns any key: val pair not in both, choosing the left value if mismatch"""
    output = d_left.copy()
    for key, val in d_right.items():
        left_val = d_left.get(key)
        if left_val == val:
            output.pop(key)
        elif left_val is None:
            output[key] = val
    return output


def key_concat(inp: dict[_KeyT, Any]) -> str:
    return "".join(map(str, inp.keys()))
