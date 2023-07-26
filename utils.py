"""Various shared utilities."""


def normalize_text(text: str) -> str:
    """Remove extra spaces from a string."""
    return " ".join(text.split())
