"""Botch: A Discord dice bot and character manager for WoD and CofD."""

import asyncio

from bot import BotchBot
from config import BOTCH_TOKEN

bot = BotchBot()
bot.load_cogs()

if __name__ == "__main__":
    asyncio.run(bot.run(BOTCH_TOKEN))
