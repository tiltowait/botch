"""Character creation utilities."""

import glob
import json
from collections import OrderedDict, deque
from typing import Any

import errors
import utils
from botch.characters import Character, GameLine, Splat


class Factory:
    """Factory for creating characters based on JSON schema."""

    def __init__(self, line: GameLine, splat: Splat, char_class: Character, args: dict):
        self.line = line
        self.splat = splat
        self.char_class = char_class
        self.schema = self.load_schema()
        self.categories = self.gather_traits()
        self.traits = deque(self.categories.keys())
        self.assignments = OrderedDict()
        self.args = args

        for k, v in self.args.items():
            if isinstance(v, str):
                self.args[k] = utils.normalize_text(v)
        from pprint import pprint

        pprint(self.args)

    @property
    def remaining(self) -> int:
        """The number of traits yet to be assigned."""
        return len(self.traits)

    def load_schema(self) -> dict[str, Any]:
        """Loads the schema file and sets it in self.schema."""
        path = f"./botch/characters/schemas/{self.line}/*"
        for schema_file in glob.glob(path):
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
                if self.splat in schema["splats"]:
                    return schema

        raise errors.MissingSchema(
            f"Unable to locate character schema for {self.line} -> {self.splat}."
        )

    def gather_traits(self) -> OrderedDict[str, str]:
        """Gathers all the traits into a dictionary of trait: type."""

        def _prep(key: str) -> OrderedDict:
            o = OrderedDict()
            for section in self.schema[key]:
                for trait in section["traits"]:
                    o[trait] = key
            return o

        traits = OrderedDict()
        traits.update(_prep("attribute"))
        traits.update(_prep("ability"))

        if special := self.schema.get("special"):
            for k, v in special.items():
                for trait in v["traits"]:
                    traits[trait] = k

        return traits

    def next_trait(self) -> str | None:
        """Get the next trait, if it exists."""
        if self.traits:
            return self.traits[0]
        return None

    def peek_last(self) -> tuple[str, int] | None:
        """Get the last-assigned trait and its rating, if any."""
        if not self.assignments:
            return None
        return next(reversed(self.assignments.items()))

    def assign_next(self, rating: int) -> str | None:
        """Assign a value to the next trait and return the next trait."""
        trait = self.traits.popleft()
        self.assignments[trait] = rating

        return self.next_trait()

    def create(self) -> Character:
        """Create the character. It is not saved to the database!"""
        if self.traits:
            raise errors.Unfinished(f"{self.args['name']} is not yet finished.")

        character = self.char_class(**self.args)
        for trait, rating in self.assignments.items():
            character.add_trait(trait, rating, self.categories[trait])

        return character
