"""Macro rolls."""

import bot
import botchcord
import errors
from botchcord.haven import Haven
from core.characters import Character


async def mroll(
    ctx: bot.AppCtx,
    macro_name: str,
    diff_override: int | None,
    comment_override: str | None,
    character: str | None,
    use_wp=False,
):
    """Perform a macro roll.

    The user can override the default difficulty with diff_override,
    and the default comment with comment_override."""
    haven = Haven(ctx, None, None, character, filter=lambda c: has_macro(c, macro_name))

    char = await haven.get_match()
    macro = char.find_macro(macro_name)
    assert macro is not None  # Guaranteed

    difficulty = diff_override or macro.difficulty
    comment = comment_override or macro.comment

    try:
        await botchcord.roll.roll(ctx, macro.key_str, difficulty, None, comment, char, use_wp)
    except errors.RollError:
        await ctx.send_error(
            "Error",
            "Unable to roll `{pool}`. Maybe you deleted one of the traits?",
        )


def has_macro(char: Character, macro_name: str):
    """Returns True if the character has the given macro."""
    return char.find_macro(macro_name) is not None
