"""Non-PII user, aka player, data."""

from datetime import UTC, datetime, timedelta
from typing import ClassVar, Optional

from beanie import Document
from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    """Various user settings that follow across guilds."""

    accessibility: bool = False


class User(Document):
    """Store user settings and other necessities."""

    PURGE_INTERVAL: ClassVar[int] = 30  # Days

    user: int
    settings: UserSettings = Field(default_factory=UserSettings)
    left_premium: Optional[datetime] = None

    @property
    def should_purge(self) -> bool:
        """Whether enough time has elapsed that the user should purge premium data."""
        if not self.left_premium:
            return False

        purge_date = self.left_premium + timedelta(days=self.PURGE_INTERVAL)

        # There appears to be an idiosyncrasy with mongomock-motor that
        # requires us to force BOTH datetimes to be naive.
        return datetime.now(UTC).replace(tzinfo=None) > purge_date.replace(tzinfo=None)

    def drop_premium(self):
        """Mark the user as having left premium."""
        self.left_premium = datetime.now(UTC)

    class Settings:
        name = "users"
