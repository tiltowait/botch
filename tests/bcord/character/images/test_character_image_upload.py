"""Character image upload tests."""

from typing import AsyncGenerator
from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest

from bot import AppCtx
from botchcord.character.images.upload import build_embed, upload_image, valid_url
from core.characters import Character

MOCKED_URL = "https://pcs.botch.lol/fake/char/img.webp"


@pytest.fixture(autouse=True)
async def mock_api_upload() -> AsyncGenerator[AsyncMock, None]:
    with patch("api.upload_faceclaim", new_callable=AsyncMock) as mocked:
        mocked.return_value = MOCKED_URL
        yield mocked


@pytest.mark.parametrize(
    "url,valid",
    [
        ("https://example.com/image.png", True),
        ("https://example.com/image.webp", True),
        ("https://example.com/image.jpg", True),
        ("https://example.com/image.jpeg", True),
        ("https://example.com/image.fake", False),
    ],
)
def test_valid_url(url: str, valid: bool):
    assert valid_url(url) == valid


async def test_invalid_url(ctx: AppCtx, character: Character):
    image = Mock()
    image.url = "https://example.com/invalid.html"

    await upload_image(ctx, character, image)
    ctx.send_error.assert_awaited_once()


def test_build_embed(ctx: AppCtx, character: Character):
    embed = build_embed(ctx.bot, character, MOCKED_URL)
    assert embed.title == "Image uploaded!"
    assert embed.author is not None
    assert embed.author.name == character.name
    assert embed.thumbnail is None
    assert embed.image is not None
    assert embed.image.url == MOCKED_URL


async def test_upload(mock_api_upload: AsyncMock, ctx: AppCtx, character: Character):
    image = Mock()
    image.url = "https://example.com/image.png"

    await upload_image(ctx, character, image)
    ctx.interaction.response.is_done.assert_called_once()
    ctx.interaction.response.defer.assert_awaited_once_with(ephemeral=True, invisible=False)

    assert str(character.profile.images[0]) == MOCKED_URL
    mock_api_upload.assert_awaited_once_with(character, image.url)
    ctx.respond.assert_awaited_once_with(embed=ANY, ephemeral=True)
    character.save.assert_awaited_once()
