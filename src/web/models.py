"""Web request/response models."""

from typing import Annotated

from pydantic import BaseModel, Field

from core.characters.factory import Schema as TraitSchema


class WizardSchema(BaseModel):
    """The response body used by the web-based wizard."""

    # We have to use Annotated so Pyright stops complaining
    guild_name: Annotated[str, Field(alias="guildName")]
    user_id: int
    traits: TraitSchema

    @classmethod
    def create(cls, guild_name: str, user_id: int, schema_file: str):
        """Create a WizardSchema.

        Args:
            guild_name (str): The name of the guild the character will be
                created on.
            schema_file (str): The location of the schema file to load.

        Returns: The generated WizardSchema.
        Raises:
            ValidationError if unable to load the schema.
        """
        trait_schema = TraitSchema.load(schema_file)
        return cls(guild_name=guild_name, user_id=user_id, traits=trait_schema)

    class Config:
        populate_by_name = True
