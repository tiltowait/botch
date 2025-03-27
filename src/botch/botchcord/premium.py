from typing import Callable, NoReturn, TypeVar

import discord
from discord.ext import commands

from botch import errors
from botch.bot import AppCtx
from botch.config import SUPPORTER_GUILD, SUPPORTER_ROLE

T = TypeVar("T")


def is_supporter(ctx: AppCtx, user: discord.Member | None = None) -> bool:
    """Whether the user is a Patreon supporter.

    Args:
        ctx: The application context.
        user: The user in question. If not given, uses ctx.user.
    Returns:
        True if the user is a Patreon supporter (as determined by having the
        Supporter role).

    This function will always return False if SUPPORTER_GUILD and SUPPORTER_ROLE
    are not set!"""
    user = user or ctx.user
    assert user is not None

    support_server = ctx.bot.get_guild(SUPPORTER_GUILD)
    if support_server is None:
        return False

    member = support_server.get_member(user.id)
    return member is not None and member.get_role(SUPPORTER_ROLE) is not None


def _check_supporter(ctx: AppCtx) -> bool:
    """Check if the user is a supporter and raise appropriate exceptions if not.

    Args:
        ctx: The command context.
        user: The user to check. Defaults to the command invoker.

    Returns:
        bool: True if the user is a supporter.

    Raises:
        NotReady: If the bot is still initializing.
        LookupError: If the support server is not configured.
        NotPremium: If the user is not a supporter."""

    def raise_not_ready() -> NoReturn:
        cmd_name = ctx.command.qualified_name
        command = ctx.bot.cmd_mention(cmd_name) or f"`/{cmd_name}`"
        assert ctx.bot.user is not None
        raise errors.NotReady(
            (
                f"{ctx.bot.user.mention} is currently rebooting. "
                f"{command} will be available in a few minutes."
            )
        )

    # Waiting for the bot to be fully ready takes about 15 minutes. To speed
    # this up, we try to fetch supporter status as soon as it's available
    # instead of waiting for on_ready().
    if ctx.bot.get_guild(SUPPORTER_GUILD) is None:
        if not ctx.bot.welcomed:
            raise_not_ready()
        else:
            raise LookupError("Inconnu's support server is not configured!")

    if not is_supporter(ctx):
        if not ctx.bot.welcomed:
            # Support server members may still be fetching
            raise_not_ready()

        # User is definitively not a supporter
        raise errors.NotPremium

    return True


def premium() -> Callable[[T], T]:
    """A decorator for commands that only work for supporters."""
    return commands.check(_check_supporter)  # type: ignore
