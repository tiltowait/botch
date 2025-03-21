"""Character creation utilities."""

import json
from collections import OrderedDict, deque
from pathlib import Path
from typing import Any

from botch import errors, utils
from botch.core.characters import Character, GameLine, Splat
from botch.core.characters.factory.schema import Schema


class Factory:
    """Factory for creating characters based on JSON schema."""

    def __init__(
        self,
        line: GameLine,
        splat: Splat,
        char_class: type[Character],
        args: dict[str, Any],
        schema_filter="*.json",
    ):
        self.line = line
        self.splat = splat
        self.char_class = char_class
        self.schema_filter = schema_filter
        self.schema = self.load_schema()
        self.traits = deque(self.schema.all_traits)
        self.assignments: dict[str, int] = OrderedDict()
        self.args = args

        for k, v in self.args.items():
            if isinstance(v, str):
                self.args[k] = utils.normalize_text(v)

    @property
    def remaining(self) -> int:
        """The number of traits yet to be assigned."""
        return len(self.traits)

    def load_schema(self) -> Schema:
        """Loads the schema file and sets it in self.schema."""
        current_dir = Path(__file__).parent
        schemas_dir = current_dir.parent / "schemas" / self.line
        for schema_file in schemas_dir.glob(self.schema_filter):
            schema = self._load_json(schema_file)
            if self.splat in schema.get("splats", []):
                return Schema(**schema)

        raise errors.MissingSchema(
            f"Unable to locate character schema for {self.line} -> {self.splat}."
        )

    @staticmethod
    def _load_json(file_path: Path) -> dict[str, Any]:
        """Helper method to load a JSON file."""
        with file_path.open() as f:
            return json.load(f)

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

        # Remove NoneType values, since no class has them
        char_args = {k: v for k, v in self.args.items() if v is not None}
        character = self.char_class(**char_args)

        for trait, rating in self.assignments.items():
            cat = self.schema.category(trait)
            sub = self.schema.subcategory(trait)
            character.add_trait(trait, rating, cat, sub)

        return character
