"""Mortal character templates."""

from typing import List

from botch.characters.base import Character, GameLine, Splat, Trait


def gen_virtues(virtues: dict[str, int]):
    """Generate a list of virtue Traits."""
    return [Trait(name=k, rating=v, category=Trait.Category.VIRTUE) for k, v in virtues.items()]


class Mortal(Character):
    """Mortals serve as the base template in WoD."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.MORTAL

    virtues: List[Trait]
