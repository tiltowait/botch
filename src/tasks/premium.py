"""Premium data culling tasks."""

import logging
from datetime import UTC, time

from discord.ext import tasks

from core import cache
from core.characters import Character
from models import User


@tasks.loop(time=time(12, 0, tzinfo=UTC))
async def purge():
    """Cull inactive characters and guilds."""
    result = await purge_expired_images()
    logging.getLogger("TASK").info(result)


async def purge_expired_images() -> str:
    """Purge all images on expired premium.

    Returns the total purged images."""
    users = await fetch_purgeable_users()
    total_purged = 0
    for user in users:
        total_purged += await purge_images(user)

    return f"Purged {total_purged} image(s) across {len(users)} user(s)."


async def fetch_purgeable_users() -> list[User]:
    """Fetch users who dropped premium a while ago."""
    users = await User.find({"left_premium": {"$ne": None}}).to_list()
    return [u for u in users if u.should_purge]


async def fetch_purgeable_characters(user: User) -> list[Character]:
    """Fetch characters whose users dropped premium a while ago."""
    chars = await Character.find(Character.user == user.user).to_list()
    guilds = {c.guild for c in chars}

    # This could be a lot more efficient if the cache maintained a list of
    # characters per user instead of characters per user per guild. Maybe we
    # will make that change in the future; for now, however, we need to make
    # sure we are working with the characters from the cache rather than the
    # newly fetched characters, so we re-fetch them. The impact of this
    # operation should be minimal, since it happens asynchronously in the
    # background.
    user_chars: list[Character] = []
    for guild in guilds:
        chars = await cache.fetchall(guild, user.user)
        user_chars.extend(chars)

    return [c for c in user_chars if c.profile.images]


async def purge_images(user: User) -> int:
    """Purge all images uploaded by the user.

    Args:
        user (User): The user whose images to purge.

    Returns the number of characters purged."""
    chars = await fetch_purgeable_characters(user)
    total_purged = 0
    for char in chars:
        total_purged += len(char.profile.images)
        await char.delete_all_images()

    user.left_premium = None
    return total_purged
