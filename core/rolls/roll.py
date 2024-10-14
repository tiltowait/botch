"""Dice rolls!"""

import re
from typing import Optional, overload

from beanie import Document, Insert, Link, before_event
from numpy.random import default_rng
from pydantic import Field

import errors
from core.characters import Character, GameLine
from core.rolls.parse import RollParser

_rng = default_rng()  # numpy's default RNG is PCG64 (superior to builtin)


@overload
def d10() -> int:
    ...


@overload
def d10(count: None) -> int:
    ...


@overload
def d10(count: int) -> list[int]:
    ...


def d10(count: int | None = None) -> int | list[int]:
    """Roll many d10s."""
    if count is None:
        return int(_rng.integers(1, 11))
    return list(map(int, _rng.integers(1, 11, count)))


class Roll(Document):
    """Performs a dice roll and calculates the result."""

    line: GameLine
    num_dice: int
    target: int  # WoD: Difficulty; CofD: "again"
    wp: bool = False
    autos: int = 0
    specialties: Optional[list[str]] = Field(default_factory=list)
    rote: bool = False
    dice: list[int] = Field(default_factory=list)
    pool: Optional[list[str | int]] = None
    syntax: Optional[str] = None
    character: Optional[Link[Character]] = None
    use_in_stats: bool = True

    @before_event(Insert)
    def reset_specialties(self):
        """Database operations are slightly easier if specialties is null
        instead of an empty list, so if there aren't any specialties set, we
        will coalesce it into null."""
        if not self.specialties:
            self.specialties = None

    @property
    def uses_traits(self) -> bool:
        """Whether the roll uses traits."""
        if self.pool is None:
            return False
        pool = " ".join(map(str, self.pool))
        return re.match(r"[A-Za-z]", pool) is not None

    @property
    def wod(self) -> bool:
        """Whether it's a WoD roll."""
        return self.line == GameLine.WOD

    @property
    def cofd(self) -> bool:
        """Whether it's a CofD roll."""
        return self.line == GameLine.COFD

    @property
    def difficulty(self) -> int:
        """The required for a success."""
        if self.wod:
            return self.target
        return 8

    @property
    def again(self) -> int:
        """The point at which a die explodes. Always 11 (unreachable) for WoD."""
        if self.wod:
            return 11
        return self.target

    @property
    def successes(self) -> int:
        """The number of successes rolled."""
        if self.line == GameLine.COFD:
            return sum(d >= 8 for d in self.dice) + self.autos

        # WoD rolls have successes canceled by 1s

        # Yes, this isn't very efficient, but we're dealing with tiny amounts
        # of data, and this is more readable.
        successes = sum(d >= self.target for d in self.dice) + self.autos
        if self.specialties:
            tens = sum(d == 10 for d in self.dice)
            successes += tens

        ones = sum(d == 1 for d in self.dice)
        if successes > 0 and ones > successes:
            successes = 0
        else:
            successes -= ones

        if self.wp:
            # WP creates an uncancelable success
            successes = max(successes + 1, 1)

        return successes

    @property
    def success_str(self) -> str:
        """The success string, such as "Exceptional Success"."""
        successes = self.successes  # Prevent recalculation

        if successes < 0:
            return "🤣 Botch!"
        if successes == 0:
            return "Failure"

        if self.line == GameLine.COFD:
            if successes >= 5:
                return "Exceptional!"
            return "Success"

        if successes == 1:
            return "Marginal"
        if successes == 2:
            return "Moderate"
        if successes == 3:
            return "Success"
        if successes == 4:
            return "Exceptional"
        return "Phenomenal!"

    @classmethod
    def from_parser(cls, p: RollParser, target: int, line: GameLine | None = None):
        """Create a roll from a RollParser and a target number."""
        if not line:
            if p.character:
                line = p.character.line
            else:
                raise errors.MissingGameLine

        return cls(
            line=line,
            num_dice=p.num_dice,
            target=target,
            wp=p.using_wp,
            specialties=p.specialties,
            pool=p.pool,
            syntax=p.raw_syntax,
            character=p.character,
        )

    def roll(self):
        """Roll the dice."""
        if self.line == GameLine.WOD:
            # WoD has no special dice rules
            self.dice = d10(self.num_dice)
        else:
            # CofD is more complicated due to explosions
            max_dice = self.num_dice
            if self.wp:
                max_dice += 3
            if self.specialties:
                max_dice += 1

            while len(self.dice) < max_dice:
                self.dice.append(d10())
                if self.dice[-1] >= self.target:
                    # The die exploded
                    max_dice += 1
                elif self.rote:
                    self.dice[-1] = d10()

        return self

    def add_specs(self, specs: list[str]):
        """Add a specialty."""
        if self.specialties is None:
            self.specialties = []
        self.specialties.extend(specs)

    class Settings:
        name = "rolls"
