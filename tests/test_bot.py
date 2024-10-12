"""Bot instance tests."""

from unittest import mock
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from discord import ApplicationCommandInvokeError, NotFound

import config
import errors
from bot import AppCtx, BotchBot


@pytest.fixture
def bot():
    return BotchBot()


@pytest.fixture
def ctx(bot: BotchBot) -> AppCtx:
    ctx = AppCtx(bot, AsyncMock())
    ctx.send_error = AsyncMock()
    return ctx


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


async def test_get_ctx(bot: BotchBot):
    inter = AsyncMock()
    ctx = await bot.get_application_context(inter)
    assert isinstance(ctx, AppCtx)


async def test_send_error_message(bot: BotchBot, ctx: AppCtx):
    msg = "This is a test"
    err = ApplicationCommandInvokeError(errors.BotchError(msg))

    await bot.on_application_command_error(ctx, err)
    ctx.send_error.assert_awaited_once_with("Error", msg, ephemeral=True)


async def test_re_raise_error_message(bot: BotchBot, ctx: AppCtx):
    err = ApplicationCommandInvokeError(ValueError("test"))

    with pytest.raises(ValueError):
        await bot.on_application_command_error(ctx, err)


async def test_not_found_ignored(bot: BotchBot, ctx: AppCtx):
    err = ApplicationCommandInvokeError(NotFound(MagicMock(), None))
    await bot.on_application_command_error(ctx, err)
    ctx.send_error.assert_not_called()
