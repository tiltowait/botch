"""World of Darkness characters submodule."""

from core.characters.wod.mortal import Ghoul, Mortal, gen_virtues
from core.characters.wod.vampire import Vampire

__all__ = ("Ghoul", "Mortal", "Vampire", "gen_virtues")
