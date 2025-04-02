"""Macro roll tests."""

from unittest.mock import ANY, AsyncMock, patch

import pytest

from botch import errors
from botch.bot import AppCtx
from botch.botchcord.macro.create import create_macro
from botch.botchcord.mroll import mroll
from botch.core.characters import Character


@pytest.fixture
def char(character: Character) -> Character:
    character.add_trait("Strength", 4)
    character.add_trait("Brawl", 3)
    macro = create_macro(character, "punch", "str+b", 6, "original comment")
    character.add_macro(macro)

    return character


async def test_macro_not_found(ctx, char):
    with pytest.raises(errors.NoMatchingCharacter):
        await mroll(ctx, "fake", None, False, False, None, char)


@pytest.mark.parametrize(
    "diff,comment",
    [
        (None, None),
        (3, "Flip"),
    ],
)
@patch("botch.botchcord.roll.roll", new_callable=AsyncMock)
async def test_mroll(
    roll_mock: AsyncMock,
    ctx: AppCtx,
    char: Character,
    diff: int | None,
    comment: str | None,
):
    macro = char.macros[0]
    diff = diff or macro.target
    comment = comment or macro.comment
    await mroll(ctx, macro.name, diff, False, False, comment, char, autos=1)  # type: ignore

    roll_mock.assert_awaited_once_with(
        ctx,
        macro.key_str,
        diff,
        None,
        False,
        False,
        comment,
        char,
        autos=1,
        blessed=False,
        blighted=False,
    )


@patch("botch.botchcord.roll.Roll.save", new_callable=AsyncMock)
async def test_mroll_no_mock(
    mock_roll_save: AsyncMock, mock_respond: AsyncMock, ctx: AppCtx, char: Character
):
    await char.save()
    macro = char.macros[0]
    await mroll(ctx, macro.name, None, False, False, None, char)  # type: ignore
    mock_respond.assert_awaited_once_with(embed=ANY)
    mock_roll_save.assert_awaited_once()


@patch("botch.botchcord.roll.Roll.save", new_callable=AsyncMock)
async def test_mroll_specs(mock_roll_save: AsyncMock, ctx: AppCtx, char: Character, mock_respond):
    char.add_subtraits("Brawl", ["Grappling"])
    macro = create_macro(char, "specs", "str+b.g", 6, None)
    char.add_macro(macro)
    await mroll(ctx, macro.name, False, False, None, None, char)  # type: ignore

    mock_respond.assert_awaited_once_with(embed=ANY)
    mock_roll_save.assert_awaited_once()  # This is our proof it rolled


async def test_mroll_missing_trait(ctx: AppCtx, char: Character, mock_send_error):
    char.remove_trait("Brawl")
    await mroll(ctx, char.macros[0].name, None, False, False, None, char)  # type: ignore
    mock_send_error.assert_awaited_once_with("Error", ANY)
