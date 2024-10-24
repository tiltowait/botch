"""Botch bot and helpers."""

import logging
import os
from pathlib import Path
from typing import cast, overload

import discord

import config
import db
import errors
from config import DEBUG_GUILDS, EMOJI_GUILD
from errors import BotchError, NotPremium

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
        self.accept_commands = False
        self.welcomed = False
        if DEBUG_GUILDS:
            logger.info("Debugging on %s", DEBUG_GUILDS)

    async def on_connect(self):
        logger.info("Connected")
        await db.init()
        await self.sync_commands()
        self.accept_commands = True

    async def on_ready(self):
        assert self.user is not None
        self.welcomed = True
        config.set_bot_id(self.user.id)
        logger.info("Ready!")

    def load_cogs(self, directories: list[str]) -> None:
        """Load cogs from specified directories relative to this script."""
        logger = logging.getLogger("COGS")
        logger.info("Opening interfaces: %s", directories)

        # Get the directory of the current script
        base_path = Path(__file__).parent

        for directory in directories:
            cog_dir = base_path / "interface" / directory
            for filename in os.listdir(cog_dir):
                if filename.endswith(".py") and not filename.startswith("_"):
                    cog_path = f"interface.{directory}.{filename[:-3]}"
                    try:
                        self.load_extension(cog_path)
                        logger.debug(f"Loaded cog: {cog_path}")
                    except Exception as e:
                        logger.error(f"Failed to load cog {cog_path}: {str(e)}")

    @overload
    def find_emoji(self, emoji_name: str) -> str:
        ...

    @overload
    def find_emoji(self, emoji_name: str, count: int) -> str | list[str]:
        ...

    def find_emoji(self, emoji_name: str, count=1) -> str | list[str]:
        """Get an emoji from the emoji guild."""
        if guild := self.get_guild(EMOJI_GUILD):
            try:
                emoji = next(e for e in guild.emojis if e.name == emoji_name)
                emoji_str = str(emoji) + "\u200b"  # Add zero-width space to fix Discord embed bug
                if count > 1:
                    return [emoji_str] * count
                return emoji_str
            except StopIteration:
                pass
        raise errors.EmojiNotFound

    async def get_application_context(self, interaction: discord.Interaction, cls=AppCtx) -> AppCtx:
        """Make all contexts AppCtx instances."""
        ctx = await super().get_application_context(interaction, cls=cls)
        return cast(AppCtx, ctx)

    async def on_interaction(self, interaction: discord.Interaction):
        """Prevent commands if database hasn't been initialized."""
        if self.accept_commands:
            await self.process_application_commands(interaction)
        else:
            bot_name = self.user.name if self.user else "Botch"
            await interaction.respond(
                f"**Error:** {bot_name} is still initializing. Please try again.",
                ephemeral=True,
            )

    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        exception: discord.DiscordException,
    ):
        # Fix some mypy complaints
        ctx = cast(AppCtx, ctx)
        exception = cast(discord.ApplicationCommandInvokeError, exception)

        err = exception.original
        match err:
            case discord.NotFound():
                # This might be dangerous during development
                pass
            case BotchError():
                await ctx.send_error("Error", str(err), ephemeral=True)
            case NotPremium():
                cmd_mention = ctx.bot.cmd_mention(ctx.command.qualified_name)
                await ctx.send_error(
                    "This is a premium feature",
                    (
                        f"Only patrons can use {cmd_mention}. Click "
                        "[this link](https://patreon.com/tiltowait) to get started!"
                    ),
                    ephemeral=True,
                )
            case _:
                # TODO: Error reporter
                raise err

    def cmd_mention(
        self,
        name: str,
        type: type[discord.ApplicationCommand] = discord.ApplicationCommand,
    ) -> str | None:
        """Shorthand for get_application_command(...).mention."""
        if command := self.get_application_command(name, type=type):
            return command.mention  # type: ignore
        return None
