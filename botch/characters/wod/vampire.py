"""WoD vampire characters."""

from botch.characters.base import GameLine, Splat
from botch.characters.wod.mortal import Mortal


class Vampire(Mortal):
    """A VtM vampire."""

    line: GameLine = GameLine.WOD
    splat: Splat = Splat.VAMPIRE
