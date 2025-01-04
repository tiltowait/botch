"""Various settings handlers."""

import discord

from models import Guild


class GuildCache:
    """A cache that manages Guilds."""

    def __init__(self):
        self._cache: dict[int, Guild] = {}

    async def get_or_fetch(self, guild_id: int) -> Guild | None:
        """Gets the Guild from the cache. If it misses, fetch from the
        database. If that fails, return None."""
        if guild := self._cache.get(guild_id):
            return guild
        if guild := await Guild.find_one(Guild.guild == guild_id):
            self._cache[guild_id] = guild
            return guild

        return None


async def accessibility(ctx: discord.ApplicationContext) -> bool:
    """Whether to use accessibility mode for the current operation."""
    return False  # TODO: Implement!


async def use_emojis(ctx: discord.ApplicationContext) -> bool:
    """Whether to use emojis."""
    return not await accessibility(ctx)


cache = GuildCache()
