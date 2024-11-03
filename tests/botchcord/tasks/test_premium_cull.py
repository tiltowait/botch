"""Premium culler tests."""

from datetime import UTC, datetime, timedelta

import pytest

from botchcord.models import User


@pytest.fixture
def user():
    return User(user=123)


def test_should_purge(user):
    assert not user.should_purge
    user.left_premium = datetime.now(UTC) - timedelta(days=User.PURGE_INTERVAL + 1)
    assert user.should_purge


def test_drop_premium(user):
    user.drop_premium()
    assert user.left_premium is not None
