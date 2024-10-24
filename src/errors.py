"""Shared Botch errors."""


class BotchError(Exception):
    """Base error class."""


class NotReady(Exception):
    """Raised when the bot isn't ready yet."""


class NotPremium(Exception):
    """Raised when the user isn't a premium supporter."""


class EmojiNotFound(Exception):
    """Raised when an emoji isn't found."""


class CharacterError(BotchError):
    """Base class for character errors."""


class CharacterAlreadyExists(CharacterError):
    """Raised if the user tries to create a character that already exists."""


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
        match_block = "```\n" + "\n".join(self.matches) + "\n```"
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


class CharacterIneligible(HavenError):
    """Raised when the specified character doesn't match the filtering criteria."""


class NoCharacterSelected(HavenError):
    """Raised when a character isn't selected."""


class MacroError(BotchError):
    """Base macro error class."""


class MacroNotFound(MacroError):
    """Raised if the user tries to delete a non-existent macro."""


class MacroAlreadyExists(MacroError):
    """Raised if the user tries to add a macro by an existing name."""
