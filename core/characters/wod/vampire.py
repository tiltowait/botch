"""WoD vampire characters."""

from pydantic import Field

from core.characters.base import GameLine, Splat
from core.characters.wod.mortal import Mortal


class Vampire(Mortal):
    """A VtM vampire."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.VAMPIRE

    generation: int
    max_bp: int
    blood_pool: int = Field(ge=0)

    def add_blood(self, count: int):
        """Add blood, to a maximum of max_bp."""
        self.blood_pool = min(self.max_bp, self.blood_pool + count)

    def reduce_blood(self, count: int):
        """Reduce blood, to a minimum of 0."""
        self.blood_pool = max(0, self.blood_pool - count)
