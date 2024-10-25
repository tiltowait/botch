"""Macro creation tests."""

from unittest.mock import Mock, patch

import pytest

import errors
from bot import AppCtx
from botchcord.macro.create import build_embed, can_use_macro
from botchcord.macro.create import create as create_cmd
from botchcord.macro.create import create_macro
from botchcord.utils import CEmbed
from core.characters import Character


@pytest.fixture
def char(character: Character) -> Character:
    character.add_trait("Strength", 3)
    character.add_trait("Brawl", 2)

    return character


@pytest.mark.parametrize(
    "pool,valid",
    [
        ("str+b", True),
        ("str+ath", False),
    ],
)
def test_can_create_macro(char: Character, pool: str, valid: bool):
    assert can_use_macro(char, pool) == valid


def test_macro_raises_bad_syntax(char: Character):
    with pytest.raises(errors.InvalidSyntax):
        can_use_macro(char, "this is not valid")


def test_create_macro(char):
    macro = create_macro(char, "punch", "str+b", 6, "punch a guy")
    assert macro.name == "punch"
    assert macro.pool == ["Strength", "+", "Brawl"]
    assert macro.target == 6
    assert macro.comment == "punch a guy"


def test_create_with_specs(char: Character):
    char.add_subtraits("Brawl", ["Grappling"])
    macro = create_macro(char, "grapple", ".g", 6, None)
    assert macro.pool[-1] == "Brawl (Grappling)"
    assert macro.keys[-1] == "Brawl.Grappling"


def test_build_embed(bot_mock, char):
    macro = create_macro(char, "punch", "str+b", 6, "punch a guy")
    embed = build_embed(bot_mock, char, macro)
    assert isinstance(embed, CEmbed)


@pytest.mark.parametrize(
    "pool,should_err",
    [
        ("dex+ath", True),
        ("Strength + Brawl", False),
    ],
)
@patch("botchcord.macro.create.build_embed")
async def test_create_cmd(
    embed_mock,
    mock_char_save,
    ctx: AppCtx,
    char: Character,
    pool: str,
    should_err: bool,
):
    expected_cembed = Mock()
    embed_mock.return_value = expected_cembed

    await create_cmd(ctx, char, "test", pool, 7, None)  # type: ignore

    if should_err:
        ctx.send_error.assert_awaited_once()
    else:
        ctx.respond.assert_awaited_once_with(embed=expected_cembed, ephemeral=True)
        mock_char_save.assert_awaited_once()

        assert len(char.macros) == 1
        macro = char.find_macro("test")
        assert macro is not None
        assert macro.name == "test"
        assert macro.pool_str == pool
        assert macro.target == 7
        assert macro.comment is None
