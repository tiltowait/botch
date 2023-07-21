"""Shared Storyteller errors."""


class StorytellerError(Exception):
    """Base error class."""


class TraitNotFound(StorytellerError):
    """Raised when a trait isn't found."""


class TraitAlreadyExists(StorytellerError):
    """Raised when the user attempts to add an extant trait."""
