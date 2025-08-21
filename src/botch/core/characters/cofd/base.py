"""Base WoD character attributes."""

from enum import StrEnum
from functools import partial
from typing import ClassVar, Self

from pydantic import BaseModel, Field, model_validator

from botch.core.characters.base import Character, GameLine, Splat, Trait
from botch.errors import TraitAlreadyExists
from botch.utils import max_vtr_vitae

INNATE_FACTORY = partial(Trait, category=Trait.Category.INNATE, subcategory=Trait.Subcategory.BLANK)


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

    blood_potency: int = Field(ge=0, le=10)
    vitae: int = Field(ge=0)
    max_vitae: int = Field(ge=0, le=75)

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

    def _all_traits(self) -> list[Trait]:
        """A copy of the vampire's traits, including innates."""
        traits = super()._all_traits()
        potency = [
            INNATE_FACTORY(name="Blood Potency", rating=self.blood_potency),
            INNATE_FACTORY(name="Potency", rating=self.blood_potency),
        ]
        return traits + potency


class Pillar(BaseModel):
    """A Pillar is a special trait that has a permanent and a temporary rating,
    like HP/WP. Unlike those, however, they do not have multiple damage types,
    and we don't care about a graphical representation of them, so we don't use
    a string to represent them."""

    name: str
    rating: int = Field(ge=0, le=5)
    temporary: int = Field(default=-1, ge=-1, le=5)
    category: ClassVar[Trait.Category] = Trait.Category.SPECIAL
    subcategory: ClassVar[Trait.Subcategory] = Trait.Subcategory.PILLARS

    @model_validator(mode="after")
    def set_temporary_on_init(self) -> Self:
        if self.temporary == -1:
            self.temporary = self.rating
        return self

    def pinc(self) -> int:
        """Increment the temporary rating, then return it."""
        self.rating = min(5, self.rating + 1)
        return self.rating

    def pdec(self) -> int:
        """Decrement the temporary rating, then return it."""
        self.rating = max(0, self.rating - 1)
        return self.rating

    def tinc(self) -> int:
        """Increment the temporary rating, then return it."""
        self.temporary = min(self.rating, self.temporary + 1)
        return self.temporary

    def tdec(self) -> int:
        """Decrement the temporary rating, then return it."""
        self.temporary = max(0, self.temporary - 1)
        return self.temporary


class Mummy(Mortal):
    splat: Splat = Splat.MUMMY

    class Pillars(StrEnum):
        AB = "Ab"
        BA = "Ba"
        KA = "Ka"
        REN = "Ren"
        SHEUT = "Sheut"

    sekhem: int = Field(ge=0, le=10)
    pillars: list[Pillar] = Field(default_factory=list)

    @model_validator(mode="after")
    def initialize_pillars(self) -> Self:
        if not self.pillars:
            self.pillars = [Pillar(name=name.value, rating=0) for name in Mummy.Pillars]
        return self

    @property
    def display_traits(self) -> list[Trait]:
        """The Mummy's traits, plus Pillars."""
        return self.traits + self.pillars  # type: ignore

    def get_pillar(self, name: "Mummy.Pillars | str") -> Pillar:
        """Returns the indicated Pillar. Unlike Traits, this is NOT a copy."""
        for pillar in self.pillars:
            if pillar.name.lower() == name.lower():
                return pillar
        raise ValueError("Unknown Pillar")

    def add_trait(
        self,
        name: str,
        rating: int,
        category=Trait.Category.CUSTOM,
        subcategory=Trait.Subcategory.BLANK,
    ) -> Trait:
        """Add a new trait.
        Args:
            name (str): The new Trait's name
            rating (int): The new Trait's rating
            category (enum): The new Trait's category

        The Traits list is automatically kept sorted.

        Returns a copy of the new Trait, if created.
        Raises TraitAlreadyExists if a Trait by that name already exists.
        Raises TraitAlreadyExists if the Trait is a Pillar."""
        titled = name.title()
        if titled in Mummy.Pillars:
            raise TraitAlreadyExists(f"**{titled}** is a Pillar! Use `/character adjust` instead.")

        return super().add_trait(name, rating, category, subcategory)
