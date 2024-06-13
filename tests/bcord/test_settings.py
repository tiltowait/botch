"""Guild settings tests. The tests here are trivial for now but exist as a
reminder to write thorough tests once the settings system is written, since
they will fail once that work is done."""

from unittest.mock import AsyncMock

import pytest

from botchcord import settings


@pytest.fixture
def ctx():
    return AsyncMock()


async def test_accessibility(ctx):
    assert await settings.accessibility(ctx) is False


async def test_use_emojis(ctx):
    assert await settings.use_emojis(ctx) != await settings.accessibility(ctx)
