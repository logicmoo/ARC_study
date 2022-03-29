from typing import Any, Hashable


def merge(
    d_base: dict[Hashable, Any], d_in: dict[Hashable, Any]
) -> dict[Hashable, Any]:
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


def dict_sub(d_base: dict[Hashable, Any], d_in: dict[Hashable, Any]) -> None:
    for key, val in d_in.items():
        if key in d_base and d_base[key] == val:
            d_base.pop(key)


def dict_and(
    d_left: dict[Hashable, Any], d_right: dict[Hashable, Any]
) -> dict[Hashable, Any]:
    """Returns a dict with any key: val pair present in both."""
    return {key: val for key, val in d_left.items() if d_right.get(key) == val}


def dict_and_group(dict_group: list[dict[Hashable, Any]]) -> dict[Hashable, Any]:
    if not dict_group:
        return {}
    result = dict_group[0]
    for other in dict_group[1:]:
        result = dict_and(result, other)
    return result


def dict_xor(
    d_left: dict[Hashable, Any], d_right: dict[Hashable, Any]
) -> dict[Hashable, Any]:
    """Returns any key: val pair not in both, choosing the left value if mismatch"""
    output = d_left.copy()
    for key, val in d_right.items():
        left_val = d_left.get(key)
        if left_val == val:
            output.pop(key)
        elif left_val is None:
            output[key] = val
    return output
