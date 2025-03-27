"""Macro deletion."""

from botch import bot, errors
from botch.botchcord.haven import Haven
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import m
from botch.config import GAME_LINE


async def delete(ctx: bot.AppCtx, character: str | None, macro_name: str):
    """Delete the named macro from the character."""
    try:
        haven = Haven(
            ctx, GAME_LINE, None, character, None, filter=lambda c: c.has_macro(macro_name)
        )
        char = await haven.get_match()
        char.remove_macro(macro_name)
        embed = CEmbed(
            ctx.bot,
            char,
            title="Macro deleted",
            description=f"Deleted **{char.name}'s** {m(macro_name)} macro.",
        )
        await ctx.respond(embed=embed, ephemeral=True)
        await char.save()

    except errors.HavenError:
        await ctx.send_error("Error", f"Macro {m(macro_name)} not found.")
