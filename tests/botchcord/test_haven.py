"""Test character haven class and decorator."""

from functools import partial
from typing import Callable, Generator, cast
from unittest.mock import ANY, AsyncMock, Mock, PropertyMock, patch

import discord
import pytest
from discord.ui import Button, Select

import errors
from bot import AppCtx
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
def invoker() -> Mock:
    return Mock(id=10)


@pytest.fixture
def mock_admin_user() -> Generator[Mock, None, None]:
    with patch("bot.AppCtx.admin_user", new_callable=PropertyMock) as mock:
        yield mock


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
    haven = Haven(ctx, None, None, None, None, test)
    await haven._populate()
    assert haven._populated

    assert len(haven.chars) == expected


async def test_match_none(ctx: AsyncMock):
    haven = Haven(ctx, GameLine.COFD, Splat.VAMPIRE, None, None)
    with pytest.raises(errors.NoMatchingCharacter):
        await haven.get_match()


async def test_match_one(ctx: AsyncMock, vamp: Character):
    haven = Haven(ctx, GameLine.WOD, Splat.VAMPIRE, None, None)
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

    haven = Haven(ctx, None, None, search_name, None)
    if should_find:
        found = await haven.get_match()
        assert found == vamp
    else:
        with pytest.raises(errors.CharacterNotFound):
            await haven.get_match()


async def test_character_ineligible(ctx: AsyncMock, vamp: Character):
    await vamp.save()

    haven = Haven(ctx, None, None, vamp.name, None, lambda _: False)
    with pytest.raises(errors.CharacterIneligible):
        await haven.get_match()


@patch("botchcord.haven.Haven._populate", new_callable=AsyncMock)
async def test_character_match_character(populate_mock: AsyncMock, ctx: AsyncMock, vamp: Character):
    haven = Haven(ctx, None, None, vamp, None)
    v = await haven.get_match()
    assert v == vamp
    populate_mock.assert_not_awaited()


@patch("botchcord.haven.Haven.wait", new_callable=AsyncMock)
async def test_no_character_selected(
    wait_mock: AsyncMock,
    mock_respond: AsyncMock,
    mock_delete: AsyncMock,
    ctx: AsyncMock,
    vamp: Character,
    mortal: Character,
):
    await vamp.save()
    await mortal.save()

    haven = Haven(ctx, None, None, None, None)
    with pytest.raises(errors.NoCharacterSelected):
        await haven.get_match()

    mock_respond.assert_awaited_once_with(embed=ANY, view=haven, ephemeral=True)
    mock_delete.assert_awaited_once()
    wait_mock.assert_awaited_once()


async def test_buttons(ctx: AsyncMock, vamp: Character, mortal: Character):
    haven = Haven(ctx, GameLine.WOD, None, None, None)
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

    haven = Haven(ctx, None, None, None, None)
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


async def test_send_selection(mock_respond: AsyncMock, ctx: AppCtx):
    haven = Haven(ctx, None, None, None, None)

    # We need to mock Haven.wait() so we don't lock up
    async def call_callback():
        inter = Mock()
        inter.custom_id = haven.children[1].custom_id  # type: ignore
        await haven._callback(inter)

    with patch("botchcord.haven.Haven.wait", new_callable=AsyncMock) as mock_wait:
        mock_wait.side_effect = call_callback

        # This context will be removed once the function is implemented
        _ = await haven.get_match()

        # Make sure everything was called
        mock_respond.assert_awaited_once_with(embed=ANY, view=haven, ephemeral=True)
        mock_wait.assert_awaited_once()

        assert haven.selected == haven.chars[1]


async def test_haven_user_matches(ctx: AppCtx):
    haven = Haven(ctx, GameLine.WOD, Splat.VAMPIRE, None, None)
    char = await haven.get_match()
    assert char.user == ctx.author.id


@pytest.mark.parametrize("is_admin", [True, False])
@patch("bot.AppCtx.admin_user", new_callable=PropertyMock)
async def test_haven_admin_lookup(
    mock_admin_user: Mock,
    is_admin: bool,
    ctx: AppCtx,
    invoker: Mock,
    vamp: Character,
):
    mock_admin_user.return_value = is_admin

    # Override, since we are looking up another user's character
    owner = cast(discord.Member, ctx.author)
    ctx.interaction.user = invoker

    assert ctx.admin_user == is_admin

    if not is_admin:
        with pytest.raises(LookupError):
            _ = Haven(ctx, None, None, None, owner)
            print(owner.id, invoker.id)
    else:
        # In real use, the filtering will be by name, owner, and guild (part
        # of ctx). The mock user has 2 characters in this setup, so we disable
        # filtering by line and splat and instead supply only the name to be
        # sure we get the correct character.
        haven = Haven(ctx, None, None, vamp.name, owner)
        char = await haven.get_match()
        assert char.user == owner.id
        assert char.user != ctx.author.id
        assert char.name == vamp.name


@pytest.mark.parametrize("allow", [True, False])
async def test_allow_any(
    mock_admin_user: Mock,
    ctx: AppCtx,
    invoker: Mock,
    vamp: Character,
    allow: bool,
):
    mock_admin_user.return_value = False
    owner = cast(discord.Member, ctx.author)
    ctx.interaction.user = invoker

    if allow:
        haven = Haven(ctx, None, None, vamp.name, owner, permissive=True)
        char = await haven.get_match()
        assert char == vamp
    else:
        with pytest.raises(LookupError):
            haven = Haven(ctx, None, None, vamp.name, owner)
