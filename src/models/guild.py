"""Discord guild record classes."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal, Optional, overload

import discord
from beanie import Document, Indexed
from pydantic import BaseModel, Field


class GuildSettings(BaseModel):
    """Guild settings."""

    accessibility: bool = False


class Guild(Document):
    """A Guild stores name, join date, leave date, and settings."""

    guild: Annotated[int, Indexed(unique=True)]
    name: str
    joined: datetime = Field(default_factory=lambda: datetime.now(UTC))
    left: Optional[datetime] = None
    settings: GuildSettings = Field(default_factory=GuildSettings)

    async def join(self):
        """The bot re-joined the server."""
        if self.left is not None:
            self.left = None
            await self.save()

    async def leave(self):
        """The bot left the guild."""
        self.left = datetime.now(UTC)
        await self.save()

    async def rename(self, new_name: str):
        """Rename the Guild and save."""
        self.name = new_name
        await self.save()

    class Settings:
        name = "guilds"


class GuildCache:
    """A cache that manages Guilds."""

    def __init__(self):
        self._cache: dict[int, Guild] = {}
        self.logger = logging.getLogger("GUILD CACHE")

    async def _create(self, discord_guild: discord.Guild) -> Guild:
        """Create a new guild and save it."""
        self.logger.info(
            "Creating %s (ID: %s)",
            discord_guild.name,
            discord_guild.id,
        )
        guild = Guild(guild=discord_guild.id, name=discord_guild.name)
        await guild.save()

        self._cache[guild.guild] = guild
        return guild

    @overload
    async def fetch(self, discord_guild: discord.Guild) -> Guild | None: ...

    @overload
    async def fetch(self, discord_guild: discord.Guild, create: Literal[True]) -> Guild: ...

    @overload
    async def fetch(self, discord_guild: discord.Guild, create: Literal[False]) -> Guild | None: ...

    async def fetch(self, discord_guild: discord.Guild, create=False) -> Guild | None:
        """Gets the Guild from the cache. If it misses, fetch from the
        database. If that fails, return None."""
        if guild := self._cache.get(discord_guild.id):
            return guild
        if guild := await Guild.find_one(Guild.guild == discord_guild.id):
            self._cache[discord_guild.id] = guild
            return guild

        if create:
            guild = await self._create(discord_guild)
            return guild

        return None

    async def guild_joined(self, discord_guild: discord.Guild):
        """Mark the guild as having joined."""
        guild = await self.fetch(discord_guild, create=True)
        await guild.join()

    async def guild_left(self, discord_guild: discord.Guild):
        """Mark the guild as having left."""
        if guild := await self.fetch(discord_guild):
            await guild.leave()

    async def rename(self, discord_guild: discord.Guild, new_name: str):
        """The guild was renamed."""
        guild = await self.fetch(discord_guild, create=True)
        guild.name = new_name
        await guild.save()
