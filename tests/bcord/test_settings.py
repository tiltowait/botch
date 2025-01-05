"""Guild settings tests. The tests here are trivial for now but exist as a
reminder to write thorough tests once the settings system is written, since
they will fail once that work is done."""

from unittest.mock import Mock

import pytest

from bot import AppCtx, BotchBot
from botchcord import settings


@pytest.fixture
def ctx() -> AppCtx:
    inter = Mock()
    inter.guild.id = 123
    inter.guild.name = "Test Guild"
    return AppCtx(BotchBot(), inter)


async def test_accessibility(ctx):
    assert await settings.accessibility(ctx) is False


async def test_use_emojis(ctx):
    assert await settings.use_emojis(ctx) != await settings.accessibility(ctx)
