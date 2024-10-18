"""General character command interface."""

import discord
from discord import option
from discord.commands import SlashCommandGroup
from discord.commands.options import OptionChoice
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options
from botchcord.premium import premium


class CharactersCog(Cog, name="General character commands"):
    character = SlashCommandGroup("character", "General character commands")
    images = character.create_subgroup("image", "Character image commands")

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

    @character.command()
    @option(
        "era",
        description="Which era of sheet do you need?",
        choices=[OptionChoice("Modern", "vtm"), OptionChoice("Dark Ages", "dav20")],
    )
    async def wizard(self, ctx: AppCtx, era: str):
        """Create a character over the web."""
        await botchcord.character.web.wizard(ctx, era)

    @character.command(name="images")
    @options.character("The character to display")
    @option(
        "controls",
        description="Who can control the buttons?",
        choices=[OptionChoice("Only you", True), OptionChoice("Anyone", False)],
        default=True,
    )
    async def display_images(self, ctx: AppCtx, character: str, controls: bool):
        """View a character's images."""
        await botchcord.character.images.display(ctx, character, controls)

    @images.command(name="upload")
    @option("image", description="The image file to upload")
    @options.character("The character to upload the image to")
    @premium()
    async def upload_image(self, ctx: AppCtx, image: discord.Attachment, character: str):
        """[PREMIUM] Upload an image."""
        await botchcord.character.images.upload(ctx, character, image)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(CharactersCog(bot))
