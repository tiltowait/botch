"""Macro command cog."""

import discord
from discord import SlashCommandGroup, option, slash_command
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options


class MacrosCog(Cog, name="Macro commands"):
    """Macro creation, review, updating, and deletion."""

    macro = SlashCommandGroup(
        "macro",
        "Macro commands",
        contexts={discord.InteractionContextType.guild},
    )

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @macro.command(name="create")
    @option("name", description="The new macro's name")
    @option("pool", description="The dice pool for the macro to use")
    @options.promoted_choice(
        "difficulty", "The macro's default difficulty", start=2, end=10, first=6
    )
    @option("comment", description="A comment to apply by default when rolling", required=False)
    @options.character("The character receiving the macro")
    async def macro_create(
        self,
        ctx: AppCtx,
        name: str,
        pool: str,
        difficulty: int,
        comment: str,
        character: str,
    ):
        """Create a macro."""
        await botchcord.macro.create(ctx, character, name, pool, difficulty, comment)

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
    @options.promoted_choice(
        "difficulty",
        "Override the default difficulty",
        start=2,
        end=10,
        first=6,
        required=False,
    )
    @option("comment", description="Override the default comment", required=False)
    @option(
        "use_wp",
        description="Override the macro to use WP",
        default=False,
    )
    @options.character("The character performing the roll")
    async def mroll(
        self,
        ctx: AppCtx,
        name: str,
        difficulty: int,
        comment: str,
        use_wp: bool,
        character: str,
    ):
        """Roll using a macro."""
        await botchcord.mroll(ctx, name, difficulty, comment, character, use_wp)


def setup(bot: BotchBot):
    bot.add_cog(MacrosCog(bot))
