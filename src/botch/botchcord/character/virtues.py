"""Character Virtue (WoD) commands."""

from enum import Enum, auto

from botch.bot import AppCtx, BotchBot
from botch.botchcord.haven import haven
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import b
from botch.core.characters import Character, Trait
from botch.core.characters.wod import Mortal  # Mortal is the base class for all WoD characters
from botch.errors import CharacterError, TraitError


class Virtue(Enum):
    MORALITY = auto()
    RESTRAINT = auto()
    COURAGE = auto()

    @classmethod
    def category(cls, virtue: str) -> "Virtue":
        """The category the Virtue belongs to."""
        match virtue.lower():
            case "conscience" | "conviction":
                return cls.MORALITY
            case "selfcontrol" | "instinct":
                return cls.RESTRAINT
            case "courage":
                return cls.COURAGE
            case _:
                raise TraitError(f"Unknown Virtue: {virtue}")


@haven()
async def update(ctx: AppCtx, character: Character, virtue_name: str, rating: int):
    """Update the Virtue, renaming or creating it if possible."""
    if not isinstance(character, Mortal):
        raise CharacterError(f"{b(character.name)} is not a World of Darkness character.")

    virtue = find_virtue(character.virtues, virtue_name)
    if virtue is not None:
        virtue.name = virtue_name
        virtue.rating = rating
    else:
        virtue = Trait(
            name=virtue_name,
            rating=rating,
            category=Trait.Category.SPECIAL,
            subcategory=Trait.Subcategory.VIRTUES,
        )
        match Virtue.category(virtue_name):
            case Virtue.MORALITY:
                index = 0
            case Virtue.RESTRAINT:
                index = 1
            case Virtue.COURAGE:
                index = 2

        character.virtues.insert(index, virtue)

    embed = build_embed(ctx.bot, character)
    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def build_embed(bot: BotchBot, char: Mortal) -> CEmbed:
    """Build the Virtues embed."""
    desc = "\n".join(map(lambda v: f"**{v.name}:** {v.rating}", char.virtues))
    return CEmbed(bot, char, title="Virtues Updated", description=desc)


def find_virtue(virtues: list[Trait], name: str) -> Trait | None:
    """Find the named Virtue, or its reciprocal. For instance, if Conscience is
    given, but Conviction is present, it will return Conviction.

    Returns: The Virtue.
    Raises TraitNotFound if the Virtue doesn't exist."""
    category = Virtue.category(name)
    for virtue in virtues:
        if Virtue.category(virtue.name) == category:
            return virtue

    return None
