"""WoD vampire characters."""

from characters.base import GameLine, Splat
from characters.wod.mortal import Mortal


class Vampire(Mortal):
    """A VtM vampire."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.VAMPIRE
