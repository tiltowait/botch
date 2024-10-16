"""Common mocks for image commands."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot import AppCtx, BotchBot


@pytest.fixture(autouse=True)
async def mock_char_cd() -> AsyncGenerator[AsyncMock, None]:
    # We already have a base character fixture, but its save method
    # isn't mocked
    with patch.multiple(
        "core.characters.base.Character", save=AsyncMock(), delete=AsyncMock()
    ) as mocked:
        yield mocked


@pytest.fixture
def interaction() -> AsyncMock:
    inter = AsyncMock()
    inter.guild.id = 0
    inter.user.id = 0
    inter.response.is_done = Mock(return_value=False)

    return inter


@pytest.fixture
async def ctx(interaction: AsyncMock) -> AsyncGenerator[AppCtx, None]:
    with patch.multiple("bot.AppCtx", send_error=AsyncMock(), respond=AsyncMock()):
        bot = BotchBot()
        yield AppCtx(bot, interaction)
