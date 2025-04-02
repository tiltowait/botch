"""Macro creation functions and utilities."""

from botch import bot, errors
from botch.botchcord.haven import Haven
from botch.botchcord.macro.display import create_macro_entry
from botch.botchcord.roll import RollParser
from botch.botchcord.utils import CEmbed
from botch.config import GAME_LINE
from botch.core.characters import Character, Macro


async def create(
    ctx: bot.AppCtx,
    character: str | None,
    name: str,
    pool: str,
    diff: int,
    comment: str | None,
    rote=False,
    blessed=False,
    blighted=False,
):
    """Create a macro and add it to the character."""
    # can_use_macro() is too complex for the @haven decorator
    try:
        haven = Haven(
            ctx, GAME_LINE, None, character, None, filter=lambda c: can_use_macro(c, pool)
        )
        char = await haven.get_match()
        macro = create_macro(char, name, pool, diff, comment, rote, blessed, blighted)
        char.add_macro(macro)

        embed = build_embed(ctx.bot, char, macro)
        await ctx.respond(embed=embed, ephemeral=True)
        await char.save()

    except errors.BotchError as err:
        await ctx.send_error("Unable to create macro", str(err))


def can_use_macro(char: Character, pool: str) -> bool:
    """Whether the character can create a given macro.

    Args:
        char (Character): The character to test
        pool (str): The macro's pool

    Returns:
        True if the character can roll the pool
        False if it cannot
    Raises: InvalidSyntax if the pool syntax is invalid. This differentiates
        characters who can't do the roll vs a roll that is ALWAYS invalid.
    """
    try:
        RollParser(pool, char).parse()
        return True
    except errors.TraitError:
        return False


def create_macro(
    char: Character,
    name: str,
    pool: str,
    diff: int,
    comment: str | None,
    rote=False,
    blessed=False,
    blighted=False,
) -> Macro:
    """Create a macro."""
    rpp = RollParser(pool, char).parse()
    rpk = RollParser(pool, char).parse(use_key=True)
    return Macro(
        name=name,
        pool=rpp.pool,
        keys=rpk.pool,
        target=diff,
        rote=rote,
        blessed=blessed,
        blighted=blighted,
        hunt=False,
        comment=comment,
    )


def build_embed(bot: bot.BotchBot, char: Character, macro: Macro) -> CEmbed:
    """Create an embed describing the newly created macro."""
    description = create_macro_entry(macro)
    embed = CEmbed(bot, char, title="Macro created", description=description)

    return embed
