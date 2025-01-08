"""General character command interface."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.commands.options import OptionChoice
from discord.ext.commands import Cog, user_command

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options
from botchcord.premium import premium
from config import GAME_LINE
from core.characters.base import GameLine

if GAME_LINE == GameLine.WOD:
    ERAS = [OptionChoice("Modern", "vtm"), OptionChoice("Dark Ages", "dav20")]
else:
    ERAS = [OptionChoice("Modern", "vtr")]


class CharactersCog(Cog, name="Character info and adjustment"):
    """Commands for displaying and updating character status as well as images\
    (premium users only)."""

    character = SlashCommandGroup(
        "character",
        "General character commands",
        contexts={discord.InteractionContextType.guild},
    )
    images = character.create_subgroup("image", "Character image commands")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @user_command(name="View: Character")
    async def user_characters(self, ctx: AppCtx, member: discord.Member):
        """Display the user's character(s)."""
        await botchcord.character.display(ctx, "", owner=member)

    @character.command()
    @options.character("The character to display")
    @options.owner()
    async def display(self, ctx: AppCtx, character: str, owner: discord.Member):
        """Display one of your character's stats."""
        await botchcord.character.display(ctx, character, owner=owner)

    @character.command()
    @options.character("The character to delete", required=True)
    async def delete(self, ctx: AppCtx, character: str):
        """Delete one of your characters."""
        await botchcord.character.delete(ctx, character)

    @character.command()
    @options.character("The character to adjust")
    async def adjust(self, ctx: AppCtx, character: str):
        """Adjust one of your character's stats."""
        await botchcord.character.adjust(ctx, character)

    @character.command()
    @option(
        "era",
        description="Which era of sheet do you need?",
        choices=ERAS,
    )
    async def wizard(self, ctx: AppCtx, era: str):
        """Create a character. This command opens a web browser."""
        await botchcord.character.web.wizard(ctx, era)

    @user_command(name="View: Character Images")
    async def user_images(self, ctx: AppCtx, member: discord.Member):
        """Display a user's character's images."""
        await botchcord.character.images.display(ctx, "", True, owner=member)

    @character.command(name="images")
    @options.character("The character to display", permissive=True)
    @options.owner()
    @option(
        "controls",
        description="Who can control the buttons?",
        choices=[OptionChoice("Only you", True), OptionChoice("Anyone", False)],
        default=True,
    )
    async def display_images(
        self,
        ctx: AppCtx,
        character: str,
        controls: bool,
        owner: discord.Member,
    ):
        """View a character's images."""
        await botchcord.character.images.display(ctx, character, controls, owner=owner)

    @images.command(name="upload")
    @option("image", description="The image file to upload")
    @options.character("The character to upload the image to")
    @premium()
    async def upload_image(self, ctx: AppCtx, image: discord.Attachment, character: str):
        """[PREMIUM] Upload a character image."""
        await botchcord.character.images.upload(ctx, character, image)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(CharactersCog(bot))
