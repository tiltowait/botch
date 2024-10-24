"""Commonly used slash command options and helpers."""

import logging
from typing import cast

import discord
from discord.commands import Option, OptionChoice

import core
from config import GAME_LINE
from core.characters.base import GameLine


def promoted_choice(
    param: str,
    description: str,
    *,
    start: int,
    end: int,
    first: int | None = None,
    required=True,
):
    """An option that creates a list of numbers between start and end,
    inclusive. If first is specified, then that element is presented first."""

    def decorator(func):
        choices = list(range(start, end + 1))
        if first in choices:
            choices.remove(first)
            choices.insert(0, first)

        func.__annotations__[param] = Option(
            int,
            description,
            name=param,
            required=required,
            choices=choices,
        )
        return func

    return decorator


def character(description="The character to use", required=False, param="character"):
    """A command decorator letting users choose a character."""

    def decorator(func):
        func.__annotations__[param] = Option(
            str,
            description,
            name=param,
            autocomplete=_available_characters,
            required=required,
        )
        return func

    return decorator


async def _available_characters(ctx: discord.AutocompleteContext):
    """Generate a list of the user's available characters."""
    logger = logging.getLogger("CHAR_OPTION")

    if (guild := ctx.interaction.guild) is None:
        return []

    # Set up some casts so the type checker is happy
    bot_user = cast(discord.ClientUser, ctx.bot.user)
    user = cast(discord.Member, ctx.interaction.user)

    # Check if they're looking up a player and have lookup permissions
    spcs = []

    if (owner := (ctx.options.get("owner") or ctx.options.get("current_owner"))) is not None:
        if owner != user.id and not user.guild_permissions.administrator:
            return [OptionChoice("You do not have admin permissions", "")]
    else:
        owner = user.id

        if user.guild_permissions.administrator:
            # Add SPCs
            spcs = await core.cache.fetchnames(guild.id, bot_user.id, GameLine(GAME_LINE))
            logger.info(
                "%s: admin %s fetched %s SPCs",
                guild.name,
                user.name,
                len(spcs),
            )

    chars = await core.cache.fetchnames(guild.id, int(owner))
    chars.extend(spcs)

    name_search = ctx.value.casefold()

    found_chars = [name for name in chars if name.casefold().startswith(name_search or "")]

    if len(found_chars) > 25:
        instructions = "Keep typing ..." if ctx.value else "Start typing a name."
        return [OptionChoice(f"Too many characters to display. {instructions}", "")]
    return found_chars
