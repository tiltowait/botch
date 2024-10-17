"""Base character models used by all splats. Some splats have their own
subclasses."""

import bisect
import copy
from collections import Counter
from enum import StrEnum
from itertools import product
from typing import Literal, Optional, overload

import pymongo
from beanie import Delete, Document, before_event
from pydantic import AnyUrl, BaseModel, Field, HttpUrl

import api
import errors
from config import MAX_NAME_LEN


class Damage(StrEnum):
    NONE = "."
    BASHING = "/"
    LETHAL = "X"
    AGGRAVATED = "*"

    @classmethod
    def emoji_name(cls, e: str) -> str:
        """The box's emoji name."""
        emoji = {
            Damage.NONE.value: "no_dmg",
            Damage.BASHING.value: "bash",
            Damage.LETHAL.value: "leth",
            Damage.AGGRAVATED.value: "agg",
        }
        return emoji[e]


class GameLine(StrEnum):
    WOD = "wod"
    COFD = "cofd"


class Splat(StrEnum):
    MORTAL = "mortal"
    VAMPIRE = "vampire"
    GHOUL = "ghoul"


class Experience(BaseModel):
    """Character experience totals."""

    unspent: int = 0
    lifetime: int = 0


class Grounding(BaseModel):
    """Humanity, Paths of Enlightenment, Integrity, etc."""

    path: str
    rating: int = Field(ge=0, le=10)

    def increment(self):
        """Increase rating by 1, to a maximum of 10."""
        self.rating = min(10, self.rating + 1)

    def decrement(self):
        """Decrease rating by 1, to a minimum of 0."""
        self.rating = max(0, self.rating - 1)


class Tracker(StrEnum):
    HEALTH = "health"
    WILLPOWER = "willpower"


class Profile(BaseModel):
    """Contains the character's description, history, and image URLs."""

    description: Optional[str] = Field(default=None, max_length=1024)
    history: Optional[str] = Field(default=None, max_length=1024)
    images: list[HttpUrl] = Field(default_factory=list)

    @property
    def main_image(self) -> str | None:
        """The character's main profile image."""
        return str(self.images[0]) if self.images else None

    def add_image(self, url: str):
        """Add an image."""
        self.images.append(AnyUrl(url))

    def remove_image(self, url: str):
        """Remove an image."""
        self.images.remove(AnyUrl(url))


