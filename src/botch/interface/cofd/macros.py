"""Macro command cog."""

import discord
from discord import SlashCommandGroup, option, slash_command

from botch import botchcord
from botch.bot import AppCtx, BotchBot
from botch.botchcord import options
from botch.config import DOCS_URL
from botch.interface import BotchCog


class MacrosCog(BotchCog, name="Macros"):
    """Macros are shortcuts for your most commonly used rolls. For instance,\
    if you often roll `Wits + Composure`, you can create a macro called\
    `perception` that rolls those traits. You can also specify a comment to\
    apply to all invocations, set the `rote` quality, and give it 9-again or\
    8-again.

    Macros are per-character, so you can have multiple macros by the same\
    name if they're all under different characters. However, if you use unique\
    names, then `BOT`'s automatic filtering system won't prompt you to ask\
    which character is rolling."""

    macro = SlashCommandGroup(
        "macro",
        "Macro commands",
        contexts={discord.InteractionContextType.guild},
    )

    def __init__(self, bot: BotchBot):
        self.bot = bot
        self.docs_url = f"{DOCS_URL}/reference/macros"

    @macro.command(name="create")
    @option("name", description="The new macro's name")
    @option("pool", description="The dice pool for the macro to use")
    @option("again", description="The number to explode at", choices=[10, 9, 8], default=10)
    @option("rote", description="Whether to always apply the Rote quality", default=False)
    @option("comment", description="A comment to apply by default when rolling", required=False)
    @options.character("The character receiving the macro")
    async def macro_create(
        self,
        ctx: AppCtx,
        name: str,
        pool: str,
        again: int,
        rote: bool,
        comment: str,
        character: str,
    ):
        """Create a macro."""
        await botchcord.macro.create(ctx, character, name, pool, again, comment, rote)

    @macro.command(name="list")
    @options.character("The character whose macros to display")
    async def display_macros(self, ctx: AppCtx, character: str):
        """Display a character's macros."""
        await botchcord.macro.display(ctx, character)

    @macro.command(name="delete")
    @option("macro_name", description="The name of the macro to delete")
    @options.character("The character with the macro to delete")
    async def delete_macro(self, ctx: AppCtx, macro_name: str, character: str):
        """Delete a macro from a character."""
        await botchcord.macro.delete(ctx, character, macro_name)

    @slash_command()
    @option("name", description="The name of the macro to roll")
    @option(
        "again",
        description="Override the explosion threshold",
        choices=[10, 9, 8],
        required=False,
    )
    @option("rote", description="Override the Rote quality", default=False)
    @option(
        "use_wp",
        description="Override the macro to use WP",
        default=False,
    )
    @option("autos", description="Add automatic successes", choices=list(range(11)), default=0)
    @option("comment", description="Override the default comment", required=False)
    @options.character("The character performing the roll")
    async def mroll(
        self,
        ctx: AppCtx,
        name: str,
        again: int,
        rote: bool,
        use_wp: bool,
        autos: int,
        comment: str,
        character: str,
    ):
        """Roll using a macro."""
        await botchcord.mroll(ctx, name, again, use_wp, rote, comment, character, autos=autos)


def setup(bot: BotchBot):
    bot.add_cog(MacrosCog(bot))
