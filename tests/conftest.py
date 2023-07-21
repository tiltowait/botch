"""Pytest configuration."""

import asyncio

import pytest
from beanie import init_beanie
from characters import Character
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture(autouse=True)
async def beanie_fixture():
    """Configures a mock beanie client for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(database=client.get_database(name="db"), document_models=[Character])


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop to share between tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
