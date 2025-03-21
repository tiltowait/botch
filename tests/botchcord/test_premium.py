from unittest.mock import Mock, patch

import pytest

from botch import errors
from botch.botchcord.premium import _check_supporter, is_supporter, premium
from botch.config import SUPPORTER_GUILD, SUPPORTER_ROLE


@pytest.mark.parametrize("has_role", [True, False])
def test_is_supporter(ctx: Mock, has_role: bool):
    support_server = Mock()
    ctx.bot.get_guild.return_value = support_server

    member = Mock()
    support_server.get_member.return_value = member

    role = Mock() if has_role else None
    member.get_role.return_value = role

    result = is_supporter(ctx)

    ctx.bot.get_guild.assert_called_once_with(SUPPORTER_GUILD)
    support_server.get_member.assert_called_once_with(ctx.user.id)
    member.get_role.assert_called_once_with(SUPPORTER_ROLE)
    assert result == has_role


@pytest.mark.parametrize("support_server_exists", [True, False])
def test_is_supporter_no_server(ctx: Mock, support_server_exists: bool):
    ctx.bot.get_guild.return_value = Mock() if support_server_exists else None

    assert is_supporter(ctx) == support_server_exists
    ctx.bot.get_guild.assert_called_once_with(SUPPORTER_GUILD)


def test_is_supporter_custom_user(ctx: Mock):
    support_server = Mock()
    ctx.bot.get_guild.return_value = support_server

    custom_user = Mock()
    custom_user.id = 67890

    member = Mock()
    support_server.get_member.return_value = member

    role = Mock()
    member.get_role.return_value = role

    assert is_supporter(ctx, custom_user)
    ctx.bot.get_guild.assert_called_once_with(SUPPORTER_GUILD)
    support_server.get_member.assert_called_once_with(custom_user.id)
    member.get_role.assert_called_once_with(SUPPORTER_ROLE)


def test_check_supporter_success(ctx):
    ctx.bot.get_guild.return_value = Mock()
    ctx.bot.welcomed = True
    with patch("botch.botchcord.premium.is_supporter", return_value=True):
        assert _check_supporter(ctx) is True


def test_check_supporter_not_ready(ctx):
    ctx.bot.welcomed = False
    ctx.bot.get_guild.return_value = None
    with pytest.raises(errors.NotReady):
        _check_supporter(ctx)


def test_check_supporter_support_server_not_configured(ctx):
    ctx.bot.welcomed = True
    ctx.bot.get_guild.return_value = None
    with pytest.raises(LookupError, match="Inconnu's support server is not configured!"):
        _check_supporter(ctx)


def test_check_supporter_not_premium(ctx):
    ctx.bot.welcomed = True
    ctx.bot.get_guild.return_value = Mock()
    with patch("botch.botchcord.premium.is_supporter", return_value=False):
        with pytest.raises(errors.NotPremium):
            _check_supporter(ctx)


def test_check_supporter_not_premium_not_welcomed(ctx):
    ctx.bot.welcomed = False
    with patch("botch.botchcord.premium.is_supporter", return_value=False):
        with pytest.raises(errors.NotReady):
            _check_supporter(ctx)


def test_premium_decorator():
    @premium()
    async def mock_command(_):
        pass

    assert len(mock_command.__commands_checks__) == 1  # type:ignore
    assert mock_command.__commands_checks__[0] == _check_supporter  # type:ignore
