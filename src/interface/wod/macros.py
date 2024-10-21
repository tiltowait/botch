"""Macro command cog."""

from discord import SlashCommandGroup, option, slash_command
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options


class MacrosCog(Cog, name="Macro commands"):
    """Macro creation, review, updating, and deletion."""

    macro = SlashCommandGroup("macro", "Macro commands")

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
    @options.character("The character performing the roll")
    async def mroll(self, ctx: AppCtx, name: str, difficulty: int, comment: str, character: str):
        """Roll using a macro."""
        await botchcord.mroll(ctx, name, difficulty, comment, character)


def setup(bot: BotchBot):
    bot.add_cog(MacrosCog(bot))
