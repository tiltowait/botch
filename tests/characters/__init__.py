"""Shared helper functions."""

from typing import Type, TypeVar, overload

from core.characters import Character, Damage, GameLine, Grounding, Splat

T = TypeVar("T", bound=Character)


@overload
def gen_char(line: GameLine, splat: Splat, **kwargs) -> Character:
    ...


@overload
def gen_char(line: GameLine, splat: Splat, cls: Type[T], **kwargs) -> T:
    ...


def gen_char(line: GameLine, splat: Splat, cls: Type[T] = Character, **kwargs) -> T:
    """Create a basic character."""
    args = {
        "name": "Test",
        "line": line,
        "splat": splat,
        "guild": 0,
        "user": 0,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * 6,
        "grounding": Grounding(path="Humanity", rating=7),
    }
    args.update(kwargs)

    return cls(**args)
