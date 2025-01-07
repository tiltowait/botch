"""Bot instance tests."""

from typing import AsyncGenerator
from unittest import mock
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, PropertyMock, patch

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
    ctx.command = Mock()
    ctx.command.qualified_name = "command"
    return ctx


@pytest.fixture
async def mock_send_error() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.send_error", new_callable=AsyncMock) as mock:
        yield mock


async def test_on_connect(bot):
    with (
        mock.patch("bot.db.init", return_value=None),
        mock.patch("bot.BotchBot.sync_commands", return_value=None),
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
    mock_emoji.__str__.return_value = "😊"  # type:ignore

    # Mocking the guild object
    mock_guild = MagicMock()
    mock_guild.emojis = [mock_emoji]

    # Patching the get_guild method to return the mocked guild
    with patch.object(bot, "get_guild", return_value=mock_guild):
        if expected == errors.EmojiNotFound:
            with pytest.raises(errors.EmojiNotFound):
                bot.find_emoji(emoji_name, count)
        else:
            result = bot.find_emoji(emoji_name, count)
            assert result == expected


async def test_get_ctx(bot: BotchBot):
    inter = AsyncMock()
    ctx = await bot.get_application_context(inter)
    assert isinstance(ctx, AppCtx)


@pytest.mark.parametrize("error_cls", [errors.BotchError, errors.NotPremium])
async def test_send_error_message(
    mock_send_error: AsyncMock, bot: BotchBot, ctx: AppCtx, error_cls: type[errors.BotchError]
):
    msg = "This is a test"
    err = ApplicationCommandInvokeError(error_cls(msg))

    await bot.on_application_command_error(ctx, err)
    if isinstance(err.original, errors.NotPremium):
        mock_send_error.assert_awaited_once_with("This is a premium feature", ANY, ephemeral=True)
    else:
        mock_send_error.assert_awaited_once_with("Error", msg, ephemeral=True)


async def test_re_raise_error_message(bot: BotchBot, ctx: AppCtx):
    err = ApplicationCommandInvokeError(ValueError("test"))

    with pytest.raises(ValueError):
        await bot.on_application_command_error(ctx, err)


async def test_not_found_ignored(mock_send_error: AsyncMock, bot: BotchBot, ctx: AppCtx):
    err = ApplicationCommandInvokeError(NotFound(MagicMock(), None))
    await bot.on_application_command_error(ctx, err)
    mock_send_error.assert_not_called()


@pytest.mark.parametrize(
    "cmd,exists",
    [
        ("roll", True),
        ("blep", False),
    ],
)
@patch("bot.BotchBot.get_application_command")
def test_cmd_mention(mock_get_cmd: Mock, bot: BotchBot, cmd: str, exists: bool):
    # We can't use the real function, so let's just test our logic as we slave
    # over high code coverage.
    mock_get_cmd.return_value = Mock() if exists else None

    mention = bot.cmd_mention(cmd)
    if exists:
        assert mention is not None
    else:
        assert mention is None
