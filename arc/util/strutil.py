def get_characteristic(input: str) -> str:
    """Return the unique, sorted characters in the string."""
    return "".join(sorted(set(input)))
