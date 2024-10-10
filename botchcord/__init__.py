"""This package houses the Discord-related code, apart from BotchBot."""

import discord

from botchcord import character, roll, settings

__all__ = ("character", "roll", "settings", "get_avatar")


def get_avatar(user: discord.User | discord.Member):
    """Get the user's avatar."""
    if isinstance(user, discord.User):
        # Users don't have a guild presence
        return user.display_avatar

    # Members can have a guild-specific avatar
    return user.guild_avatar or user.display_avatar
