"""Test character haven class and decorator."""

from functools import partial
from typing import Callable
from unittest.mock import ANY, AsyncMock

import pytest
from discord.ui import Button, Select

import errors
from botchcord.haven import Haven
from core import cache
from core.characters import Character, GameLine, Splat
from tests.characters import gen_char


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache after every test."""
    cache._cache = {}
    yield
    cache._cache = {}


@pytest.fixture(autouse=True)
async def vamp() -> Character:
    vamp = gen_char(GameLine.WOD, Splat.VAMPIRE, name="Aaron")
    await vamp.save()
    return vamp


@pytest.fixture(autouse=True)
async def mortal() -> Character:
    mortal = gen_char(GameLine.WOD, Splat.MORTAL, name="Sally")
    await mortal.save()
    return mortal


@pytest.fixture
def ctx() -> AsyncMock:
    ctx = AsyncMock()
    ctx.guild.id = 0
    ctx.user.id = 0
    ctx.respond.return_value = "able"

    return ctx


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
    ctx: AsyncMock,
):
    haven = Haven(ctx, None, None, None, test)
    await haven._populate()
    assert haven._populated

    assert len(haven.chars) == expected


async def test_match_none(ctx: AsyncMock):
    haven = Haven(ctx, GameLine.COFD, Splat.VAMPIRE, None)
    with pytest.raises(errors.NoMatchingCharacter):
        await haven.get_match()


async def test_match_one(ctx: AsyncMock, vamp: Character):
    haven = Haven(ctx, GameLine.WOD, Splat.VAMPIRE, None)
    found = await haven.get_match()

    assert found is not None
    assert found.id == vamp.id, str(vamp.splat)


@pytest.mark.parametrize(
    "search_name,should_find",
    [
        ("Billy", True),
        ("Jimmy", False),
    ],
)
async def test_match_name(search_name: str, should_find: bool, ctx: AsyncMock, vamp: Character):
    vamp.name = "Billy"
    await vamp.save()

    haven = Haven(ctx, None, None, search_name)
    if should_find:
        found = await haven.get_match()
        assert found == vamp
    else:
        with pytest.raises(errors.NoMatchingCharacter):
            await haven.get_match()


async def test_buttons(ctx: AsyncMock, vamp: Character, mortal: Character):
    haven = Haven(ctx, GameLine.WOD, None, None)
    await haven._populate()
    haven._add_buttons()

    assert len(haven.children) == 2

    for i, char in enumerate([vamp, mortal]):
        btn = haven.children[i]
        assert isinstance(btn, Button)
        assert btn.label == char.name
        assert btn.callback == haven._callback


async def test_select(ctx: AsyncMock, vamp: Character, mortal: Character):
    # We need to add 3 more
    gc = partial(gen_char, line=GameLine.WOD, splat=Splat.MORTAL)
    c3 = gc(name="Z3")
    c4 = gc(name="Z4")
    c5 = gc(name="Z5")
    c6 = gc(name="Z6")

    await c3.save()
    await c4.save()
    await c5.save()
    await c6.save()

    haven = Haven(ctx, None, None, None)
    await haven._populate()
    assert len(haven.chars) == 6

    haven._add_buttons()
    assert len(haven.children) == 1

    sel = haven.children[0]
    assert sel.callback == haven._callback
    assert isinstance(sel, Select)

    chars = [vamp, mortal, c3, c4, c5, c6]
    for i, char in enumerate(chars):
        assert sel.options[i].label == char.name


async def test_send_selection(ctx: AsyncMock):
    haven = Haven(ctx, None, None, None)

    # We need to mock Haven.wait() so we don't lock up
    async def call_callback():
        inter = AsyncMock()
        inter.custom_id = haven.children[1].custom_id  # type: ignore
        await haven._callback(inter)

    mock_wait = AsyncMock()
    mock_wait.side_effect = call_callback
    haven.wait = mock_wait

    # This context will be removed once the function is implemented
    _ = await haven.get_match()

    # Make sure everything was called
    ctx.respond.assert_called_once_with(embed=ANY, view=haven, ephemeral=True)
    mock_wait.assert_called_once()

    assert haven.selected == haven.chars[1]
