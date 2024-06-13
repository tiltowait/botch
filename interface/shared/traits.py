"""Character traits command interface."""


import discord
from discord import option
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

    @traits.command()
    @option("traits", description="The traits to assign. Ex: Foo=1 Bar=2", required=True)
    @options.character("The character to modify")
    async def assign(
        self,
        ctx: discord.ApplicationContext,
        traits: str,
        character: str,
    ):
        """Assign new traits or update existing ones."""
        await botchcord.character.traits.assign(ctx, character, traits)

    @traits.command()
    @option("traits", description="The traits to remove (separate with spaces)", required=True)
    @options.character("The character to modify")
    async def remove(self, ctx: discord.ApplicationContext, traits: str, character: str):
        """Remove traits from a character."""
        await botchcord.character.traits.remove(ctx, character, traits)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(TraitsCog(bot))
