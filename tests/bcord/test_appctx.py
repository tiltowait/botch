"""AppCtx tests."""

from unittest.mock import ANY, AsyncMock, Mock, patch

import discord
import pytest

from bot import AppCtx


@pytest.fixture
def ctx() -> AppCtx:
    bot = Mock()
    inter = AsyncMock()
    return AppCtx(bot, inter)


@pytest.mark.parametrize("ephemeral", [(True,), (False,)])
@patch("discord.Embed")
async def test_send_error(embed_mock: Mock, ctx: AppCtx, ephemeral: bool):
    title = "title"
    description = "description"

    await ctx.send_error(title, description, ephemeral=ephemeral)
    embed_mock.assert_called_once_with(
        title=title,
        description=description,
        color=discord.Color.brand_red(),
    )
    ctx.interaction.respond.assert_called_once_with(embed=ANY, ephemeral=ephemeral)


@pytest.mark.parametrize("ephemeral", [(True,), (False,)])
async def test_send_error_with_interaction(ctx: AppCtx, ephemeral: bool):
    inter = AsyncMock()
    await ctx.send_error("title", "desc", interaction=inter, ephemeral=ephemeral)

    ctx.interaction.respond.assert_not_called()
    inter.respond.assert_called_once_with(embed=ANY, ephemeral=ephemeral)
