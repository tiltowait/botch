"""Shared helper functions."""

from characters import Character, Damage, Grounding, Splat


def gen_char(splat: Splat, **kwargs) -> Character:
    """Create a basic character."""
    args = {
        "name": "Test",
        "splat": splat,
        "guild": 0,
        "user": 0,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * 6,
        "grounding": Grounding(path="Humanity", rating=7),
    }
    args.update(kwargs)

    return Character(**args)
