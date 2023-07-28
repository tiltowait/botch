"""Commonly used slash command options and helpers."""

from discord.commands import Option, OptionChoice


def promoted_choice(
    param: str,
    description: str,
    *,
    start: int,
    end: int,
    first: int | None = None,
    required=True,
):
    """An option that creates a list of numbers between start and end,
    inclusive. If first is specified, then that element is presented first."""

    def decorator(func):
        choices = list(range(start, end + 1))
        if first in choices:
            choices.remove(first)
            choices.insert(0, first)

        func.__annotations__[param] = Option(
            int,
            description,
            name=param,
            required=required,
            choices=choices,
        )
        return func

    return decorator
