"""Discord guild record classes."""

from datetime import UTC, datetime
from typing import Annotated, Optional

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

    async def fetch(self, guild_id: int) -> Guild | None:
        """Gets the Guild from the cache. If it misses, fetch from the
        database. If that fails, return None."""
        if guild := self._cache.get(guild_id):
            return guild
        if guild := await Guild.find_one(Guild.guild == guild_id):
            self._cache[guild_id] = guild
            return guild

        return None

    async def guild_joined(self, guild_id: int, name: str):
        """Mark the guild as having joined."""
        if guild := self._cache.get(guild_id):
            await guild.join()
        else:
            guild = Guild(guild=guild_id, name=name)
            self._cache[guild_id] = guild
            await guild.save()

    async def guild_left(self, guild_id: int):
        """Mark the guild as having left."""
        if guild := await self.fetch(guild_id):
            await guild.leave()

    async def rename(self, guild_id: int, new_name: str):
        """The guild was renamed."""
        if guild := await self.fetch(guild_id):
            await guild.rename(new_name)
        else:
            guild = Guild(guild=guild_id, name=new_name)
            await guild.save()
