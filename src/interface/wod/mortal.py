"""Mortal commands."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

from bot import BotchBot
from botchcord.character.creation import wod
from botchcord.options import promoted_choice
from config import MAX_NAME_LEN
from core.characters import Splat


class MortalCog(Cog, name="WoD Mortal Commands"):
    """The mortal cog contains commands specific to VtM mortals."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    mortal = SlashCommandGroup("mortal", "Mortal-specific commands")

    @mortal.command(name="create")
    @option("name", description="The new mortal's name", max_length=MAX_NAME_LEN)
    @promoted_choice("health", "The number of health levels", start=1, end=10, first=7)
    @promoted_choice("willpower", "The willpower rating", start=1, end=10)
    @option("path", description="The character's path (e.g. Humanity)")
    @promoted_choice("path_rating", "The character's path rating", start=0, end=10)
    @option(
        "integrity",
        description="The name of the integrity virtue",
        choices=["Conscience", "Conviction"],
    )
    @promoted_choice("integrity_rating", "The rating of the integrity virtue", start=0, end=5)
    @option(
        "control",
        description="The name of the control virtue",
        choices=["SelfControl", "Instincts"],
    )
    @promoted_choice("control_rating", "The rating of the control virtue", start=0, end=5)
    @promoted_choice("Courage", "The courage virtue rating", start=0, end=5)
    @option(
        "max_trait",
        description="Override the generational trait maximum",
        min_value=1,
        required=False,
    )
    async def create_mortal(
        self,
        ctx: discord.ApplicationContext,
        name: str,
        health: int,
        willpower: int,
        path: str,
        path_rating: int,
        integrity: str,
        integrity_rating: int,
        control: str,
        control_rating: int,
        courage: int,
        max_trait: int,
    ):
        """Create a new WoD vanilla mortal."""
        await wod.create(
            ctx,
            Splat.MORTAL,
            name,
            health,
            willpower,
            path,
            path_rating,
            integrity,
            integrity_rating,
            control,
            control_rating,
            courage,
            max_trait,
        )


def setup(bot: BotchBot):
    bot.add_cog(MortalCog(bot))
