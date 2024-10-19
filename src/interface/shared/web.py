"""Web interface."""

import asyncio
import logging

import uvicorn
from discord.ext import commands

from bot import BotchBot
from web.app import app

logger = logging.getLogger("APICOG")


class APIServerCog(commands.Cog):
    """Starts the FastAPI server."""

    def __init__(self, bot: BotchBot):
        self.bot = bot
        self.server_task: asyncio.Task | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        config = uvicorn.Config(app, host="::", port=8000, loop="asyncio")
        server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(server.serve())
        logger.info("API server started")

    def cog_unload(self):
        if self.server_task:
            self.server_task.cancel()
            logger.info("API server stopped")


def setup(bot: BotchBot):
    bot.add_cog(APIServerCog(bot))
