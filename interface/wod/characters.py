"""General character command interface."""


from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options


class CharactersCog(Cog, name="General character commands"):
    character = SlashCommandGroup("character", "General character commands")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @character.command()
    @options.character("The character to display")
    async def display(self, ctx: AppCtx, character: str):
        """Display a character."""
        await botchcord.character.display(ctx, character)

    @character.command()
    @options.character("The character to delete", required=True)
    async def delete(self, ctx: AppCtx, character: str):
        """Delete a character."""
        await botchcord.character.delete(ctx, character)

    @character.command()
    @options.character("The character to adjust")
    async def adjust(self, ctx: AppCtx, character: str):
        """Adjust character stats."""
        await botchcord.character.adjust(ctx, character)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(CharactersCog(bot))
