"""AppCtx tests."""

from unittest.mock import ANY, AsyncMock, Mock, patch

import discord
import pytest

from botch.bot import AppCtx


@pytest.mark.parametrize("ephemeral", [(True,), (False,)])
@patch("discord.Embed")
async def test_send_error(embed_mock: Mock, mock_respond: AsyncMock, ctx: AppCtx, ephemeral: bool):
    title = "title"
    description = "description"

    await ctx.send_error(title, description, ephemeral=ephemeral)
    embed_mock.assert_called_once_with(
        title=title,
        description=description,
        color=discord.Color.brand_red(),
    )
    mock_respond.assert_awaited_once_with(embed=ANY, ephemeral=ephemeral)


@pytest.mark.parametrize("ephemeral", [(True,), (False,)])
async def test_send_error_with_interaction(mock_respond: AsyncMock, ctx: AppCtx, ephemeral: bool):
    inter = AsyncMock()
    await ctx.send_error("title", "desc", interaction=inter, ephemeral=ephemeral)

    mock_respond.assert_not_awaited()
    inter.respond.assert_awaited_once_with(embed=ANY, ephemeral=ephemeral)
