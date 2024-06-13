"""Discord text utilities."""


def b(text: object) -> str:
    """Bold text."""
    return f"**{text}**"


def i(text: object) -> str:
    """Italic text."""
    return f"*{text}*"


def bi(text: object) -> str:
    """Bolditalic text."""
    return f"***{text}***"


def u(text: object) -> str:
    """Underlined text."""
    return f"__{text}__"


def m(text: object) -> str:
    """Monospaced text."""
    return f"`{text}`"


def c(text: object) -> str:
    """Code-fenced text."""
    return f"```{text}```"
