"""Character select autogenerator tests."""

from functools import partial
from typing import Any
from unittest.mock import Mock

import pytest
from cachetools import TTLCache
from discord import OptionChoice

from botchcord.options import _available_characters as generate
from core.cache import cache
from core.characters import Character, GameLine, Splat
from tests.characters import gen_char


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache after every test."""
    cache._cache = TTLCache(maxsize=100, ttl=1800)
    yield
    cache._cache = TTLCache(maxsize=100, ttl=1800)


@pytest.fixture(autouse=True)
async def chars() -> list[Character]:
    gen = partial(gen_char, line=GameLine.WOD, splat=Splat.MORTAL)
    characters = [
        gen(name="Billy"),
        gen(name="Jimmy"),
        gen(name="Sally"),
        gen(name="Tommy"),
    ]
    for char in characters:
        await char.save()

    return characters


@pytest.fixture
def owner() -> Mock:
    owner = Mock()
    owner.id = 0
    owner.guild_permissions.administrator = False
    return owner


@pytest.fixture
def other_user() -> Mock:
    other_user = Mock()
    other_user.id = 1
    other_user.guild_permissions.administrator = False
    return other_user


@pytest.fixture
def admin() -> Mock:
    admin = Mock()
    admin.id = 10
    admin.guild_permissions.administrator = True
    return admin


@pytest.fixture
def ctx(request: Any) -> Mock:
    user = request.getfixturevalue(request.param)

    ctx = Mock()
    ctx.interaction.user = user
    ctx.interaction.guild.id = 0
    ctx.options = {"owner": 0}
    ctx.bot.user.id = 300
    ctx.value = ""

    return ctx


@pytest.mark.parametrize("ctx", ["owner", "other_user", "admin"], indirect=True)
def test_ctx_fixture(ctx: Mock):
    assert isinstance(ctx.interaction.guild.id, int)
    assert isinstance(ctx.interaction.user.id, int)
    assert isinstance(ctx.interaction.user.guild_permissions.administrator, bool)
    assert isinstance(ctx.bot.user.id, int)


@pytest.mark.parametrize("ctx", ["owner"], indirect=True)
async def test_own_lookup(ctx: Mock, chars: list[Character]):
    assert ctx.interaction.user.id == 0
    assert not ctx.interaction.user.guild_permissions.administrator

    options = await generate(ctx, False)
    assert len(options) == len(chars)
    assert frozenset(char.name for char in chars) == frozenset(name for name in options)


@pytest.mark.parametrize("ctx", ["other_user"], indirect=True)
async def test_other_user_lookup(ctx: Mock):
    assert ctx.interaction.user.id == 1
    assert not ctx.interaction.user.guild_permissions.administrator

    options = await generate(ctx, False)
    assert len(options) == 1
    assert isinstance(options[0], OptionChoice)
    assert options[0].value == ""


@pytest.mark.parametrize("ctx", ["other_user"], indirect=True)
async def test_other_user_lookup_permissive(ctx: Mock, chars: list[Character]):
    assert ctx.interaction.user.id == 1
    assert not ctx.interaction.user.guild_permissions.administrator

    options = await generate(ctx, True)
    assert len(options) == len(chars)
    assert frozenset(char.name for char in chars) == frozenset(name for name in options)


@pytest.mark.parametrize("ctx", ["admin"], indirect=True)
async def test_admin_lookup(ctx: Mock, chars: list[Character]):
    assert ctx.interaction.user.id == 10
    assert ctx.interaction.user.guild_permissions.administrator

    options = await generate(ctx, False)
    assert len(options) == len(chars)
    assert frozenset(char.name for char in chars) == frozenset(name for name in options)
