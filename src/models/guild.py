"""Discord guild record classes."""

from datetime import UTC, datetime
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


class GuildSettings(BaseModel):
    """Guild settings."""

    accessibility: bool = False


class Guild(Document):
    """A Guild stores name, join date, leave date, and settings."""

    guild: int
    name: str
    joined: datetime
    left: Optional[datetime] = None
    settings: GuildSettings = Field(default_factory=GuildSettings)

    @classmethod
    async def join(cls, id: int, name: str):
        """Bot joined the guild."""
        if guild := await Guild.find_one(Guild.guild == id):
            # Bot added back to old guild
            guild.left = None
        else:
            guild = cls(
                guild=id,
                name=name,
                joined=datetime.now(UTC),
            )
        await guild.save()

    @classmethod
    async def leave(cls, id: int):
        """The bot left the guild."""
        if guild := await Guild.find_one(Guild.guild == id):
            guild.left = datetime.now(UTC)
            await guild.save()

    @classmethod
    async def rename(cls, id: int, new_name: str):
        """Rename the Guild and save."""
        if guild := await Guild.find_one(Guild.guild == id):
            guild.name = new_name
            await guild.save()

    class Settings:
        name = "guilds"
