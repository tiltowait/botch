"""Shared configuration variables."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BOTCH_TOKEN = os.getenv("BOTCH_TOKEN")
DEBUG_GUILDS: Optional[list] = None
EMOJI_GUILD = int(os.getenv("EMOJI_GUILD", 0))

if (_debug_guilds := os.getenv("DEBUG")) is not None:
    DEBUG_GUILDS = [int(g) for g in _debug_guilds.split(",")]

# Bucket for storing character images
FC_BUCKET = "pcs-dev.botch.lol" if "TESTING" in os.environ else "pcs.botch.lol"
