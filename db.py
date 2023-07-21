"""Database connection, functions, and collections."""

import logging
import os

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from characters import Character

load_dotenv()

logger = logging.getLogger("db")
logger.info("Initializing database connection")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["MONGO_DB"]]


async def init():
    """Initialize the database."""
    logger.info("Initializing beanie")
    await init_beanie(database=db, document_models=[Character])