class Trait(BaseModel):
    """A trait represents an Attribute, Ability, Discipline, etc."""

    _DELIMITER = "."

    class Category(StrEnum):
        ATTRIBUTE = "attributes"
        ABILITY = "abilities"
        VIRTUE = "virtues"
        SPECIAL = "special"
        INNATE = "innate"
        CUSTOM = "custom"

    class Subcategory(StrEnum):
        PHYSICAL = "physical"
        SOCIAL = "social"
        MENTAL = "mental"
        TALENTS = "talents"
        SKILLS = "skills"
        KNOWLEDGES = "knowledges"
        BLANK = "\u200b"  # Discord doesn't allow empty field names
        CUSTOM = "custom"

    class Selection(BaseModel):
        """When the user invokes a Trait, they receive a Trait.Selection. This
        is a copy of the Trait's relevant details, with the name reflecting
        any subtraits selected. For instance, a Trait.Selection matching
        "brawl.throws" would become "Brawl (Throws)"."""

        name: str  # The selected name, such as "Brawl (Throws)"
        rating: int  # In CofD, the rating might be higher than the base Trait's
        exact: bool  # Whether the user exactly searched for this Selection
        key: str  # The exact search key matching this Selection, ("Brawl.Kindred")
        subtraits: list[str]  # The list of subtraits selected
        category: str  # The Trait.Category. Must be str due to placement here

    name: str
    rating: int
    category: Category
    subcategory: Subcategory
    subtraits: list[str] = Field(default_factory=list)

    def add_subtraits(self, subtraits: str | list[str] | set[str]):
        """Add subtraits to the trait."""
        if isinstance(subtraits, str):
            subtraits = {subtraits}
        else:
            subtraits = set(subtraits)

        for subtrait in subtraits:
            if subtrait.casefold() not in map(str.casefold, self.subtraits):
                self.subtraits.append(subtrait)

        self.subtraits.sort()

    def remove_subtraits(self, subtraits: str | list[str] | set[str]):
        """Remove subtraits from the trait."""
        if isinstance(subtraits, str):
            subtraits = {subtraits}
        else:
            subtraits = set(subtraits)

        for subtrait in map(str.casefold, subtraits):
            current = [spec.casefold() for spec in self.subtraits]
            try:
                index = current.index(subtrait)
                del self.subtraits[index]
            except ValueError:
                continue

    def matches(self, search: str) -> bool:
        """Return true if the trait name starts with the search string."""
        return self.name.casefold().startswith(search.casefold())

    def matching(self, identifier: str, exact: bool) -> list[Selection]:
        """Returns a list of Selections that match the identifier."""
        expanded_groups = self.expanding(identifier, exact, join=False)

        if not expanded_groups:
            return []

        normalized = self._normalize_identifier(identifier)

        return [
            self._create_selection(group, normalized == self._DELIMITER.join(group).casefold())
            for group in expanded_groups
        ]

    @overload
    def expanding(self, identifier: str, exact: bool) -> list[str]:
        ...

    @overload
    def expanding(self, identifier: str, exact: bool, join: Literal[True]) -> list[str]:
        ...

    @overload
    def expanding(self, identifier: str, exact: bool, join: Literal[False]) -> list[list[str]]:
        ...

    def expanding(self, identifier: str, exact: bool, join=True) -> list[str] | list[list[str]]:
        """Expand the user's input to full skill:spec names."""
        tokens = identifier.lower().split(self._DELIMITER)
        comp = self._exact_comp if exact else self._starting_comp

        if not comp(tokens[0], self.name):
            return []

        spec_groups = self._get_matching_spec_groups(tokens[1:], comp)

        if not spec_groups:
            matches = [[self.name]]
        else:
            matches = self._generate_unique_matches(spec_groups)

        return [self._DELIMITER.join(match) for match in matches] if join else matches

    def _normalize_identifier(self, identifier: str) -> str:
        tokens = identifier.split(self._DELIMITER)
        return self._DELIMITER.join([tokens[0]] + sorted(tokens[1:])).lower()

    def _create_selection(self, group: list[str], is_exact: bool) -> Selection:
        full_name = self.name
        if len(group) > 1:
            full_name += f" ({', '.join(group[1:])})"

        return Trait.Selection(
            name=full_name,
            rating=self.rating,
            exact=is_exact,
            key=self._DELIMITER.join(group),
            subtraits=group[1:],
            category=self.category,
        )

    def _get_matching_spec_groups(self, tokens: list[str], comp) -> list[list[str]]:
        return [
            [subtrait for subtrait in self.subtraits if comp(token, subtrait)] for token in tokens
        ]

    def _generate_unique_matches(self, spec_groups: list[list[str]]) -> list[list[str]]:
        if len(spec_groups) == 1:
            return [[self.name, spec] for spec in spec_groups[0]]

        combinations = product(*spec_groups)
        seen_groups = set()
        matches = []

        for group in combinations:
            if len(set(group)) < len(group):
                continue
            frozen_group = frozenset(group)
            if frozen_group not in seen_groups:
                seen_groups.add(frozen_group)
                matches.append([self.name] + sorted(group))

        return matches

    @staticmethod
    def _exact_comp(t: str, i: str) -> bool:
        return t == i.lower()

    @staticmethod
    def _starting_comp(t: str, i: str) -> bool:
        return i.lower().startswith(t)


