"""Guild tests."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot import BotchBot
from models import Guild


@pytest.fixture
def guild() -> Mock:
    mock = Mock()
    mock.id = 123
    mock.name = "Test Guild"
    return mock


@pytest.fixture
def bot() -> BotchBot:
    return BotchBot()


@pytest.fixture
async def mock_save() -> AsyncGenerator[AsyncMock, None]:
    with patch("models.Guild.save", new_callable=AsyncMock) as mock:
        yield mock


async def test_guild_join(bot: BotchBot, guild: Mock):
    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is None

    await bot.on_guild_join(guild)
    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.guild == guild.id
    assert found.name == guild.name
    assert found.left is None


async def test_guild_leave_nonexistent(bot: BotchBot, guild: Mock, mock_save: AsyncMock):
    await bot.on_guild_remove(guild)
    mock_save.assert_not_awaited()

    found = await bot.guild_cache.fetch(guild)
    assert found is None


async def test_guild_leave_extant(bot: BotchBot, guild: Mock, mock_save: AsyncMock):
    await bot.on_guild_join(guild)
    await bot.on_guild_remove(guild)

    assert mock_save.await_count == 2, "join + leave"

    found = await bot.guild_cache.fetch(guild)
    # found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.left is not None


async def test_guild_rejoin(bot: BotchBot, guild: Mock, mock_save: AsyncMock):
    await bot.on_guild_join(guild)
    await bot.on_guild_remove(guild)
    await bot.on_guild_join(guild)

    mock_save.assert_awaited()
    assert mock_save.await_count == 3, "join + leave + join"

    found = await bot.guild_cache.fetch(guild)
    assert found is not None
    assert found.left is None


async def test_guild_rename(bot: BotchBot, guild: Mock, mock_save: AsyncMock):
    await bot.on_guild_join(guild)
    renamed = Mock()
    renamed.id = guild.id
    renamed.name = "Renamed!"

    await bot.on_guild_update(guild, renamed)
    mock_save.assert_awaited()
    assert mock_save.await_count == 2

    found = await bot.guild_cache.fetch(guild)
    assert found is not None
    assert found.name == renamed.name


async def test_cache_fetch_not_found(bot: BotchBot, guild: Mock):
    found = await bot.guild_cache.fetch(guild)
    assert found is None
    assert not bot.guild_cache._cache


async def test_cache_fetch_create(bot: BotchBot, guild: Mock, mock_save: AsyncMock):
    guild = await bot.guild_cache.fetch(guild, create=True)
    assert guild.guild in bot.guild_cache._cache
    mock_save.assert_awaited_once()


async def test_cache_fetch_found(bot: BotchBot, guild: Mock):
    await bot.on_guild_join(guild)
    found = await bot.guild_cache.fetch(guild)
    assert found is not None
    assert bot.guild_cache._cache[guild.id] == found


async def test_cache_invalidation(bot: BotchBot, guild: Mock):
    await bot.on_guild_join(guild)
    # Get it into cache
    _ = await bot.guild_cache.fetch(guild)
    # Modify directly in DB
    g = await Guild.find_one(Guild.guild == guild.id)
    assert g is not None
    g.name = "Changed Outside Cache"
    await g.save()
    # Should still get cached version
    cached = await bot.guild_cache.fetch(guild)
    assert cached is not None
    assert cached.name == guild.name
