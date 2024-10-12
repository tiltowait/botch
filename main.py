"""Botch: A Discord dice bot and character manager for WoD and CofD."""

from bot import BotchBot
from config import BOTCH_TOKEN


def main():
    assert BOTCH_TOKEN is not None
    bot = BotchBot()
    bot.load_cogs()
    bot.run(BOTCH_TOKEN)


if __name__ == "__main__":
    main()
