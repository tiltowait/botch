"""Various shared utilities."""


def normalize_text(text: str) -> str:
    """Remove extra spaces from a string."""
    return " ".join(text.split())


def max_vtm_bp(generation: int) -> int:
    """The maximum blood pool for a given generation."""
    if generation >= 8:
        return max(15 - (generation - 8), 10)
    return (5 - (generation - 4)) * 10


def max_vtm_trait(generation: int) -> int:
    if generation >= 8:
        return 5
    return 10 - (generation - 3)


def format_join(collection: list, separator: str, f: str, alt="") -> str:
    """Join a collection by a separator, formatting each item."""
    return separator.join(map(lambda c: f"{f}{c}{f}", collection)) or alt
