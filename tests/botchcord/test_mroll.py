"""Macro roll tests."""

from unittest.mock import ANY, AsyncMock, patch

import pytest

import errors
from bot import AppCtx
from botchcord.macro.create import create_macro
from botchcord.mroll import mroll
from core.characters import Character


@pytest.fixture
def char(character: Character) -> Character:
    character.add_trait("Strength", 4)
    character.add_trait("Brawl", 3)
    macro = create_macro(character, "punch", "str+b", 6, "original comment")
    character.add_macro(macro)

    return character


async def test_macro_not_found(ctx, char):
    with pytest.raises(errors.NoMatchingCharacter):
        await mroll(ctx, "fake", None, None, char)


@pytest.mark.parametrize(
    "diff,comment",
    [
        (None, None),
        (3, "Flip"),
    ],
)
@patch("botchcord.roll.roll", new_callable=AsyncMock)
async def test_mroll(
    roll_mock: AsyncMock,
    ctx: AppCtx,
    char: Character,
    diff: int | None,
    comment: str | None,
):
    macro = char.macros[0]
    diff = diff or macro.difficulty
    comment = comment or macro.comment
    await mroll(ctx, macro.name, diff, comment, char)  # type: ignore

    roll_mock.assert_awaited_once_with(
        ctx,
        " ".join(map(str, macro.pool)),
        diff,
        None,
        comment,
        char,
    )


@patch("botchcord.roll.Roll.save", new_callable=AsyncMock)
async def test_mroll_no_mock(mock_roll_save: AsyncMock, ctx: AppCtx, char: Character):
    await char.save()
    macro = char.macros[0]
    await mroll(ctx, macro.name, None, None, char)  # type: ignore
    ctx.respond.assert_awaited_once_with(embed=ANY)
    mock_roll_save.assert_awaited_once()


@patch("botchcord.roll.Roll.save", new_callable=AsyncMock)
async def test_mroll_specs(mock_roll_save: AsyncMock, ctx: AppCtx, char: Character):
    char.add_subtraits("Brawl", ["Grappling"])
    await mroll(ctx, char.macros[0].name, None, None, char)  # type: ignore

    ctx.respond.assert_awaited_once_with(embed=ANY)
    mock_roll_save.assert_awaited_once()  # This is our proof it rolled


async def test_mroll_missing_trait(ctx: AppCtx, char: Character):
    char.remove_trait("Brawl")
    await mroll(ctx, char.macros[0].name, None, None, char)  # type: ignore
    ctx.send_error.assert_awaited_once_with("Error", ANY)
