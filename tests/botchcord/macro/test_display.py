"""Macro display tests."""

from unittest.mock import AsyncMock, patch

import pytest
from discord.ext.pages import Paginator

from bot import AppCtx
from botchcord.macro.display import create_macro_entry, create_paginator
from botchcord.macro.display import display as display_cmd
from botchcord.macro.display import paginate_macros
from botchcord.utils.text import i, m
from core.characters import Character, Macro


@pytest.fixture
def macro() -> Macro:
    return Macro(
        name="punch",
        pool=["Strength", "+", "Brawl"],
        keys=["Strength", "+", "Brawl"],
        target=6,
        rote=False,
        hunt=False,
        comment="Punch a guy",
    )


@pytest.fixture
def char(character: Character, macro: Macro) -> Character:
    character.add_trait("Strength", 3)
    character.add_trait("Brawl", 2)
    character.add_macro(macro)

    return character


def test_create_macro_entry(macro: Macro):
    entry = create_macro_entry(macro)
    lines = [
        f"### {macro.name}",
        f"**Pool:** {m(macro.pool_str)}",
        f"**Difficulty:** {macro.target}",
        i(macro.comment),
    ]
    assert entry == "\n".join(lines)


def test_paginate_macros(macro: Macro):
    per_entry = len(create_macro_entry(macro)) + 1  # Add for \n
    macros_per_page = 2000 // per_entry
    print(macros_per_page, per_entry)
    num_pages = 3

    macros = [macro] * (macros_per_page * num_pages)
    pages = paginate_macros(macros)

    assert len(pages) == 3
    pool_count = pages[0].count("Pool:")
    assert pool_count == macros_per_page


async def test_create_paginator(bot_mock, char: Character):
    paginator = create_paginator(bot_mock, char)
    assert isinstance(paginator, Paginator)


@patch("discord.ext.pages.Paginator.respond", new_callable=AsyncMock)
async def test_display_cmd(mock_respond: AsyncMock, ctx: AppCtx, char: Character):
    await display_cmd(ctx, char)
    mock_respond.assert_awaited_once_with(ctx.interaction, ephemeral=True)
