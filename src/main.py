"""Botch: A Discord dice bot and character manager for WoD and CofD."""

import logconfig
from bot import BotchBot
from config import BOTCH_TOKEN


def main():
    assert BOTCH_TOKEN is not None
    logconfig.configure_logging()

    bot = BotchBot()
    bot.load_cogs(["shared", "wod"])
    bot.run(BOTCH_TOKEN)


if __name__ == "__main__":
    main()