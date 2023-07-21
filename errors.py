"""Shared Storyteller errors."""


class StorytellerError(Exception):
    """Base error class."""


class TraitError(StorytellerError):
    """Base trait-related errors."""


class TraitNotFound(TraitError):
    """Raised when a user specifies a nonexistent trait."""

    def __init__(self, character, trait: str):
        super().__init__()
        self.name = character.name
        self.trait = trait

    def __str__(self) -> str:
        return f"**{self.name}** has no trait named `{self.trait}`."


class TraitAlreadyExists(TraitError):
    """Raised when the user attempts to add an extant trait."""
