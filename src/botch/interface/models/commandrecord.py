"""Facility for logging user commands."""

from datetime import UTC, datetime
from typing import Any, Optional, Self

from beanie import Document
from discord import ApplicationContext
from pydantic import Field


class CommandRecord(Document):
    """A database record for a user slash command. This is essentially the same
    data as is info-logged to the console."""

    command: str
    options: Optional[list[dict[str, Any]]]
    guild: Optional[int]
    user: int
    locale: Optional[str]
    date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    type: int

    @classmethod
    def from_context(cls, ctx: ApplicationContext) -> Self:
        """Create a record from an AppCtx."""
        record = cls(
            command=ctx.command.qualified_name,
            options=ctx.selected_options,
            guild=ctx.guild.id if ctx.guild else None,
            user=ctx.user.id,
            locale=ctx.interaction.locale,
            type=ctx.command.type,  # type: ignore
        )
        return record

    class Settings:
        name = "command_log"
