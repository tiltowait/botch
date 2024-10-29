"""Base WoD character attributes."""

from pydantic import Field

from core.characters.base import Character, GameLine, Splat, Trait
from utils import max_vtr_vitae


class CofD(Character):
    """Abstract class for CofD characters. Used primarily for inheritance tree
    to let Beanie know what class to instantiate."""

    line: GameLine = GameLine.COFD

    @staticmethod
    def _trait_sort_key(t: Trait) -> str:
        """The key used for insorting traits."""
        Cat = Trait.Category
        Sub = Trait.Subcategory

        params = {
            Cat.ATTRIBUTE: "a",
            Cat.SKILL: "b",
            Sub.MENTAL: "a",
            Sub.PHYSICAL: "b",
            Sub.SOCIAL: "c",
            Sub.TALENTS: "a",
            Sub.SKILLS: "b",
            Sub.KNOWLEDGES: "c",
            # Preserve character sheet attribute order
            "Intelligence": "0",
            "Wits": "1",
            "Resolve": "2",
            "Strength": "3",
            "Dexterity": "4",
            "Stamina": "5",
            "Presence": "6",
            "Manipulation": "7",
            "Composure": "8",
        }

        # Example: Brawl is an ability -> physical. Key: b.a.brawl
        primary = params.get(t.category, "zzz")
        secondary = params.get(t.subcategory, "zzz")
        tertiary = params.get(t.name, t.name)
        return f"{primary}.{secondary}.{tertiary}".casefold()


class Mortal(CofD):
    """Mortals serve as the base template in CofD."""

    splat: Splat = Splat.MORTAL


class Vampire(Mortal):
    """A vampire is a mortal with blood stuff."""

    splat: Splat = Splat.VAMPIRE

    blood_potency: int = Field(ge=1, le=10)
    vitae: int = Field(ge=0)
    max_vitae: int = Field(ge=1, le=75)

    @property
    def blood_pool(self) -> int:
        return self.vitae

    @property
    def max_bp(self) -> int:
        return self.max_vitae

    def add_blood(self, count: int):
        """Add blood, to a maximum of max_vitae."""
        self.vitae = min(self.max_vitae, self.vitae + count)

    def reduce_blood(self, count: int):
        """Reduce blood, to a minimum of 0."""
        self.vitae = max(0, self.vitae - count)

    def increment_max_blood(self):
        """Increase max BP by 1."""
        if self.max_vitae < 50:
            self.max_vitae += 1

    def decrement_max_blood(self):
        """Decrease max BP by 1."""
        if self.max_vitae > 1:
            self.max_vitae -= 1
            self.vitae = min(self.vitae, self.max_vitae)

    def lower_potency(self):
        """Lower generation by 1, adjusting max BP to fit."""
        if self.blood_potency > 0:
            self.blood_potency -= 1
            self.max_vitae = max_vtr_vitae(self.blood_potency)

    def raise_potency(self):
        """Increase generation by 1, adjusting max BP to fit."""
        if self.blood_potency < 10:
            self.blood_potency += 1
            self.max_vitae = max_vtr_vitae(self.blood_potency)
            self.vitae = min(self.vitae, self.max_vitae)


class Mummy(Mortal):
    splat: Splat = Splat.MUMMY

    sekhem: int = Field(ge=0, le=10)
