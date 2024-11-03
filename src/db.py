"""Database connection, functions, and collections."""

import logging
import os

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from botchcord.models import User
from core.characters import Character, cofd, wod
from core.rolls import Roll
from interface.models import CommandRecord

load_dotenv()

logger = logging.getLogger("DB")
DOCUMENT_MODELS = [
    Character,
    wod.Vampire,
    wod.Ghoul,
    wod.Mortal,
    cofd.Mummy,
    cofd.Vampire,
    cofd.Mortal,
    Roll,
    User,
    CommandRecord,
]


async def init():
    """Initialize the database."""
    logger.info("Initializing database")

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["MONGO_DB"]]
    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
