"""Botch: A Discord dice bot and character manager for WoD and CofD."""

from botch import logconfig
from botch.bot import BotchBot
from botch.config import BOTCH_TOKEN, GAME_LINE


def main():
    assert BOTCH_TOKEN is not None
    logconfig.configure_logging()

    bot = BotchBot()
    bot.load_cogs(["shared", GAME_LINE])
    bot.run(BOTCH_TOKEN)


if __name__ == "__main__":
    main()
