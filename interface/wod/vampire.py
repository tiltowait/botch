"""Vampire commands."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.ext.commands import Cog

import utils
from bot import BotchBot
from botch.characters import Damage, GameLine, Grounding, Splat, Trait
from botch.characters.wod import Vampire
from botchcord.options import promoted_choice
from botchcord.wizard import Wizard


class VampireCog(Cog, name="VtM Commands"):
    """The vampire cog contains commands specific to VtM vampires."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    vampire = SlashCommandGroup("vampire", "Vampire-specific commands")

    @vampire.command(name="create")
    @option("name", description="The new vampire's name")
    @promoted_choice("generation", "The vampire's generation", start=4, end=15, first=13)
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
    @option(
        "max_bp",
        description="Override the generational maximum blood pool",
        min_value=1,
        required=False,
    )
    async def create_vampire(
        self,
        ctx: discord.ApplicationContext,
        name: str,
        generation: int,
        health: int,
        willpower: int,
        path: str,
        path_rating: int,
        integrity: str,
        integrity_rating: str,
        control: str,
        control_rating: str,
        courage: int,
        max_trait: int,
        max_bp: int,
    ):
        """Create a new V20 vampire."""
        if max_trait is None:
            max_trait = utils.max_vtm_trait(generation)
        if max_bp is None:
            max_bp = utils.max_vtm_bp(generation)

        # Because they have unique names, virtues are separate from regular traits
        virtues = [
            Trait(name=integrity, rating=integrity_rating, category=Trait.Category.VIRTUE),
            Trait(name=control, rating=control_rating, category=Trait.Category.VIRTUE),
            Trait(name="Courage", rating=courage, category=Trait.Category.VIRTUE),
        ]

        wizard = Wizard(
            GameLine.WOD,
            Splat.VAMPIRE,
            Vampire,
            generation=generation,
            max_rating=max_trait,
            name=name,
            guild=ctx.guild.id,
            user=ctx.user.id,
            health=Damage.NONE * health,
            willpower=Damage.NONE * willpower,
            grounding=Grounding(path=utils.normalize_text(path), rating=path_rating),
            max_bp=max_bp,
            blood_pool=max_bp,
            virtues=virtues,
        )
        await wizard.start(ctx.interaction)


def setup(bot: BotchBot):
    bot.add_cog(VampireCog(bot))