class Character(Document):
    """The character class contains all the standard fields for any character.

    WARNING: Character.traits items may be modified by a receiver, resulting in
    unexpected behavior. Do not directly work on these objects; use
    Character.get_traits() instead."""

    name: str = Field(max_length=MAX_NAME_LEN)
    profile: Profile = Field(default_factory=Profile, repr=False)
    line: GameLine
    splat: Splat
    experience: Experience = Field(default_factory=Experience, repr=False)

    guild: int
    user: int

    health: str
    willpower: str
    grounding: Grounding

    traits: list[Trait] = Field(default_factory=list)

    @property
    def has_blood_pool(self) -> bool:
        """Whether the character is a vampire or a ghoul."""
        return self.splat in (Splat.GHOUL, Splat.VAMPIRE)

    def _all_traits(self) -> list[Trait]:
        """A copy of all the character's rollable traits, including innates."""
        innate = Trait.Category.INNATE
        blank = Trait.Subcategory.BLANK
        innates = [
            Trait(
                name="Willpower",
                rating=len(self.willpower),
                category=innate,
                subcategory=blank,
            ),
            Trait(
                name=self.grounding.path,
                rating=self.grounding.rating,
                category=innate,
                subcategory=blank,
            ),
        ]
        return self.traits + innates

    @before_event(Delete)
    async def prep_delete(self):
        """Special operations before deleting a character."""
        try:
            await self.delete_all_images(False)
        except errors.ApiError:
            pass

    def _get_tracker_count(self, tracker: Tracker, severity: Damage) -> int:
        """Get the number of boxes at the indicated damage level."""
        if tracker == Tracker.HEALTH:
            track = self.health
        else:
            track = self.willpower
        return track.count(severity.value)

    def increment_damage(self, tracker: Tracker, severity: Damage) -> str:
        """Increment the damage track. Sets and returns the new track."""
        count = self._get_tracker_count(tracker, severity)
        return self.set_damage(tracker, severity, count + 1)

    def decrement_damage(self, tracker: Tracker, severity: Damage) -> str:
        """Decrement the damage track. Sets and returns the new track."""
        count = self._get_tracker_count(tracker, severity)
        return self.set_damage(tracker, severity, max(count - 1, 0))

    def set_damage(self, tracker: Tracker, severity: Damage, count: int) -> str:
        """Set the tracker's new damage rating. Sets and returns the new track."""

        def _track(track: str, severity: Damage, count: int):
            """Inner function handles the actual work."""
            length = len(track)
            counter = Counter(list(track))
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

    def match_traits(self, search: str, exact=False) -> list[Trait.Selection]:
        """Match traits to user input. Used in rolls."""
        matches = []
        for trait in self._all_traits():
            matches.extend(trait.matching(search, exact))
        return matches

    @staticmethod
    def _trait_sort_key(t: Trait) -> str:
        """The key used for insorting traits. A default is provided so tests
        pass, but this method should be overridden by child classes."""
        return t.name.casefold()

    def add_trait(
        self,
        name: str,
        rating: int,
        category=Trait.Category.CUSTOM,
        subcategory=Trait.Subcategory.BLANK,
    ) -> Trait:
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

        new_trait = Trait(name=name, rating=rating, category=category, subcategory=subcategory)
        bisect.insort(self.traits, new_trait, key=self._trait_sort_key)

        return copy.deepcopy(new_trait)

    def update_trait(self, name: str, new_rating: int) -> Trait:
        """Update a trait.
        Args:
            name (str): The name of the Trait to update
            new_rating (int): The Trait's new rating

        Returns a copy of the updated Trait.
        Raises TraitNotFound.
        """
        trait_name = name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                trait.rating = new_rating
                return copy.deepcopy(trait)
        raise errors.TraitNotFound(self, name)

    def remove_trait(self, name: str) -> str:
        """Remove a trait.
        Args:
            trait_name (str): The name of the trait to remove

        Returns the trait's name, properly capitalized.
        Raises TraitNotFound.
        """
        trait_name = name.casefold()
        for i, trait in enumerate(self.traits):
            if trait.name.casefold() == trait_name:
                if trait.category == Trait.Category.CUSTOM:
                    del self.traits[i]
                else:
                    # Set core traits to 0 rather than remove them
                    trait.rating = 0
                return trait.name
        raise errors.TraitNotFound(self, name)

    def add_subtraits(self, name: str, subtraits: list[str] | str) -> tuple[Trait, list[str]]:
        """Add subtraits to a trait.
        Args:
            name (str): The exact name of the trait to add to
            subtraits (list[str]): The subtraits to add

        Subtraits may not be added to innates. If this is a CofD character,
        attributes may not accept subtraits.

        Returns: A copy of the trait with the subtraits added, and the set of
            the added subtraits.
        Raises: TraitNotFound if the character has no trait by that name."""
        trait_name = name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                if self.line == GameLine.COFD and trait.category == Trait.Category.ATTRIBUTE:
                    raise errors.InvalidTrait("Attributes can't have specialties in CofD.")

                before = set(trait.subtraits)
                trait.add_subtraits(subtraits)
                after = set(trait.subtraits)
                delta = sorted(after.symmetric_difference(before))

                return copy.deepcopy(trait), delta

        raise errors.TraitNotFound(self, name)

    def remove_subtraits(self, name: str, subtraits: list[str] | str) -> tuple[Trait, list[str]]:
        """Remove subtraits from a trait."""
        trait_name = name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                before = set(trait.subtraits)
                trait.remove_subtraits(subtraits)
                after = set(trait.subtraits)
                delta = sorted(after.symmetric_difference(before))

                return copy.deepcopy(trait), delta

        raise errors.TraitNotFound(self, name)

    # Image handling

    async def add_image(self, discord_url: str) -> str:
        """Upload a character image via URL. Premium feature."""
        image_url = await api.upload_faceclaim(self, discord_url)
        self.profile.add_image(image_url)
        await self.save_changes()

        return image_url

    async def delete_image(self, url: str):
        """Remove a profile image. Premium feature."""
        if await api.delete_single_faceclaim(url):
            self.profile.remove_image(url)
            await self.save_changes()

    async def delete_all_images(self, save_changes=True):
        """Delete all the character's images."""
        await api.delete_character_faceclaims(self)
        del self.profile.images[:]
        if save_changes:
            await self.save_changes()

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
        validate_on_save = True
