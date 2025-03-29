"""Character traits command interface."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.ext.commands import user_command

from botch import botchcord
from botch.bot import AppCtx, BotchBot
from botch.botchcord import options
from botch.config import DOCS_URL
from botch.interface import BotchCog


class TraitsCog(BotchCog, name="Character traits and specialties"):
    """Traits are Attributes, Skills, Disciplines, and anything else you might\
    roll as part of a dice pool. In addition to the standard traits all\
    characters have, such as `Strength`, `Intelligence`, `Athletics`, etc.,\
    you can create any number of custom traits.

    Traits can also have specialties, which can be rolled using the syntax,\
    `Trait.Specialty` (e.g. `Performance.Dance`). `BOT` places no restrictions\
    on the number of specialties a trait can have, though different game lines\
    do."""

    traits = SlashCommandGroup(
        "traits",
        "Character trait commands",
        contexts={discord.InteractionContextType.guild},
    )
    specialties = SlashCommandGroup(
        "specialties",
        "Character specialties commands",
        contexts={discord.InteractionContextType.guild},
    )

    def __init__(self, bot: BotchBot):
        self.bot = bot
        self.docs_url = f"{DOCS_URL}/reference/traits"

    @user_command(name="View: Traits")
    async def user_characters(self, ctx: AppCtx, member: discord.Member):
        """Display the stats for a user's character."""
        await botchcord.character.traits.display(ctx, "", owner=member)

    @traits.command(name="list")
    @options.character("The character to display")
    @options.owner()
    async def display(self, ctx: AppCtx, character: str, owner: discord.Member):
        """Display one of your character's traits."""
        await botchcord.character.traits.display(ctx, character, owner=owner)

    @traits.command()
    @option("traits", description="The traits to assign. Ex: Foo=1; Bar=2", required=True)
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
    @option("traits", description="The traits to remove (separate with semicolons)", required=True)
    @options.character("The character to modify")
    async def remove(self, ctx: AppCtx, traits: str, character: str):
        """Remove traits from one of your characters."""
        await botchcord.character.traits.remove(ctx, character, traits)

    @specialties.command(name="assign")
    @option(
        "specialties",
        description="The trait + specialties to add. Ex: Brawl=Kindred,Kine",
        required=True,
    )
    @options.character("The character receiving the specialties")
    async def assign_specialties(self, ctx: AppCtx, specialties: str, character: str):
        """Assign specialties to one of your character's trait(s)."""
        await botchcord.character.specialties.assign(ctx, character, specialties)

    @specialties.command(name="remove")
    @option(
        "specialties",
        description="The trait + specialties to remove. Ex: Brawl=Kindred,Kine",
        required=True,
    )
    @options.character("The character losing the specialties")
    async def remove_specialties(self, ctx: AppCtx, specialties: str, character: str):
        """Remove specialties from one of your character's trait(s)."""
        await botchcord.character.specialties.remove(ctx, character, specialties)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(TraitsCog(bot))
