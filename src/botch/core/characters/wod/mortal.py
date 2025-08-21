"""Mortal character templates."""

from copy import deepcopy
from enum import StrEnum

from pydantic import field_validator

from botch.core.characters.base import GameLine, Splat, Trait
from botch.core.characters.wod.base import WoD


class Virtue(Trait):
    """A Virtue is a Trait with predefined category and subcategory."""

    class Name(StrEnum):
        CONSCIENCE = "Conscience"
        CONVICTION = "Conviction"
        SELF_CONTROL = "SelfControl"
        INSTINCT = "Instinct"
        COURAGE = "Courage"

    category: Trait.Category = Trait.Category.SPECIAL
    subcategory: Trait.Subcategory = Trait.Subcategory.VIRTUES

    @field_validator("name")
    @classmethod
    def validate_virtue_name(cls, v: str):
        if v not in cls.Name:
            raise ValueError(f"Unknown Virtue: {v}")
        return v


def gen_virtues(virtues: dict[str, int]) -> list[Virtue]:
    """Generate a list of virtue Traits."""
    return [Virtue(name=k, rating=v) for k, v in virtues.items()]


class Mortal(WoD):
    """Mortals serve as the base template in WoD."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.MORTAL

    virtues: list[Trait]

    @property
    def display_traits(self) -> list[Trait]:
        """The character's traits, plus Virtues."""
        return self.traits + self.virtues

    def _all_traits(self) -> list[Trait]:
        """A copy of the character's rollable traits."""
        traits = super()._all_traits()
        return traits + deepcopy(self.virtues)


class Ghoul(Mortal):
    """A ghoul is just a fancy mortal."""

    splat: Splat = Splat.GHOUL
