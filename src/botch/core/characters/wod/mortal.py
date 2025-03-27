"""Mortal character templates."""

from botch.core.characters.base import GameLine, Splat, Trait
from botch.core.characters.wod.base import WoD


def gen_virtues(virtues: dict[str, int]):
    """Generate a list of virtue Traits."""
    return [
        Trait(
            name=k,
            rating=v,
            category=Trait.Category.SPECIAL,
            subcategory=Trait.Subcategory.VIRTUES,
        )
        for k, v in virtues.items()
    ]


class Mortal(WoD):
    """Mortals serve as the base template in WoD."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.MORTAL

    virtues: list[Trait]

    @property
    def display_traits(self) -> list[Trait]:
        """The character's traits, plus Virtues."""
        return self.traits + self.virtues


class Ghoul(Mortal):
    """A ghoul is just a fancy mortal."""

    splat: Splat = Splat.GHOUL
