"""Character traits command interface."""


import discord
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

import botchcord
from bot import BotchBot
from botchcord import options


class TraitsCog(Cog, name="Character trait commands"):
    traits = SlashCommandGroup("traits", "Character trait commands")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @traits.command(name="list")
    @options.character("The character to display")
    async def display(self, ctx: discord.ApplicationContext, character: str):
        """Display a character's traits."""
        await botchcord.character.traits.display(ctx, character)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(TraitsCog(bot))
