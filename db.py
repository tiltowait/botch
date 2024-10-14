"""Database connection, functions, and collections."""

import logging
import os

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from core.characters import Character, wod
from core.rolls import Roll
from interface.models import CommandRecord

load_dotenv()

logger = logging.getLogger("db")
DOCUMENT_MODELS = [Character, wod.Vampire, wod.Mortal, Roll, CommandRecord]


async def init():
    """Initialize the database."""
    logger.info("Initializing database")

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["MONGO_DB"]]
    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
