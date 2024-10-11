"""Shared Botch errors."""


class BotchError(Exception):
    """Base error class."""


class EmojiNotFound(Exception):
    """Raised when an emoji isn't found."""


class CharacterError(BotchError):
    """Base class for character errors."""


class CharacterTemplateNotFound(CharacterError):
    """A supplied game line or splat is not found."""


class CharacterNotFound(CharacterError):
    """Raised when a character isn't found."""


class Unfinished(CharacterError):
    """Raised when character is created prematurely."""


class MissingSchema(BotchError):
    """Raised when a schema can't be found for a given character type."""


class ApiError(BotchError):
    """An exception raised when there's an error with the API."""


class InvalidSyntax(BotchError):
    """Raised when invalid syntax is given."""


class RollError(BotchError):
    """Base roll error class."""


class MissingGameLine(RollError):
    """The roller is unable to determine which game line it's using."""


class NeedsCharacter(RollError):
    """Raised when a roll needs a character."""


class TraitError(BotchError):
    """Base trait-related errors."""


class AmbiguousTraitError(TraitError):
    """Raised when multiple traits are found."""

    def __init__(self, needle, matches):
        super().__init__()
        self.needle = needle
        self.matches = matches

    def __str__(self) -> str:
        match_block = "```" + "\n".join(self.matches) + "```"
        return f"`{self.needle}` is amgiguous. Did you mean: {match_block}"


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


class InvalidTrait(TraitError):
    """Raised when the wrong trait is chosen for an action."""


class HavenError(BotchError):
    """Base error class for Haven errors."""


class NoMatchingCharacter(HavenError):
    """Raised when a character can't be matched."""


class NoCharacterSelected(HavenError):
    """Raised when a character isn't selected."""
