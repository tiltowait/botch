"""Premium culler tests."""

from datetime import UTC, datetime, timedelta

import pytest

from botchcord.models import User
from botchcord.tasks import premium


@pytest.fixture
def user():
    return User(user=123)


@pytest.fixture(autouse=True)
async def mock_users():
    users = [
        User(user=1, left_premium=datetime.now(UTC) - timedelta(days=31)),  # Should purge
        User(user=2, left_premium=datetime.now(UTC) - timedelta(days=15)),  # Should not purge
        User(user=3, left_premium=None),  # Should not purge
        User(user=4, left_premium=datetime.now(UTC) - timedelta(days=35)),  # Should purge
    ]
    for user in users:
        await user.save()

    return users


def test_should_purge(user):
    assert not user.should_purge
    user.left_premium = datetime.now(UTC) - timedelta(days=User.PURGE_INTERVAL + 1)
    assert user.should_purge


def test_drop_premium(user):
    user.drop_premium()
    assert user.left_premium is not None


async def test_fetch_purgable_users():
    purgable = await premium.fetch_purgable_users()
    assert len(purgable) == 2
    assert [u.user for u in purgable] == [1, 4]
