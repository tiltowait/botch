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


@pytest.fixture(scope="function")
def skilled(character: Character):
    character.add_trait("Intelligence", 4)
    character.add_trait("Strength", 2)
    character.add_trait("Brawl", 3)
    character.add_trait("Fighting", 3)
    character.add_trait("Streetwise", 1)
    character.add_subtraits("Brawl", "Kindred")
    print(character.traits)
    return character


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop to share between tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
