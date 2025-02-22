"""Pytest configuration."""

import asyncio
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from motor.motor_asyncio import AsyncIOMotorClient

from core.characters import Character, GameLine, Splat, Trait
from db import DOCUMENT_MODELS
from tests.characters import gen_char


@pytest.fixture(autouse=True, scope="session")
async def beanie_fixture():
    """Configures a mock beanie client for all tests."""
    client = cast(AsyncIOMotorClient, AsyncMongoMockClient())
    await init_beanie(
        database=client.get_database(name="db"),
        document_models=DOCUMENT_MODELS,
    )


@pytest.fixture(autouse=True)
async def clear_collections():
    """Clear all collections. Doing it this way results in a 20% speedup over
    re-initializing the collections on each test."""
    yield
    for model in DOCUMENT_MODELS:
        await model.delete_all()


@pytest.fixture(params=list(Splat), scope="function")
def character(request):
    return gen_char(GameLine.WOD, request.param)


@pytest.fixture(params=list(GameLine))
def line(request):
    return request.param


@pytest.fixture(scope="function")
def skilled(character: Character):
    Cat = Trait.Category
    Sub = Trait.Subcategory

    character.add_trait("Intelligence", 4, Cat.ATTRIBUTE, Sub.MENTAL)
    character.add_trait("Strength", 2, Cat.ATTRIBUTE, Sub.PHYSICAL)
    character.add_trait("Brawl", 3, Cat.ABILITY, Sub.TALENTS)
    character.add_trait("Fighting", 3, Cat.CUSTOM)
    character.add_trait("Streetwise", 1, Cat.ABILITY, Sub.TALENTS)
    character.add_subtraits("Brawl", "Kindred")
    return character


@pytest.fixture(scope="function")
def bot_mock() -> Mock:
    user = Mock()
    user.display_name = "tiltowait"
    user.guild_avatar = "https://example.com/img.png"

    bot = Mock()
    bot.get_user.return_value = user
    bot.find_emoji = lambda e: e

    return bot


@pytest.fixture
def ctx(bot_mock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.guild.name = "Great Guildy!"
    ctx.guild.icon.url = "https://example.com/icon.png"
    ctx.bot = bot_mock
    ctx.respond.return_value = None

    return ctx


@pytest.fixture
def mock_char_save():
    with patch("core.characters.Character.save") as mocked:
        yield mocked


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop to share between tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
