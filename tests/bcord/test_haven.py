"""Test character haven class and decorator."""

from typing import Callable
from unittest.mock import Mock

import pytest

from botchcord.haven import Haven
from core import cache
from core.characters import Character, GameLine, Splat
from tests.characters import gen_char


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache after every test."""
    yield
    cache._cache = {}


@pytest.fixture(autouse=True)
async def vamp() -> Character:
    vamp = gen_char(GameLine.WOD, Splat.VAMPIRE)
    await vamp.save()
    return vamp


@pytest.fixture(autouse=True)
async def mortal() -> Character:
    mortal = gen_char(GameLine.WOD, Splat.MORTAL)
    await mortal.save()
    return mortal


@pytest.fixture
def ctx() -> Mock:
    ctx = Mock()
    ctx.guild.id = 0
    ctx.user.id = 0

    return ctx


async def prep_chars() -> tuple[Character, Character]:
    vamp = gen_char(GameLine.WOD, Splat.VAMPIRE)
    await vamp.save()

    mortal = gen_char(GameLine.WOD, Splat.MORTAL)
    await mortal.save()

    return vamp, mortal


@pytest.mark.parametrize(
    "expected,test",
    [
        (2, lambda _: True),
        (1, lambda c: c.splat == Splat.VAMPIRE),
    ],
)
async def test_filtering_func(
    expected: int,
    test: Callable[[Character], bool],
    ctx: Mock,
):
    # await prep_chars()
    haven = Haven(ctx, None, None, None, test)
    await haven._populate()
    assert haven._populated

    assert len(haven.chars) == expected


async def test_match_none(ctx: Mock):
    haven = Haven(ctx, GameLine.COFD, Splat.VAMPIRE, None)
    found = await haven.get_match()
    assert found is None


async def test_match_one(ctx: Mock, vamp: Character):
    haven = Haven(ctx, GameLine.WOD, Splat.VAMPIRE, None)
    found = await haven.get_match()

    assert found is not None
    assert found.id == vamp.id, str(vamp.splat)
