import os
from unittest.mock import AsyncMock, mock_open, patch

import pytest

import api
from config import FC_BUCKET

os.environ["BOTCH_API_TOKEN"] = "test_token"


class Character:
    """Sample Character class for testing purposes."""

    def __init__(self, guild, user, id):
        self.guild = guild
        self.user = user
        self.id = id


@pytest.mark.asyncio
async def test_upload_faceclaim():
    character = Character(guild="guild1", user="user1", id="char1")
    image_url = "http://example.com/image.jpg"

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value="http://new_image_url.com")
        mock_post.return_value.__aenter__.return_value = mock_response

        new_url = await api.upload_faceclaim(character, image_url)
        assert new_url == "http://new_image_url.com"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_delete_single_faceclaim():
    image_url = f"https://{FC_BUCKET}/1234/5678.webp"

    with patch("aiohttp.ClientSession.delete") as mock_delete:
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value="Deleted")
        mock_delete.return_value.__aenter__.return_value = mock_response

        result = await api.delete_single_faceclaim(image_url)
        assert result is True
        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_character_faceclaims():
    character = Character(guild="guild1", user="user1", id="char1")

    with patch("aiohttp.ClientSession.delete") as mock_delete:
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value="All Deleted")
        mock_delete.return_value.__aenter__.return_value = mock_response

        await api.delete_character_faceclaims(character)
        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_upload_logs():
    with patch("glob.glob", return_value=["./logs/log1.txt", "./logs/log2.txt"]), patch(
        "builtins.open", mock_open(read_data="data")
    ), patch("aiohttp.ClientSession.post") as mock_post, patch("os.unlink") as mock_unlink:

        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value="Uploaded")
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await api.upload_logs()
        assert result is True
        assert mock_post.call_count == 2
        mock_unlink.assert_called_once_with("./logs/log1.txt")
