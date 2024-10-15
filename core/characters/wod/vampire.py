"""WoD vampire characters."""

from pydantic import Field

from core.characters.base import GameLine, Splat
from core.characters.wod.mortal import Mortal
from utils import max_vtm_bp, max_vtm_trait


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

    def increment_max_bp(self):
        """Increase max BP by 1."""
        if self.max_bp < 50:
            self.max_bp += 1

    def decrement_max_bp(self):
        """Decrease max BP by 1."""
        if self.max_bp > 1:
            self.max_bp -= 1
            self.blood_pool = min(self.blood_pool, self.max_bp)

    def lower_generation(self):
        """Lower generation by 1, adjusting max BP to fit."""
        if self.generation > 3:
            self.generation -= 1
            self.max_bp = max_vtm_bp(self.generation)

    def raise_generation(self):
        """Increase generation by 1, adjusting max BP to fit."""
        if self.generation < 15:
            self.generation += 1
            self.max_bp = max_vtm_bp(self.generation)
            self.blood_pool = min(self.blood_pool, self.max_bp)
