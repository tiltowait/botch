"""Character image uploading."""

import logging
from urllib.parse import urlparse

import discord

import api
from bot import AppCtx, BotchBot
from botchcord.haven import haven
from botchcord.utils import CEmbed
from core.characters import Character

VALID_EXTENSIONS = [".png", ".webp", ".jpg", ".jpeg"]
logger = logging.getLogger("IMAGES")


@haven()
async def upload_image(ctx: AppCtx, character: Character, image: discord.Attachment):
    """Upload an image. Only premium users can use this feature."""
    if not valid_url(image.url):
        await ctx.send_error(
            "Invalid image file!", f"**Allowed extensions:** {', '.join(VALID_EXTENSIONS)}"
        )
        return

    if not ctx.interaction.response.is_done():
        # If we responded already, there's no chance of timeout; also we can't
        # defer if we've responded, so ...
        await ctx.interaction.response.defer(ephemeral=True, invisible=False)

    processed_url = await api.upload_faceclaim(character, image.url)
    logger.info("%s: Uploaded new image to %s", character.name, processed_url)

    character.profile.add_image(processed_url)
    embed = build_embed(ctx.bot, character, processed_url)

    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def build_embed(bot: BotchBot, character: Character, new_image_url: str) -> CEmbed:
    """Build the CEmbed for the new image."""
    embed = CEmbed(
        bot,
        character,
        show_thumbnail=False,
        title="Image uploaded!",
    )
    embed.set_image(url=new_image_url)
    embed.set_footer(text="View your images with /character images.")

    return embed


def valid_url(url: str) -> bool:
    """Check whether a URL is a valid image URL."""
    purl = urlparse(url.lower())
    logger.debug("Checking validity of %s", url)

    for extension in VALID_EXTENSIONS:
        if purl.path.endswith(extension):
            return True
    return False
