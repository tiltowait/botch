"""Schema for the character factory."""


import json
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


class SpecialTrait(BaseModel):
    """An individual splat trait."""

    name: str
    type: str
    options: Optional[list[str] | list[int]]
    default: Optional[str | int]


class Special(BaseModel):
    """Special, splat-specific traits."""

    splat: str
    traits: list[SpecialTrait]


class Schema(BaseModel):
    """The Schema class handles loading and validation of character schemas
    and provides a model for the Factory class to build characters. Schemas
    define only those traits (abilities & attributes) that are captured in
    the character creation wizard."""

    line: GameLine
    splats: list[Splat]
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
