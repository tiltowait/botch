"""Botch bot and helpers."""

import logging
import os

import discord

import db
from config import DEBUG_GUILDS

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
