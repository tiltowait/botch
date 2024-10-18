"""Mortal character templates."""

from core.characters.base import GameLine, Splat, Trait
from core.characters.wod.base import WoD


def gen_virtues(virtues: dict[str, int]):
    """Generate a list of virtue Traits."""
    return [
        Trait(
            name=k,
            rating=v,
            category=Trait.Category.VIRTUE,
            subcategory=Trait.Subcategory.BLANK,
        )
        for k, v in virtues.items()
    ]


class Mortal(WoD):
    """Mortals serve as the base template in WoD."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.MORTAL

    virtues: list[Trait]


class Ghoul(Mortal):
    """A ghoul is just a fancy mortal."""

    bond_strength: int
