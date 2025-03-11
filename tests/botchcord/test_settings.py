"""Guild settings tests. The tests here are trivial for now but exist as a
reminder to write thorough tests once the settings system is written, since
they will fail once that work is done."""

from typing import Any, NamedTuple, cast
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from discord import (
    ButtonStyle,
    Guild,
    PartialMessageable,
    Permissions,
    Role,
    TextChannel,
)
from discord.ui import Button

from bot import AppCtx
from botchcord import settings
from models import Guild, User


class A11yParams(NamedTuple):
    guild: bool
    user: bool
    expected: bool


A11Y_TEST_CASES = [
    A11yParams(False, False, False),
    A11yParams(True, False, True),
    A11yParams(False, True, True),
    A11yParams(True, True, True),
]


@pytest.fixture
def mock_ctx() -> Any:
    ctx = Mock()
    ctx.interaction = Mock()
    return ctx


def test_external_emojis_dms(mock_ctx):
    mock_ctx.interaction.guild = None
    assert settings.can_use_external_emoji(mock_ctx) is True


def test_external_emojis_missing_channel(mock_ctx):
    mock_ctx.interaction.guild = Mock(spec=Guild)
    mock_ctx.interaction.channel = None

    assert settings.can_use_external_emoji(mock_ctx) is False


def test_external_emojis_partialmessageable(mock_ctx):
    mock_ctx.interaction.guild = Mock(spec=Guild)
    mock_ctx.interaction.channel = Mock(spec=PartialMessageable)

    assert settings.can_use_external_emoji(mock_ctx) is False


@pytest.mark.parametrize("able", [True, False])
def test_external_emojis_everyone_role(mock_ctx, able: bool):
    guild = Mock(spec=Guild)
    channel = Mock(spec=TextChannel)
    everyone_role = Mock(spec=Role)
    perms = Mock(spec=Permissions)
    type(perms).external_emojis = PropertyMock(return_value=able)

    channel.permissions_for.return_value = perms
    guild.default_role = everyone_role
    mock_ctx.interaction.guild = guild
    mock_ctx.interaction.channel = channel

    assert settings.can_use_external_emoji(mock_ctx) == able


async def test_accessibility(ctx: AppCtx):
    assert await settings.accessibility(ctx) is False


async def test_use_emojis(ctx: AppCtx):
    assert await settings.use_emojis(ctx) != await settings.accessibility(ctx)


@pytest.mark.parametrize("a11y", A11Y_TEST_CASES)
async def test_settings_logic(ctx: AppCtx, a11y: A11yParams):
    guild = Mock()
    guild.settings.accessibility = a11y.guild

    user = Mock()
    user.settings.accessibility = a11y.user

    with (
        patch.object(ctx.bot.guild_cache, "fetch", new_callable=AsyncMock) as guild_fetch,
        patch.object(ctx.bot.user_store, "fetch", new_callable=AsyncMock) as user_mock,
    ):
        guild_fetch.return_value = guild
        user_mock.return_value = user

        assert await settings.accessibility(ctx) == a11y.expected
        assert await settings.use_emojis(ctx) != a11y.expected


@pytest.mark.parametrize("a11y", A11Y_TEST_CASES)
@pytest.mark.parametrize("admin", [False, True])
@patch("bot.AppCtx.admin_user", new_callable=PropertyMock)
async def test_settings_control_states(
    mock_admin: PropertyMock,
    ctx: AppCtx,
    admin: bool,
    a11y: A11yParams,
):
    mock_admin.return_value = admin
    ctx.bot.guild_cache.clear()
    ctx.bot.user_store.clear()

    # We don't use a fixture, because we need to parametrize the states
    guild = Guild(guild=0, name="Test Guild")
    guild.settings.accessibility = a11y.guild
    await guild.save()

    user = User(user=0)
    user.settings.accessibility = a11y.user
    await user.save()

    assert ctx.guild.id == guild.guild
    assert ctx.author.id == user.user

    view = settings.SettingsView(ctx)
    await view._populate_buttons()

    user_a11y_btn = cast(Button, view.children[0])
    assert user_a11y_btn.style == ButtonStyle.secondary if a11y.user else ButtonStyle.primary

    guild_a11y_btn = cast(Button, view.children[1])
    assert guild_a11y_btn.disabled != admin
    assert guild_a11y_btn.style == ButtonStyle.secondary if a11y.guild else ButtonStyle.primary
    if guild_a11y_btn.disabled:
        assert guild_a11y_btn.callback != view.toggle_guild_a11y

    # Test toggles. Eventually this might need to be split up if we have lots
    # of settings, but for now we'll keep them grouped together.

    inter = AsyncMock()

    with patch("models.user.User.save", new_callable=AsyncMock) as mock_user_save:
        await view.toggle_user_a11y(inter)
        mock_user_save.assert_awaited_once()

        user = await ctx.bot.user_store.fetch(user.user)  # Need to get cached object
        assert user.settings.accessibility != a11y.user
        user_a11y_btn = cast(Button, view.children[0])
        assert user_a11y_btn.style == ButtonStyle.primary if a11y.user else ButtonStyle.secondary

    if admin:
        with patch("models.guild.Guild.save", new_callable=AsyncMock) as mock_guild_save:
            await view.toggle_guild_a11y(inter)
            mock_guild_save.assert_awaited_once()

            guild = await ctx.bot.guild_cache.fetch(ctx.guild, create=True)
            assert guild.settings.accessibility != a11y.guild
            guild_a11y_btn = cast(Button, view.children[1])
            assert (
                guild_a11y_btn.style == ButtonStyle.primary if a11y.guild else ButtonStyle.secondary
            )
