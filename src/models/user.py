"""Non-PII user, aka player, data."""

import logging
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

    def gain_premium(self):
        """Mark the user as having premium."""
        self.left_premium = None  # TODO: Track times left? Is that useful?

    def drop_premium(self):
        """Mark the user as having left premium."""
        self.left_premium = datetime.now(UTC)

    class Settings:
        name = "users"


class UserStore:
    """A cache for managing users."""

    def __init__(self):
        self._cache: dict[int, User] = {}
        self.logger = logging.getLogger("USER CACHE")
        self._populated = False

    async def _populate(self):
        """Pre-populate the cache with all user objects."""
        if not self._populated:
            users = await User.find().to_list()
            print(users)
            self._cache = {u.user: u for u in users}
            self._populated = True
        print(([(u.user, u.left_premium) for u in self._cache.values()]))

    async def fetch_purgeable(self) -> list[User]:
        """Users with purgable images due to dropping premium."""
        await self._populate()
        return [u for u in self._cache.values() if u.should_purge]

    async def fetch(self, user_id) -> User:
        """Fetch a user. If it doesn't exist, create it. Created user is not
        persisted in the database."""
        await self._populate()
        if user := self._cache.get(user_id):
            return user

        user = User(user=user_id)
        self._cache[user_id] = user

        # We don't save the user on creation, because most users never change
        # settings, and there's no benefit to keeping their records.
        return user


# Unlike the guild cache, we keep a singleton here because the premium
# culler would otherwise invalidate the bot's cache.
cache = UserStore()
