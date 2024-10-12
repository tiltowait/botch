"""General character command interface."""


import discord
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

import botchcord
from bot import BotchBot
from botchcord import options


class CharactersCog(Cog, name="General character commands"):
    character = SlashCommandGroup("character", "General character commands")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @character.command()
    @options.character("The character to display", required=False)
    async def display(self, ctx: discord.ApplicationContext, character: str):
        """Display a character."""
        await botchcord.character.display(ctx, character)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(CharactersCog(bot))
