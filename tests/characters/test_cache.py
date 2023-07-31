"""Test the character cache."""

import copy

import pytest

import errors
from botch.cache import CharCache
from botch.characters import Character, GameLine, Splat


@pytest.fixture
def cache() -> CharCache:
    return CharCache()


@pytest.fixture
async def fcache(skilled) -> CharCache:
    one = copy.deepcopy(skilled)
    one.name = "One"
    one.line = GameLine.WOD
    one.splat = Splat.VAMPIRE
    await one.insert()

    two = copy.deepcopy(skilled)
    two.name = "Two"
    two.line = GameLine.COFD
    two.splat = Splat.MORTAL
    await two.insert()

    return CharCache()


@pytest.mark.parametrize(
    "guild,user,expected",
    [
        (1, 2, "1.2"),
        (0, 3, "0.3"),
    ],
)
def test_key(guild: int, user: int, expected: str, cache: CharCache):
    assert cache.key(guild, user) == expected


async def test_fetchall_empty(cache: CharCache):
    chars = await cache.fetchall(0, 0)
    assert not chars


@pytest.mark.parametrize(
    "guild,user,expected",
    [
        (0, 0, 2),
        (0, 1, 0),
        (1, 0, 0),
        (1, 1, 0),
    ],
)
async def test_count(guild: int, user: int, expected: int, fcache: CharCache):
    count = await fcache.count(guild, user)
    assert count == expected


async def test_fetchall_filled(fcache: CharCache):
    chars = await fcache.fetchall(0, 0)
    assert len(chars) == 2
    assert chars[0].name == "One"
    assert chars[1].name == "Two"


async def test_fetchnames(fcache: CharCache):
    names = await fcache.fetchnames(0, 0)
    assert names == ["One", "Two"]


@pytest.mark.parametrize(
    "guild,user,count",
    [
        (0, 0, 2),
        (0, 1, 0),
        (1, 0, 0),
        (1, 1, 0),
    ],
)
async def test_fetch_parameters_correct(guild: int, user: int, count: int, fcache: CharCache):
    chars = await fcache.fetchall(guild, user)
    assert len(chars) == count


@pytest.mark.parametrize(
    "name,fails",
    [
        ("One", False),
        ("Two", False),
        ("one", False),
        ("TwO", False),
        ("Three", True),
    ],
)
async def test_fetchone(name: str, fails: bool, fcache: CharCache):
    if fails:
        with pytest.raises(errors.CharacterNotFound):
            await fcache.fetchone(0, 0, name)
    else:
        char = await fcache.fetchone(0, 0, name)
        assert char.name.casefold() == name.casefold()


async def test_register(skilled: Character, fcache: CharCache):
    skilled.name = "Three"
    await fcache.register(skilled)

    found = await fcache.fetchone(0, 0, skilled.name)
    assert skilled == found

    names = await fcache.fetchnames(0, 0)
    assert len(names) == 3
    print(names)
    assert names == ["One", "Three", "Two"], "Names should be alphabetical!"


async def test_delete(skilled: Character, fcache: CharCache):
    with pytest.raises(errors.CharacterNotFound):
        await fcache.remove(skilled)

    expected = 2
    while expected > 0:
        chars = await fcache.fetchall(0, 0)
        assert expected == await fcache.count(0, 0)
        await fcache.remove(chars[0])
        expected -= 1

        assert expected == await fcache.count(0, 0)


@pytest.mark.parametrize(
    "line,splat,count,names",
    [
        (None, None, 2, ["One", "Two"]),
        (GameLine.WOD, None, 1, ["One"]),
        (GameLine.WOD, Splat.MORTAL, 0, []),
        (GameLine.WOD, Splat.VAMPIRE, 1, ["One"]),
        (None, Splat.VAMPIRE, 1, ["One"]),
        (None, Splat.MORTAL, 1, ["Two"]),
        (GameLine.COFD, None, 1, ["Two"]),
        (GameLine.COFD, Splat.VAMPIRE, 0, []),
        (GameLine.COFD, Splat.MORTAL, 1, ["Two"]),
    ],
)
async def test_splat_line_filtering(
    line: GameLine, splat: Splat, count: int, names: str, fcache: CharCache
):
    assert await fcache.count(0, 0, line=line, splat=splat) == count
    assert await fcache.fetchnames(0, 0, line=line, splat=splat) == names
