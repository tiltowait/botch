"""General character command interface."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.commands.options import OptionChoice
from discord.ext.commands import user_command

from botch import botchcord
from botch.bot import AppCtx, BotchBot
from botch.botchcord import options
from botch.botchcord.premium import premium
from botch.config import DOCS_URL, GAME_LINE
from botch.core.characters.base import GameLine
from botch.interface import BotchCog

if GAME_LINE == GameLine.WOD:
    ERAS = [OptionChoice("Modern", "vtm"), OptionChoice("Dark Ages", "dav20")]
else:
    ERAS = [OptionChoice("Modern", "vtr")]


class CharactersCog(BotchCog, name="Character info and adjustment"):
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
        self.docs_url = f"{DOCS_URL}/reference/characters"

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
    @options.character("The character to rename", required=True)
    @option("new_name", description="The character's new name")
    async def rename(self, ctx: AppCtx, character: str, new_name: str):
        """Rename a character."""
        await botchcord.character.rename(ctx, character, new_name)

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
        choices=[OptionChoice("Anyone", 0), OptionChoice("Only you", 1)],
        default=0,
    )
    async def display_images(
        self,
        ctx: AppCtx,
        character: str,
        controls: int,
        owner: discord.Member,
    ):
        """View a character's images."""
        await botchcord.character.images.display(ctx, character, bool(controls), owner=owner)

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
