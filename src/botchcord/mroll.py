"""Macro rolls."""

import bot
import botchcord
from botchcord.haven import Haven
from core.characters import Character


async def mroll(
    ctx: bot.AppCtx,
    macro_name: str,
    diff_override: int | None,
    comment_override: str | None,
    character: str | None,
):
    """Perform a macro roll."""
    haven = Haven(ctx, None, None, character, filter=lambda c: has_macro(c, macro_name))

    char = await haven.get_match()
    macro = char.find_macro(macro_name)
    assert macro is not None  # Guaranteed

    pool = " ".join(map(str, macro.pool))
    difficulty = diff_override or macro.difficulty
    comment = comment_override or macro.comment

    await botchcord.roll.roll(ctx, pool, difficulty, None, comment, char)


def has_macro(char: Character, macro_name: str):
    """Returns True if the character has the given macro."""
    return char.find_macro(macro_name) is not None
