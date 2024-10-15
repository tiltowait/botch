"""Character traits command interface."""

from discord import option
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options


class TraitsCog(Cog, name="Character trait/specialty commands"):
    traits = SlashCommandGroup("traits", "Character trait commands")
    specialties = SlashCommandGroup("specialties", "Character specialties commands")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @traits.command(name="list")
    @options.character("The character to display")
    async def display(self, ctx: AppCtx, character: str):
        """Display a character's traits."""
        await botchcord.character.traits.display(ctx, character)

    @traits.command()
    @option("traits", description="The traits to assign. Ex: Foo=1 Bar=2", required=True)
    @options.character("The character to modify")
    async def assign(
        self,
        ctx: AppCtx,
        traits: str,
        character: str,
    ):
        """Assign new traits or update existing ones."""
        await botchcord.character.traits.assign(ctx, character, traits)

    @traits.command()
    @option("traits", description="The traits to remove (separate with spaces)", required=True)
    @options.character("The character to modify")
    async def remove(self, ctx: AppCtx, traits: str, character: str):
        """Remove traits from a character."""
        await botchcord.character.traits.remove(ctx, character, traits)

    @specialties.command(name="assign")
    @option(
        "specialties",
        description="The trait + specialties to add. Ex: Brawl=Kindred,Kine",
        required=True,
    )
    @options.character("The character receiving the specialties")
    async def assign_specialties(self, ctx: AppCtx, traits: str, character: str):
        """Assign specialties to a character's trait(s)."""
        await botchcord.character.specialties.assign(ctx, character, traits)

    @specialties.command(name="remove")
    @option(
        "specialties",
        description="The trait + specialties to remove. Ex: Brawl=Kindred,Kine",
        required=True,
    )
    @options.character("The character losing the specialties")
    async def remove_specialties(self, ctx: AppCtx, traits: str, character: str):
        """Remove specialties from a character's trait(s)."""
        await botchcord.character.specialties.remove(ctx, character, traits)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(TraitsCog(bot))
