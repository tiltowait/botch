"""Guild tests."""

from unittest.mock import Mock

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


async def test_guild_join(bot: BotchBot, guild: Mock):
    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is None

    await bot.on_guild_join(guild)
    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.guild == guild.id
    assert found.name == guild.name
    assert found.left is None


async def test_guild_leave_nonexistent(bot: BotchBot, guild: Mock):
    await bot.on_guild_remove(guild)
    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is None


async def test_guild_leave_extant(bot: BotchBot, guild: Mock):
    await bot.on_guild_join(guild)
    await bot.on_guild_remove(guild)

    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.left is not None


async def test_guild_rejoin(bot: BotchBot, guild: Mock):
    await bot.on_guild_join(guild)
    await bot.on_guild_remove(guild)
    await bot.on_guild_join(guild)

    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.left is None


async def test_guild_rename(bot: BotchBot, guild: Mock):
    await bot.on_guild_join(guild)
    new_named = Mock()
    new_named.id = guild.id
    new_named.name = "Renamed!"

    await bot.on_guild_update(guild, new_named)

    found = await Guild.find_one(Guild.guild == guild.id)
    assert found is not None
    assert found.name == new_named.name
