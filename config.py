"""Shared configuration variables."""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("CONFIG")

BOTCH_TOKEN = os.getenv("BOTCH_TOKEN")
DEBUG_GUILDS = [int(g) for g in os.getenv("DEBUG", "").split(",") if g and g.isdigit()] or None
EMOJI_GUILD = int(os.getenv("EMOJI_GUILD", 0))
BOT_ID: int | None = None

# Bucket for storing character images
FC_BUCKET = "pcs-dev.botch.lol" if "TESTING" in os.environ else "pcs.botch.lol"


def set_bot_id(bot_id: int):
    """Set the bot's user ID."""
    global BOT_ID
    BOT_ID = bot_id
    logger.info("Set bot ID to %s", bot_id)
