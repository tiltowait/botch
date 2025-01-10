"""Premium culler tests."""

from datetime import UTC, datetime, timedelta
from functools import partial
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bot import BotchBot
from config import SUPPORTER_GUILD
from core import cache
from core.characters import Character, GameLine, Splat
from models import User
from tasks import premium
from tests.characters import gen_char

# We don't care about the save and delete operations in the database, so we
# mock therm here to save time. The relevant actions are handled by the cache
# and not the database, but we can still check whether we're properly saving.


@pytest.fixture(autouse=True)
async def mock_save() -> AsyncGenerator[AsyncMock, None]:
    with patch("core.characters.Character.save", new_callable=AsyncMock) as mocked:
        yield mocked


@pytest.fixture(autouse=True)
async def mock_delete() -> AsyncGenerator[AsyncMock, None]:
    with patch("core.characters.Character.delete", new_callable=AsyncMock) as mocked:
        yield mocked


@pytest.fixture(autouse=True)
async def mock_api() -> AsyncGenerator[AsyncMock, None]:
    with patch("api.delete_character_faceclaims", new_callable=AsyncMock) as mocked:
        yield mocked


@pytest.fixture
def bot() -> BotchBot:
    return BotchBot()


@pytest.fixture
def user() -> User:
    return User(user=123)


@pytest.fixture(autouse=True)
async def mock_users() -> AsyncGenerator[list[User], None]:
    users = [
        User(user=1, left_premium=datetime.now(UTC) - timedelta(days=31)),  # Should purge
        User(user=2, left_premium=datetime.now(UTC) - timedelta(days=15)),  # Should not purge
        User(user=3, left_premium=None),  # Should not purge
        User(user=4, left_premium=datetime.now(UTC) - timedelta(days=35)),  # Should purge
    ]
    for user in users:
        await user.save()

    yield users

    # tasks.premium uses the user cache singleton. Some tests modify the users
    # in the cache, so we need to reset the cache after each test. We can
    # easily do this by tricking it into thinking it hasn't yet populated.
    premium.user_store._populated = False


@pytest.fixture(autouse=True)
async def mock_characters() -> AsyncGenerator[list[Character], None]:
    gc = partial(gen_char, line=GameLine.WOD, splat=Splat.VAMPIRE)
    chars = [
        gc(guild=1, user=1, name="A"),  # Should purge
        gc(guild=2, user=2, name="B"),
        gc(guild=3, user=3, name="C"),
        gc(guild=1, user=1, name="D"),  # Should NOT purge - no images
        gc(guild=2, user=4, name="E"),  # Should purge
        gc(guild=3, user=4, name="F"),  # Should purge
        gc(guild=1, user=2, name="G"),
        gc(guild=2, user=1, name="H"),  # Should purge
    ]
    # The correct method is just Character.add_image(), but we don't need the
    # API call for these tests
    chars[0].profile.add_image("https://example.com/image.png")
    chars[0].profile.add_image("https://example.com/image.png")
    chars[0].profile.add_image("https://example.com/image.png")
    chars[4].profile.add_image("https://example.com/image.png")
    chars[5].profile.add_image("https://example.com/image.png")
    chars[7].profile.add_image("https://example.com/image.png")
    chars[7].profile.add_image("https://example.com/image.png")

    for char in chars:
        await cache.register(char)

    yield chars

    for char in chars:
        await cache.remove(char)


def test_should_purge(user: User):
    assert not user.should_purge
    user.left_premium = datetime.now(UTC) - timedelta(days=User.PURGE_INTERVAL + 1)
    assert user.should_purge


def test_should_not_purge(user: User):
    assert not user.should_purge
    user.left_premium = datetime.now(UTC) - timedelta(days=User.PURGE_INTERVAL - 1)
    assert not user.should_purge


def test_drop_premium(user: User):
    user.drop_premium()
    assert user.left_premium is not None


async def test_fetch_purgeable_characters():
    users = await premium.fetch_purgeable_users()
    chars = []
    for user in users:
        purgeable = await premium.fetch_purgeable_characters(user)
        assert all(c.user == user.user for c in purgeable)
        chars.extend(purgeable)

    assert len(chars) == 4
    assert all(len(c.profile.images) > 0 for c in chars)

    # We have to use a set here, because the order from the database isn't
    # guaranteed
    assert {c.name for c in chars} == {"A", "E", "F", "H"}


async def test_fetch_purge_images(mock_api: AsyncMock, mock_save: AsyncMock):
    users = await premium.fetch_purgeable_users()
    for user in users:
        count = await premium.purge_images(user)
        assert user.left_premium is None
        assert not user.should_purge

        if user.user == 1:
            assert count == 5
        elif user.user == 4:
            assert count == 2

    assert mock_api.await_count == 4
    assert mock_save.await_count == 4


async def test_purge_expired():
    purge_info = await premium.purge_expired_images()
    assert purge_info == "Purged 7 image(s) across 2 user(s)."


@patch("models.User.save", new_callable=AsyncMock)
async def test_on_member_update_wrong_guild(mock_save: AsyncMock, bot: BotchBot):
    member = Mock()
    member.guild.id = SUPPORTER_GUILD + 1

    await bot.on_member_update(member, member)
    mock_save.assert_not_awaited()


@patch("models.User.drop_premium")
@patch("models.User.gain_premium")
@patch("models.User.save", new_callable=AsyncMock)
async def test_on_member_update_wrong_role(
    mock_save: AsyncMock,
    mock_gain: Mock,
    mock_drop: Mock,
    bot: BotchBot,
):
    member = Mock()
    member.id = 1
    member.guild.id = SUPPORTER_GUILD
    member.get_role.return_value = None

    await bot.on_member_update(member, member)
    mock_gain.assert_not_called()
    mock_drop.assert_not_called()
    mock_save.assert_awaited_once()


@patch("models.User.drop_premium")
@patch("models.User.gain_premium")
@patch("models.User.save", new_callable=AsyncMock)
async def test_on_member_update_drop_premium(
    mock_save: AsyncMock,
    mock_gain: Mock,
    mock_drop: Mock,
    bot: BotchBot,
):
    before = Mock()
    before.id = 1
    before.guild.id = SUPPORTER_GUILD
    before.get_role.return_value = True

    after = Mock()
    after.id = 1
    after.guild.id = SUPPORTER_GUILD
    after.get_role.return_value = None

    await bot.on_member_update(before, after)
    mock_gain.assert_not_called()
    mock_drop.assert_called_once()
    mock_save.assert_awaited_once()


@patch("models.User.drop_premium")
@patch("models.User.gain_premium")
@patch("models.User.save", new_callable=AsyncMock)
async def test_on_member_update_gain_premium(
    mock_save: AsyncMock,
    mock_gain: Mock,
    mock_drop: Mock,
    bot: BotchBot,
):
    before = Mock()
    before.id = 1
    before.guild.id = SUPPORTER_GUILD
    before.get_role.return_value = None

    after = Mock()
    after.id = 1
    after.guild.id = SUPPORTER_GUILD
    after.get_role.return_value = True

    await bot.on_member_update(before, after)
    mock_gain.assert_called_once()
    mock_drop.assert_not_called()
    mock_save.assert_awaited_once()


def test_shared_singleton_user_store():
    bot = BotchBot()
    assert bot.user_store == premium.user_store
