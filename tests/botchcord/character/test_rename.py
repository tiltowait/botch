"""Character rename tests."""

from unittest.mock import ANY

import pytest

from botch.bot import AppCtx
from botch.botchcord.character.rename import rename, validate_name
from botch.core import cache
from botch.core.characters import Character, GameLine, Splat
from botch.errors import CharacterAlreadyExists
from tests.characters import gen_char


@pytest.fixture
def char() -> Character:
    return gen_char(GameLine.WOD, Splat.VAMPIRE, name="Nadea Theron")


@pytest.fixture(autouse=True)
async def register(char: Character):
    await cache.register(char)
    yield
    await cache.remove(char)


@pytest.mark.parametrize(
    "name,raises",
    [
        ("Billy", False),
        ("Nadea Theron", True),
    ],
)
async def test_validate_name(name: str, raises: bool):
    if raises:
        with pytest.raises(CharacterAlreadyExists):
            await validate_name(0, 0, GameLine.WOD, name)
    else:
        await validate_name(0, 0, GameLine.WOD, name)


async def test_rename_command_pass(mock_respond, ctx: AppCtx, char: Character):
    await rename(ctx, char, "Billy")
    mock_respond.assert_awaited_once_with(ANY, ephemeral=True)


async def test_rename_command_fail(ctx: AppCtx, char: Character):
    with pytest.raises(CharacterAlreadyExists):
        await rename(ctx, char, char.name)
