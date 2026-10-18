"""Shared helper functions."""

from typing import overload

from botch.core.characters import Character, Damage, GameLine, Grounding, Splat


@overload
def gen_char(line: GameLine, splat: Splat, **kwargs) -> Character: ...


@overload
def gen_char[T: Character](line: GameLine, splat: Splat, cls: type[T], **kwargs) -> T: ...


def gen_char[T: Character](line: GameLine, splat: Splat, cls: type[T] = Character, **kwargs) -> T:
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
