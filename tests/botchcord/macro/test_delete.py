"""Macro deletion tests."""

from unittest.mock import ANY, AsyncMock

import pytest

from botch.bot import AppCtx
from botch.botchcord.macro.create import create_macro
from botch.botchcord.macro.delete import delete as delete_macro
from botch.core.characters import Character


@pytest.fixture
def char(character: Character) -> Character:
    character.add_trait("Strength", 3)
    character.add_trait("Brawl", 2)
    macro = create_macro(character, "punch", "str+br", 6, None)
    character.add_macro(macro)

    return character


@pytest.mark.parametrize(
    "macro_name,err",
    [
        ("punch", None),
        ("flabbergast", "Macro `flabbergast` not found."),
    ],
)
async def test_macro_deletion(
    mock_char_save: AsyncMock,
    mock_respond: AsyncMock,
    mock_send_error: AsyncMock,
    ctx: AppCtx,
    char: Character,
    macro_name: str,
    err: str | None,
):
    assert len(char.macros) == 1
    await delete_macro(ctx, char, macro_name)  # type: ignore

    if err:
        mock_send_error.assert_awaited_once_with("Error", err)
        assert len(char.macros) == 1
    else:
        mock_respond.assert_awaited_once_with(embed=ANY, ephemeral=True)
        assert not char.macros
        mock_char_save.assert_awaited_once()
