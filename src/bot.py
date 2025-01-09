"""Botch bot and helpers."""

import logging
import os
from pathlib import Path
from typing import cast, overload

import discord

import config
import db
import errors
import tasks
from config import DEBUG_GUILDS, EMOJI_GUILD, SUPPORTER_GUILD, SUPPORTER_ROLE
from errors import BotchError, NotPremium
from models import GuildCache
from models.user import cache as user_cache

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

    @property
    def admin_user(self) -> bool:
        """Whether the invoking user is an admin."""
        return self.channel.permissions_for(self.author).administrator


class BotchBot(discord.Bot):
    """The bot class for Botch."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            intents=discord.Intents(guilds=True, members=True),
            debug_guilds=DEBUG_GUILDS,
            *args,
            **kwargs,
        )
        self.guild_cache = GuildCache()
        self.user_store = user_cache  # Singleton instance

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

        tasks.premium.purge.start()
        logger.info("Tasks scheduled")

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
    def find_emoji(self, emoji_name: str) -> str: ...

    @overload
    def find_emoji(self, emoji_name: str, count: int) -> str | list[str]: ...

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
        context: discord.ApplicationContext,
        exception: discord.DiscordException,
    ):
        context = cast(AppCtx, context)
        exception = cast(discord.ApplicationCommandInvokeError, exception)

        err = exception.original
        match err:
            case discord.NotFound():
                # This might be dangerous during development
                pass
            case BotchError():
                await context.send_error("Error", str(err), ephemeral=True)
            case NotPremium():
                cmd_mention = context.bot.cmd_mention(context.command.qualified_name)
                await context.send_error(
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

    async def on_guild_join(self, guild: discord.Guild):
        """Notify guild joining."""
        logger.info("Joined %s :)", guild.name)
        await self.guild_cache.guild_joined(guild)

    async def on_guild_remove(self, guild: discord.Guild):
        """Notify guild removal."""
        logger.info("Left %s :(", guild.name)
        await self.guild_cache.guild_left(guild)

    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Rename the guild."""
        if before.name != after.name:
            logger.info("Guild: %s renamed to %s (ID: %s)", before.name, after.name, after.id)
            await self.guild_cache.rename(after, after.name)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Check for supporter status changes."""
        if before.guild.id != SUPPORTER_GUILD:
            return

        def is_supporter(member: discord.Member) -> bool:
            """Check if the member is a supporter."""
            return member.get_role(SUPPORTER_ROLE) is not None

        user = await self.user_store.fetch(after.id)

        if is_supporter(before) and not is_supporter(after):
            logger.info("%s is no longer a supporter :(", after.name)
            user.drop_premium()

        elif is_supporter(after) and not is_supporter(before):
            logger.info("%s is now a supporter!", after.name)
            user.gain_premium()

        await user.save()

    def cmd_mention(
        self,
        name: str,
        type: type[discord.ApplicationCommand] = discord.ApplicationCommand,
    ) -> str | None:
        """Shorthand for get_application_command(...).mention."""
        if command := self.get_application_command(name, type=type):
            return command.mention  # type: ignore
        return None
