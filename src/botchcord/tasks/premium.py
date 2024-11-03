"""Premium data culling tasks."""

from botchcord.models import User


async def fetch_purgable_users() -> list[User]:
    """Fetch users who dropped premium a while ago."""
    users = await User.find({"left_premium": {"$ne": None}}).to_list()
    print(len(users))
    return [u for u in users if u.should_purge]
