"""Virtue command tests."""

from unittest.mock import ANY, AsyncMock

import pytest

from botch.bot import AppCtx
from botch.botchcord.character import virtues as vr
from botch.core.characters import GameLine, Splat, Trait
from botch.core.characters.wod import Mortal, gen_virtues
from botch.errors import CharacterError
from tests.characters import gen_char


@pytest.fixture
def virtues() -> list[Trait]:
    return gen_virtues({"Conscience": 1, "SelfControl": 2, "Courage": 3})


@pytest.fixture
def char(virtues: list[Trait]) -> Mortal:
    return gen_char(GameLine.WOD, Splat.MORTAL, Mortal, virtues=virtues)


@pytest.mark.parametrize(
    "search,expected",
    [
        ("Conscience", "Conscience"),
        ("Conviction", "Conscience"),
        ("SelfControl", "SelfControl"),
        ("Instincts", "SelfControl"),
        ("Courage", "Courage"),
    ],
)
def test_find_virtue(virtues: list[Trait], search: str, expected: str):
    virtue = vr.find_virtue(virtues, search)
    assert virtue is not None
    assert virtue.name == expected


def test_find_virtue_missing(virtues: list[Trait]):
    missing = virtues.pop()
    assert vr.find_virtue(virtues, missing.name) is None


async def test_invalid_char_raises(ctx: AppCtx):
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    with pytest.raises(CharacterError):
        await vr.update(ctx, char, "", 0)


@pytest.mark.parametrize(
    "virtue,rating",
    [
        ("Conscience", 5),
        ("Conviction", 4),
    ],
)
async def test_update_command(
    mock_respond: AsyncMock,
    mock_char_save: AsyncMock,
    ctx: AppCtx,
    char: Mortal,
    virtue: str,
    rating: int,
):
    await vr.update(ctx, char, virtue, rating)
    assert char.virtues[0].name == virtue
    assert char.virtues[0].rating == rating

    mock_respond.assert_awaited_once_with(embed=ANY, ephemeral=True)
    mock_char_save.assert_awaited_once()


@pytest.mark.parametrize("index", [0, 1, 2])
async def test_update_inserts_virtue(
    mock_respond: AsyncMock,
    mock_char_save: AsyncMock,
    ctx: AppCtx,
    char: Mortal,
    index: int,
):
    virtue = char.virtues.pop(index)
    await vr.update(ctx, char, virtue.name, virtue.rating)
    assert char.virtues[index].name == virtue.name
    assert char.virtues[index].rating == virtue.rating

    mock_respond.assert_awaited_once_with(embed=ANY, ephemeral=True)
    mock_char_save.assert_awaited_once()
