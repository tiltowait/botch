"""Shared helper functions."""

from botch.characters import Character, Damage, GameLine, Grounding, Splat


def gen_char(line: GameLine, splat: Splat, cls=Character, **kwargs) -> Character:
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
