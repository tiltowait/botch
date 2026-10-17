"""The Botch API endpoints."""

import functools
import json
import logging
import os
import re
import time
from functools import partial
from typing import Any
from urllib.parse import urlparse

import aiohttp
import async_timeout

from botch import core, errors
from botch.config import FC_BUCKET

dumps = partial(json.dumps, default=str)

# An argument can be made that these should simply live with their appropriate
# command counterparts, but I see a value in keeping them together.

BASE_API = "https://api.botch.lol/"

logger = logging.getLogger("API")


def measure(func):
    """A decorator that measures API response time."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        val = await func(*args, **kwargs)
        end = time.perf_counter()

        logger.info("%s finished in %.3fs", kwargs["path"], end - start)

        return val

    return wrapper


def headers() -> dict[str, str]:
    """The API's authorization header."""
    return {"Authorization": os.getenv("BOTCH_API_TOKEN", "")}


async def upload_faceclaim(character: "core.characters.Character", image_url: str) -> str:
    """Uploads a faceclaim to cloud storage."""
    payload = {
        "guild": character.guild,
        "user": character.user,
        "charid": character.id,
        "image_url": image_url,
        "bucket": FC_BUCKET,
    }
    new_url = await _post(path="/faceclaim/upload", data=dumps(payload))

    return new_url


async def delete_single_faceclaim(image: str) -> bool:
    """Delete a single faceclaim image."""
    url = urlparse(image)
    if url.netloc != FC_BUCKET:
        return False

    if (match := re.match(r"/([A-F0-9a-f]+/[A-F0-9a-f]+\.webp)$", url.path)) is None:
        return False

    key = match.group(1)
    res = await _delete(path=f"/faceclaim/delete/{FC_BUCKET}/{key}")
    logger.debug("%s", res)

    return True


async def delete_character_faceclaims(character: "core.characters.Character"):
    """Delete all of a character's faceclaims."""
    res = await _delete(path=f"/faceclaim/delete/{FC_BUCKET}/{character.id}/all")
    logger.info("%s", res)


@measure
async def _post(*, path: str, data: dict[str, Any] | str) -> str:
    """Send an API POST request."""
    logger.debug("POST to %s with %s", path, str(data))
    url = BASE_API + path.lstrip("/")

    async with (
        async_timeout.timeout(60),
        aiohttp.ClientSession(headers=headers()) as session,
        session.post(url, data=data) as response,
    ):
        json = await response.json()

        if not response.ok:
            raise errors.ApiError(str(json))
        return json


@measure
async def _delete(*, path: str) -> str:
    """Send an API DELETE request."""
    logger.debug("DELETE to %s", path)
    url = BASE_API + path.lstrip("/")

    async with (
        async_timeout.timeout(60),
        aiohttp.ClientSession(headers=headers()) as session,
        session.delete(url) as response,
    ):
        json = await response.json()

        if not response.ok:
            raise errors.ApiError(str(json))
        return json
