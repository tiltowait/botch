"""Fixture config."""

import re
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import discord
import pytest

import errors
from bot import AppCtx, BotchBot
from models.guild import GuildCache

# We use configure_mock(), because kwarg-based instantiation causes problems
# with pydantic.


@pytest.fixture
def guild() -> Mock:
    mock = Mock(spec=discord.Guild)
    everyone_role = Mock(spec=discord.Role)
    mock.default_role = everyone_role
    mock.configure_mock(id=0, name="Test Guild")
    return mock


@pytest.fixture
def user() -> Mock:
    return Mock(
        id=0,
        display_name="tiltowait",
        guild_avatar="https://example.com/img.png",
    )


@pytest.fixture
def bot() -> BotchBot:
    user = Mock(
        display_name="tiltowait",
        guild_avatar="https://example.com/img.png",
    )

    def find_emoji(name):
        if re.match(r"^((ss?|f|b)?\d+|no_dmg|bash)$", str(name)):
            return name  # The real deal adds \u200b, but we don't need that here
        raise errors.EmojiNotFound

    bot = BotchBot()
    bot.guild_cache = GuildCache()
    bot.get_user = Mock(return_value=user)
    bot.get_guild = Mock(return_value=Mock())
    bot.find_emoji = Mock(side_effect=find_emoji)

    bot._connection = Mock(user=Mock(mention="@MockBot"))
    bot.cmd_mention = Mock(return_value="/mock_command")

    return bot


@pytest.fixture
async def ctx(bot: BotchBot, guild: Mock, user: Mock) -> AsyncGenerator[AppCtx, None]:
    response_mock = Mock(
        is_done=Mock(return_value=False),
        defer=AsyncMock(),
    )
    perms = Mock(spec=discord.Permissions)
    type(perms).external_emojis = PropertyMock(return_value=True)
    channel = Mock(spec=discord.TextChannel)
    channel.permissions_for.return_value = perms

    inter = AsyncMock(
        guild=guild,
        user=user,
        channel=channel,
        response=response_mock,
    )

    ctx = AppCtx(bot, inter)
    ctx.command = Mock(qualified_name="mock_command")
    yield ctx


@pytest.fixture
async def mock_respond() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.respond", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
async def mock_send_error() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.send_error", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
async def mock_edit() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.edit", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
async def mock_delete() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.delete", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
async def mock_send_modal() -> AsyncGenerator[AsyncMock, None]:
    with patch("bot.AppCtx.send_modal", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
async def mock_is_done() -> AsyncGenerator[Mock, None]:
    with patch("discord.InteractionResponse.is_done") as mock:
        yield mock


@pytest.fixture
async def mock_defer() -> AsyncGenerator[AsyncMock, None]:
    with patch("discord.InteractionResponse.defer", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_char_save():
    with patch("core.characters.Character.save", new_callable=AsyncMock) as mocked:
        yield mocked
