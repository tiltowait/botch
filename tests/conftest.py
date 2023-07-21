"""Pytest configuration."""

import asyncio

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from characters import Character, Splat
from tests.characters import gen_char


@pytest.fixture(autouse=True)
async def beanie_fixture():
    """Configures a mock beanie client for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(database=client.get_database(name="db"), document_models=[Character])


@pytest.fixture(params=list(Splat), scope="function")
def character(request):
    return gen_char(request.param)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop to share between tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
