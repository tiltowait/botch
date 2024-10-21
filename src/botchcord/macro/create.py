"""Macro creation functions and utilities."""

import bot
import errors
from botchcord.haven import Haven
from botchcord.roll import RollParser
from botchcord.utils import CEmbed
from botchcord.utils.text import m
from core.characters import Character, Macro


async def create(
    ctx: bot.AppCtx,
    character: str | None,
    name: str,
    pool: str,
    diff: int,
    comment: str | None,
):
    """Create a macro and add it to the character."""
    # can_use_macro() is too complex for the @haven decorator
    try:
        haven = Haven(ctx, None, None, character, filter=lambda c: can_use_macro(c, pool))
        char = await haven.get_match()
        macro = create_macro(char, name, pool, diff, comment)
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
    """
    try:
        RollParser(pool, char).parse()
        return True
    except errors.TraitError:
        return False


def create_macro(char: Character, name: str, pool: str, diff: int, comment: str | None) -> Macro:
    """Create a macro."""
    rp = RollParser(pool, char).parse(use_key=True)
    return Macro(name=name, pool=rp.pool, difficulty=diff, rote=False, hunt=False, comment=comment)


def build_embed(bot: bot.BotchBot, char: Character, macro: Macro) -> CEmbed:
    """Create an embed describing the newly created macro."""
    pool = " ".join(map(str, macro.pool))
    lines = [
        f"**Name:** {macro.name}",
        f"**Pool:** {m(pool)}",
        f"**Difficulty:** {macro.difficulty}",
        f"**Comment:** {macro.comment}",
    ]
    embed = CEmbed(bot, char, title="Macro created", description="\n".join(lines))

    return embed
