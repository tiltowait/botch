"""User cache tests."""

from datetime import UTC, datetime, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest

from botch.models import User, UserStore


@pytest.fixture
def cache() -> UserStore:
    return UserStore()


@pytest.fixture
async def mock_save() -> AsyncGenerator[AsyncMock, None]:
    with patch("botch.models.user.User.save", new_callable=AsyncMock) as mock:
        yield mock


async def test_cache_miss(mock_save: AsyncMock, cache: UserStore):
    user = await User.find_one()
    assert user is None

    user = await cache.fetch(0)
    assert isinstance(user, User)
    assert user.user == 0
    assert not user.settings.accessibility

    mock_save.assert_not_awaited()


async def test_cache_hit(cache: UserStore):
    user = User(user=0)
    user.settings.accessibility = True
    await user.save()

    found = await cache.fetch(0)
    assert user.id == found.id
    assert found.settings.accessibility


async def test_fetch_purgeable(cache: UserStore):
    users = [
        User(user=1, left_premium=datetime.now(UTC) - timedelta(days=31)),  # Should purge
        User(user=2, left_premium=datetime.now(UTC) - timedelta(days=15)),  # Should not purge
        User(user=3, left_premium=None),  # Should not purge
        User(user=4, left_premium=datetime.now(UTC) - timedelta(days=35)),  # Should purge
    ]
    for user in users:
        await user.save()

    purgeable = await cache.fetch_purgeable()
    purgeable_ids = [u.user for u in purgeable if u.should_purge]
    assert len(purgeable) == 2
    assert purgeable_ids == [1, 4]
