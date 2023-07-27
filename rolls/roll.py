"""Dice rolls!"""

from typing import Optional

from beanie import Document, Link
from pydantic import Field

import errors
from characters import Character, GameLine
from rolls import d10
from rolls.parse import RollParser


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
                return "Exceptional Success!"
            return "Success"

        if successes == 1:
            return "Marginal Success"
        if successes == 2:
            return "Moderate Success"
        if successes == 3:
            return "Complete Success"
        if successes == 4:
            return "Exceptional Success"
        return "Phenomenal Success!"

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
