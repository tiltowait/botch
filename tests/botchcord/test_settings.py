"""Guild settings tests. The tests here are trivial for now but exist as a
reminder to write thorough tests once the settings system is written, since
they will fail once that work is done."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot import AppCtx
from botchcord import settings


async def test_accessibility(ctx: AppCtx):
    assert await settings.accessibility(ctx) is False


async def test_use_emojis(ctx: AppCtx):
    assert await settings.use_emojis(ctx) != await settings.accessibility(ctx)


@pytest.mark.parametrize(
    "guild_a11y,user_a11y,a11y",
    [
        (False, False, False),
        (True, False, True),
        (False, True, True),
        (True, True, True),
    ],
)
async def test_settings_logic(ctx: AppCtx, guild_a11y: bool, user_a11y: bool, a11y: bool):
    guild = Mock()
    guild.settings.accessibility = guild_a11y

    user = Mock()
    user.settings.accessibility = user_a11y

    with (
        patch.object(ctx.bot.guild_cache, "fetch", new_callable=AsyncMock) as guild_fetch,
        patch.object(ctx.bot.user_store, "fetch", new_callable=AsyncMock) as user_mock,
    ):
        guild_fetch.return_value = guild
        user_mock.return_value = user

        assert await settings.accessibility(ctx) == a11y
        assert await settings.use_emojis(ctx) != a11y
