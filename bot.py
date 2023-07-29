"""Botch bot and helpers."""

import logging
import os

import discord

import db
import errors
from config import DEBUG_GUILDS, EMOJI_GUILD

logging.basicConfig(level=logging.INFO)


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
            logging.getLogger("BOT").info("Debugging on %s", DEBUG_GUILDS)

    async def on_connect(self):
        print("Connected")
        await db.init()
        await self.sync_commands()

    async def on_ready(self):
        print("Ready!")

    def load_cogs(self):
        """Load cogs based on configuration parameters."""
        # Add the cogs
        for filename in os.listdir("./interface/wod"):
            if filename[0] != "_" and filename.endswith(".py"):
                logging.getLogger("COGS").debug("Loading %s", filename)
                self.load_extension(f"interface.wod.{filename[:-3]}")

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
