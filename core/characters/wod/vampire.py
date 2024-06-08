"""WoD vampire characters."""

from core.characters.base import GameLine, Splat
from core.characters.wod.mortal import Mortal


class Vampire(Mortal):
    """A VtM vampire."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.VAMPIRE

    generation: int
    max_bp: int
    blood_pool: int
