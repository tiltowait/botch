"""Bot instance tests."""

from unittest import mock
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

import config
import errors
from bot import BotchBot


@pytest.fixture
def bot():
    return BotchBot()


async def test_on_connect(bot):
    with mock.patch("bot.db.init", return_value=None), mock.patch(
        "bot.BotchBot.sync_commands", return_value=None
    ):
        await bot.on_connect()


@patch.object(BotchBot, "user", new_callable=PropertyMock)
async def test_on_ready(mock_id, bot):
    mock_id.return_value.id = 3
    await bot.on_ready()
    assert config.BOT_ID == 3


@pytest.mark.parametrize(
    "emoji_name, count, expected",
    [
        ("smile", 1, "😊\u200b"),
        ("smile", 3, ["😊\u200b", "😊\u200b", "😊\u200b"]),
        ("not_found", 1, errors.EmojiNotFound),
    ],
)
def test_get_emoji(emoji_name, count, expected, bot):
    # Mocking the emoji object
    mock_emoji = MagicMock()
    mock_emoji.name = "smile"
    mock_emoji.__str__.return_value = "😊"

    # Mocking the guild object
    mock_guild = MagicMock()
    mock_guild.emojis = [mock_emoji]

    # Patching the get_guild method to return the mocked guild
    with patch.object(bot, "get_guild", return_value=mock_guild):
        if expected == errors.EmojiNotFound:
            with pytest.raises(errors.EmojiNotFound):
                bot.get_emoji(emoji_name, count)
        else:
            result = bot.get_emoji(emoji_name, count)
            assert result == expected
