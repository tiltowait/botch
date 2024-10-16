"""Shared configuration variables."""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("CONFIG")

BOTCH_TOKEN = os.getenv("BOTCH_TOKEN")
DEBUG_GUILDS = [int(g) for g in os.getenv("DEBUG", "").split(",") if g and g.isdigit()] or None
EMOJI_GUILD = int(os.getenv("EMOJI_GUILD", 0))
SUPPORTER_GUILD = int(os.getenv("SUPPORTER_GUILD", 0))
SUPPORTER_ROLE = int(os.getenv("SUPPORTER_ROLE", 0))
BOT_ID: int | None = None

# Bucket for storing character images
FC_BUCKET = "pcs-dev.botch.lol" if "TESTING" in os.environ else "pcs.botch.lol"

MAX_NAME_LEN = 37  # Because of modal length restrictions
VERSION = os.getenv("VERSION_TAG", "local")


def set_bot_id(bot_id: int):
    """Set the bot's user ID."""
    global BOT_ID
    BOT_ID = bot_id
    logger.info("Set bot ID to %s", bot_id)
