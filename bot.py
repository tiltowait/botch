"""Botch bot and helpers."""

import logging
import os
from typing import cast

import discord

import config
import db
import errors
from config import DEBUG_GUILDS, EMOJI_GUILD
from errors import BotchError

__all__ = ("AppCtx", "BotchBot")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BOT")


class AppCtx(discord.ApplicationContext):
    bot: "BotchBot"

    async def send_error(
        self,
        title: str,
        description: str,
        ephemeral=True,
        interaction: discord.Interaction | None = None,
    ):
        """Send an error embed."""
        embed = discord.Embed(title=title, description=description, color=discord.Color.brand_red())
        if interaction:
            await interaction.respond(embed=embed, ephemeral=ephemeral)
        else:
            await self.respond(embed=embed, ephemeral=ephemeral)


class BotchBot(discord.Bot):
    """The bot class for Botch."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            intents=discord.Intents(guilds=True, members=True),
            debug_guilds=DEBUG_GUILDS,
            *args,
            **kwargs,
        )
        if DEBUG_GUILDS:
            logger.info("Debugging on %s", DEBUG_GUILDS)

    async def on_connect(self):
        logger.info("Connected")
        await db.init()
        await self.sync_commands()

    async def on_ready(self):
        assert self.user is not None
        config.set_bot_id(self.user.id)
        logger.info("Ready!")

    def load_cogs(self):
        """Load cogs based on configuration parameters."""
        # Add the cogs
        def load(dir: str):
            for filename in os.listdir(f"./interface/{dir}"):
                if filename[0] != "_" and filename.endswith(".py"):
                    logging.getLogger("COGS").debug("Loading %s", filename)
                    self.load_extension(f"interface.{dir}.{filename[:-3]}")

        load("wod")
        load("shared")

    def get_emoji(self, emoji_name: str, count=1) -> str | list[str] | None:
        """Get an emoji from the emoji guild."""
        if guild := self.get_guild(EMOJI_GUILD):
            try:
                emoji = next(e for e in guild.emojis if e.name == emoji_name)
                emoji = str(emoji) + "\u200b"  # Add zero-width space to fix Discord embed bug
                if count > 1:
                    return [emoji] * count
                return emoji
            except StopIteration:
                pass
        raise errors.EmojiNotFound

    async def get_application_context(self, interaction: discord.Interaction, cls=AppCtx) -> AppCtx:
        """Make all contexts AppCtx instances."""
        ctx = await super().get_application_context(interaction, cls=cls)
        return cast(AppCtx, ctx)

    async def on_application_command_error(
        self,
        ctx: AppCtx,
        exception: discord.ApplicationCommandInvokeError,
    ):
        err = exception.original
        match err:
            case discord.NotFound():
                # This might be dangerous during development
                pass
            case BotchError():
                await ctx.send_error("Error", str(err), ephemeral=True)
            case _:
                # TODO: Error reporter
                raise err
