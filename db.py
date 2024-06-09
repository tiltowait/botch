"""Database connection, functions, and collections."""

import logging
import os

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from core.characters import Character, wod
from core.rolls import Roll

load_dotenv()

logger = logging.getLogger("db")
logger.info("Initializing database connection")


async def init():
    """Initialize the database."""
    logger.info("Initializing beanie")

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["MONGO_DB"]]
    await init_beanie(database=db, document_models=[Character, wod.Vampire, wod.Mortal, Roll])
