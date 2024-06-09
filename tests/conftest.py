"""Pytest configuration."""

import asyncio

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from core.characters import Character, GameLine, Splat, Trait
from db import DOCUMENT_MODELS
from tests.characters import gen_char


@pytest.fixture(autouse=True)
async def beanie_fixture():
    """Configures a mock beanie client for all tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client.get_database(name="db"),
        document_models=DOCUMENT_MODELS,
    )


@pytest.fixture(params=list(Splat), scope="function")
def character(request):
    return gen_char(GameLine.WOD, request.param)


@pytest.fixture(params=list(GameLine))
def line(request):
    return request.param


@pytest.fixture(scope="function")
def skilled(character: Character):
    character.add_trait("Intelligence", 4, Trait.Category.ATTRIBUTE)
    character.add_trait("Strength", 2, Trait.Category.ATTRIBUTE)
    character.add_trait("Brawl", 3, Trait.Category.ABILITY)
    character.add_trait("Fighting", 3, Trait.Category.CUSTOM)
    character.add_trait("Streetwise", 1, Trait.Category.ABILITY)
    character.add_subtraits("Brawl", "Kindred")
    return character


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop to share between tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
