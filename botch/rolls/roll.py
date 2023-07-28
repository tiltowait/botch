"""Dice rolls!"""

from typing import Optional

from beanie import Document, Link
from numpy.random import default_rng
from pydantic import Field

import errors
from botch.characters import Character, GameLine
from botch.rolls.parse import RollParser

_rng = default_rng()  # numpy's default RNG is PCG64 (superior to builtin)


def d10(count: int | None = None) -> int | list[int]:
    """Roll one or many d10s."""
    if count is None:
        return int(_rng.integers(1, 11))
    return list(map(int, _rng.integers(1, 11, count)))


class Roll(Document):
    """Performs a dice roll and calculates the result."""

    line: GameLine
    dice: int
    target: int  # WoD: Difficulty; CofD: "again"
    wp: bool = False
    autos: int = 0
    specialties: Optional[list[str]] = None
    rote: bool = False
    rolled: list[int] = Field(default_factory=list)
    pool: Optional[list[str | int]] = None
    syntax: Optional[str] = None
    character: Optional[Link[Character]] = None

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
            return sum(d >= 8 for d in self.rolled) + self.autos

        # WoD rolls have successes canceled by 1s

        # Yes, this isn't very efficient, but we're dealing with tiny amounts
        # of data, and this is more readable.
        successes = sum(d >= self.target for d in self.rolled) + self.autos
        if self.specialties:
            tens = sum(d == 10 for d in self.rolled)
            successes += tens

        ones = sum(d == 1 for d in self.rolled)
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
            return "Botch!"
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
            dice=p.dice,
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
            self.rolled = d10(self.dice)
        else:
            # CofD is more complicated due to explosions
            max_dice = self.dice
            if self.wp:
                max_dice += 3
            if self.specialties:
                max_dice += 1

            while len(self.rolled) < max_dice:
                self.rolled.append(d10())
                if self.rolled[-1] >= self.target:
                    # The die exploded
                    max_dice += 1
                elif self.rote:
                    self.rolled[-1] = d10()

        return self
