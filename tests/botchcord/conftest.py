"""Fixture config."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot import AppCtx
from models.guild import GuildCache


@pytest.fixture
def bot_mock() -> Mock:
    user = Mock()
    user.display_name = "tiltowait"
    user.guild_avatar = "https://example.com/img.png"

    bot = Mock()
    bot.guild_cache = GuildCache()
    bot.get_user.return_value = user
    bot.find_emoji = lambda e: e

    return bot


@pytest.fixture
async def ctx(bot_mock) -> AsyncGenerator[AppCtx, None]:
    with patch.multiple("bot.AppCtx", send_error=AsyncMock(), respond=AsyncMock()):
        ctx = AppCtx(bot_mock, AsyncMock())
        ctx.guild.id = 123
        ctx.guild.name = "Test Guild"
        yield ctx
