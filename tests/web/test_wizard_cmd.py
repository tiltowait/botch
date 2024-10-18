"""Wizard schema creation tests."""

from unittest.mock import ANY, AsyncMock

import discord
import pytest

from botchcord.character.web import get_schema_file, wizard
from core.characters.factory import Schema
from web.models import WizardSchema


def test_wizard_schema_create():
    # Test both get_schema_file() and WizardSchema.create()
    sf = get_schema_file("vtm")
    ws = WizardSchema.create("guildy", sf)

    assert ws.guild_name == "guildy"
    assert isinstance(ws.traits, Schema)


def test_wizard_schema_fail():
    with pytest.raises(FileNotFoundError):
        WizardSchema.create("guildy", "fake")


@pytest.mark.parametrize("era", ["vtm", "dav20", "a"])
async def test_wizard(ctx: AsyncMock, era: str):
    if len(era) < 3:
        with pytest.raises(FileNotFoundError):
            await wizard(ctx, era)
    else:
        await wizard(ctx, era)
        ctx.respond.assert_awaited_once_with(embed=ANY, ephemeral=True)

        _, kwargs = ctx.respond.await_args
        embed = kwargs.get("embed")
        assert isinstance(embed, discord.Embed)
        assert embed.url is not None
