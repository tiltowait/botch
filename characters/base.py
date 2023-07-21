"""Base character models used by all splats. Some splats have their own
subclasses."""

import bisect
import copy
from collections import Counter
from enum import StrEnum

import errors
import pymongo
from beanie import Document
from pydantic import BaseModel, Field


class Damage(StrEnum):
    NONE = "."
    BASHING = "/"
    LETHAL = "X"
    AGGRAVATED = "*"


class Splat(StrEnum):
    V20 = "v20"
    M20 = "m20"


class Grounding(BaseModel):
    """Humanity, Paths of Enlightenment, Integrity, etc."""

    path: str
    rating: int


class Tracker(StrEnum):
    HEALTH = "health"
    WILLPOWER = "willpower"


class Trait(BaseModel):
    """A trait represents an Attribute, Ability, Discipline, etc."""

    class Category(StrEnum):
        ATTRIBUTE = "attribute"
        ABILITY = "ability"
        SPECIAL = "special"
        CUSTOM = "custom"

    name: str
    rating: int
    category: Category
    subtraits: list[str] = Field(default_factory=list)

    def matches(self, search: str) -> bool:
        """Return true if the trait name starts with the search string."""
        return self.name.casefold().startswith(search.casefold())


class Character(Document):
    """The character class contains all the standard fields for any character.

    WARNING: Character.traits items may be modified by a receiver, resulting in
    unexpected behavior. Do not directly work on these objects; use
    Character.get_traits() instead."""

    name: str
    splat: Splat

    guild: int
    user: int

    health: str
    willpower: str
    grounding: Grounding

    traits: list[Trait] = Field(default_factory=list)

    def set_damage(self, tracker: Tracker, severity: Damage, count: int) -> str:
        """Set the tracker's new damage rating. Returns the new track."""

        def _track(track: str, severity: Damage, count: int):
            """Inner fuction handles the actual work."""
            length = len(track)
            counter = Counter()

            for elem in track:
                counter[elem] += 1
            counter[severity] = count

            # Reconstruct the track string. Reverse the damage, because we may
            # truncate by lopping off from the end.
            new_track = ""
            for sev in reversed(Damage):
                new_track += sev * counter[sev]

            # Make sure the new track is the same length as originally
            if len(new_track) > length:
                new_track = new_track[:length]
            else:
                diff = length - len(new_track)
                new_track += Damage.NONE * diff

            return new_track[::-1]

        if tracker == Tracker.WILLPOWER:
            self.willpower = _track(self.willpower, severity, count)
            return self.willpower
        self.health = _track(self.health, severity, count)
        return self.health

    # Traits

    def has_trait(self, name: str) -> bool:
        """See if a trait by this exact name exists."""
        for trait in self.traits:
            if trait.name.casefold() == name.casefold():
                return True
        return False

    def find_traits(self, search: str) -> list[Trait]:
        """Get copies of all traits starting with the search key."""
        traits = []
        for trait in self.traits:
            if trait.matches(search):
                traits.append(copy.deepcopy(trait))
        return traits

    def add_trait(self, name: str, rating: int, category=Trait.Category.CUSTOM) -> Trait:
        """Add a new trait.
        Args:
            name (str): The new trait's name
            rating (int): The new trait's rating
            category (enum): The new trait's category

        The traits list is automatically kept sorted.

        Returns a copy of the new trait, if created.
        Raises TraitAlreadyExists if a trait by that name already exists."""
        if self.has_trait(name):
            raise errors.TraitAlreadyExists(f"**{self.name}** already has a trait called `{name}`.")

        new_trait = Trait(name=name, rating=rating, category=category)
        bisect.insort(self.traits, new_trait, key=lambda t: t.name.casefold())

        return copy.deepcopy(new_trait)

    class Settings:
        name = "characters"
        indexes = [
            [
                ("guild", pymongo.ASCENDING),
                ("user", pymongo.ASCENDING),
            ]
        ]
        is_root = True
        use_state_management = True
