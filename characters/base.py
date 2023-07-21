"""Base character models used by all splats. Some splats have their own
subclasses."""

import bisect
import copy
import itertools
from collections import Counter, namedtuple
from enum import StrEnum

import pymongo
from beanie import Document
from pydantic import BaseModel, Field

import errors


class Damage(StrEnum):
    NONE = "."
    BASHING = "/"
    LETHAL = "X"
    AGGRAVATED = "*"


class Splat(StrEnum):
    VTM = "vtm"
    MTAS = "mtaw"


class Grounding(BaseModel):
    """Humanity, Paths of Enlightenment, Integrity, etc."""

    path: str
    rating: int


class Tracker(StrEnum):
    HEALTH = "health"
    WILLPOWER = "willpower"


class Trait(BaseModel):
    """A trait represents an Attribute, Ability, Discipline, etc."""

    _DELIMITER = "."

    class Category(StrEnum):
        ATTRIBUTE = "attribute"
        ABILITY = "ability"
        SPECIAL = "special"
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
        category: str  # The Trait.Category. Must be str due to placement here

    name: str
    rating: int
    category: Category
    subtraits: list[str] = Field(default_factory=list)

    def add_subtraits(self, subtraits: str | list[str]):
        """Add subtraits to the trait."""
        if isinstance(subtraits, str):
            subtraits = {subtraits}
        else:
            subtraits = set(subtraits)

        for subtrait in subtraits:
            if subtrait.casefold() not in map(str.casefold, self.subtraits):
                self.subtraits.append(subtrait)

        self.subtraits.sort()

    def remove_subtraits(self, subtraits: str | list[str]):
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
        """Returns the fully qualified name if a string matches, or None."""
        matches = []
        if groups := self.expanding(identifier, exact, False):
            # The expanded values are sorted alphabetically, and we need
            # that to match our input for testing exactness
            tokens = identifier.split(Trait._DELIMITER)
            tokens = [tokens[0]] + sorted(tokens[1:])
            normalized = Trait._DELIMITER.join(tokens).casefold()

            for expanded in groups:
                full_name = self.name
                if expanded[1:]:
                    # Add the subtraits
                    full_name += f" ({', '.join(expanded[1:])})"

                key = Trait._DELIMITER.join(expanded)

                matches.append(
                    Trait.Selection(
                        name=full_name,
                        rating=self.rating,
                        exact=normalized == key.casefold(),
                        key=key,
                        category=self.category,
                    )
                )
        return matches

    def expanding(self, identifier: str, exact: bool, join=True) -> list[str | list[str]]:
        """Expand the user's input to full skill:spec names. If join is False, return a list."""
        tokens = [token.casefold() for token in identifier.split(Trait._DELIMITER)]

        # The "comp" lambda takes a token and an instance var
        if exact:
            comp = lambda t, i: t == i.casefold()
        else:
            comp = lambda t, i: i.casefold().startswith(t)

        if comp(tokens[0], self.name):
            # A token might match multiple specs in the same skill. Therefore,
            # we need to make a list of all matching specs. We don't need to
            # track ratings, however, as we can just sum the spec counts at the
            # end.
            spec_groups = []
            for token in tokens[1:]:
                found_specs = []
                for subtrait in self.subtraits:
                    if comp(token, subtrait):
                        found_specs.append(subtrait)
                spec_groups.append(found_specs)

            # If no subtraits were given, then spec_groups is empty. If
            # subtraits were given but not found, then we have [[]], which
            # will eventually return [].
            #
            # This also holds true if multiple specs are given and only one
            # fails to match (e.g. [["Kindred"], []]). It works because
            # itertools.product() will return an empty list if one of its
            # arguments is itself an empty list. Therefore, we don't need any
            # "if not group: return None" patterns in this next block.

            if spec_groups:
                matches = []
                if len(spec_groups) > 1:
                    # Multiple matching specs per token; get all combinations:
                    #     [[1, 2], [3]] -> [(1, 3), (2, 3)]
                    spec_groups = itertools.product(*spec_groups)
                else:
                    # Zero or one match; golden path
                    spec_groups = spec_groups[0]

                seen_groups = []
                for group in spec_groups:
                    if isinstance(group, str):
                        group = [group]
                    if len(set(group)) < len(group):
                        # This group has at least one duplicate spec; skip
                        continue

                    group = set(group)
                    if group in seen_groups:
                        # Prevent (A, B) and (B, A) from both showing in the results
                        continue

                    matches.append([self.name] + sorted(group))
            else:
                matches = [[self.name]]

            if join:
                return [Trait._DELIMITER.join(match) for match in matches]
            return matches

        # No matches
        return []


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

    def update_trait(self, trait_name: str, new_rating: int) -> str:
        """Update a trait.
        Args:
            trait_name (str): The name of the trait to update
            new_rating (int): The trait's new rating

        Returns the trait's name, properly capitalized.
        Raises TraitNotFound.
        """
        trait_name = trait_name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                trait.rating = new_rating
                return trait.name
        raise errors.TraitNotFound(self, trait_name)

    def remove_trait(self, trait_name: str) -> str:
        """Remove a trait.
        Args:
            trait_name (str): The name of the trait to remove

        Returns the trait's name, properly capitalized.
        Raises TraitNotFound.
        """
        trait_name = trait_name.casefold()
        for i, trait in enumerate(self.traits):
            if trait.name.casefold() == trait_name:
                del self.traits[i]
                return trait.name
        raise errors.TraitNotFound(self, trait_name)

    def add_specialties(
        self, trait_name: str, subtraits: list[str] | str
    ) -> tuple[Trait, set[str]]:
        """Add specialties to a trait.
        Args:
            trait_name (str): The name of the trait to add to
            subtraits (list[str]): The specialties to add.

        Returns: A copy of the Trait with specialties added, and the set of
            the added specialties.
        Raises TraitNotFound."""
        raise NotImplementedError("This function is not implemented in the base class.")

    def add_subtraits(self, trait_name: str, subtraits: list[str] | str) -> tuple[Trait, list[str]]:
        """Add subtraits to a trait.
        Args:
            trait_name (str): The exact name of the trait to add to
            subtraits (list[str]): The subtraits to add

        Returns: A copy of the trait with the subtraits added, and the set of
            the added subtraits.
        Raises: TraitNotFound if the character has no trait by that name."""
        trait_name = trait_name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                before = set(trait.subtraits)
                trait.add_subtraits(subtraits)
                after = set(trait.subtraits)
                delta = sorted(after.symmetric_difference(before))

                return copy.deepcopy(trait), delta

        raise errors.TraitNotFound(self, trait_name)

    def remove_subtraits(
        self, trait_name: str, subtraits: list[str] | str
    ) -> tuple[Trait, list[str]]:
        """Remove subtraits from a trait."""
        trait_name = trait_name.casefold()
        for trait in self.traits:
            if trait.name.casefold() == trait_name:
                before = set(trait.subtraits)
                trait.remove_subtraits(subtraits)
                after = set(trait.subtraits)
                delta = sorted(after.symmetric_difference(before))

                return copy.deepcopy(trait), delta

        raise errors.TraitNotFound(self, trait_name)

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
