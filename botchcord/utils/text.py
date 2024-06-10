"""Discord text utilities."""


def b(text: str) -> str:
    """Bold text."""
    return f"**{text}**"


def i(text: str) -> str:
    """Italic text."""
    return f"*{text}*"


def bi(text: str) -> str:
    """Bolditalic text."""
    return f"***{text}***"


def u(text: str) -> str:
    """Underlined text."""
    return f"__{text}__"


def m(text: str) -> str:
    """Monospaced text."""
    return f"`{text}`"


def c(text: str) -> str:
    """Code-fenced text."""
    return f"```{text}```"
