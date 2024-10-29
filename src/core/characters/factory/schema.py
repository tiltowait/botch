"""Schema for the character factory."""


import json
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from core.characters import GameLine, Splat, Trait


class TraitSubgroup(BaseModel):
    """Represents a list of traits within a group."""

    name: Trait.Subcategory
    traits: list[str]


class TraitGroup(BaseModel):
    """Represents a list of traits under a similar umbrella."""

    category: Trait.Category
    subcategories: list[TraitSubgroup]

    @property
    def traits(self) -> list[str]:
        """All the traits in the category."""
        return [t for s in self.subcategories for t in s.traits]

    def find_subcategory(self, trait: str) -> Trait.Subcategory | None:
        """Find the trait's subcategory."""
        for sub in self.subcategories:
            if trait in sub.traits:
                return sub.name
        return None


class SpecialTraitType(StrEnum):
    SELECT = "select"
    TRAIT_GROUP = "trait-group"


class SpecialTrait(BaseModel):
    """An individual splat trait.

    For SELECT type:
        - Use options to define valid choices
        - Default should be one of the options

    For TRAIT_GROUP type:
        - Use items to define trait names
        - Use min/max to define value range
        - Default is the starting value
    """

    label: str
    name: str
    type: SpecialTraitType
    options: Optional[list[str] | list[int]] = None
    default: Optional[str | int] = None
    items: Optional[list[str]] = None
    min: Optional[int] = None
    max: Optional[int] = None


class Special(BaseModel):
    """Special, splat-specific traits."""

    splats: list[Splat]
    traits: list[SpecialTrait]


class Schema(BaseModel):
    """The Schema class handles loading and validation of character schemas
    and provides a model for the Factory class to build characters. Schemas
    define only those traits (abilities & attributes) that are captured in
    the character creation wizard."""

    line: GameLine
    splats: list[Splat]
    grounding: dict[Splat, str]
    inherent: TraitGroup
    learned: TraitGroup
    virtues: Optional[list[list[str]]] = None
    special: Optional[list[Special]] = None

    @classmethod
    def load(cls, loc: str):
        """Load the Schema from a file."""
        with open(loc) as f:
            data = json.load(f)
            return cls(**data)

    @property
    def all_traits(self) -> list[str]:
        """The names of all traits in the schema."""
        return self.inherent.traits + self.learned.traits

    def category(self, trait: str) -> Trait.Category:
        """The category the trait belongs to."""
        if trait in self.inherent.traits:
            return self.inherent.category
        if trait in self.learned.traits:
            return self.learned.category
        raise ValueError(f"Unknown trait: {trait}")

    def subcategory(self, trait: str) -> Trait.Subcategory:
        """The subcategory the trait belongs to."""
        if sub := self.inherent.find_subcategory(trait):
            return sub
        if sub := self.learned.find_subcategory(trait):
            return sub
        raise ValueError(f"Unknown trait: {trait}")
