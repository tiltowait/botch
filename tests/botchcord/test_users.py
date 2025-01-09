"""User cache tests."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest

from models import User, UserStore


@pytest.fixture
def cache() -> UserStore:
    return UserStore()


@pytest.fixture
async def mock_save() -> AsyncGenerator[AsyncMock, None]:
    with patch("models.user.User.save", new_callable=AsyncMock) as mock:
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
