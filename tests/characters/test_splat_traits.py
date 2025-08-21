"""Splat-specific trait tests."""

import pytest

from botch.core.characters.base import Character, GameLine, Splat
from botch.core.characters.cofd import Vampire
from botch.core.characters.wod import Mortal, gen_virtues
from tests.characters import gen_char


@pytest.fixture
def wmortal() -> Mortal:
    virtues = gen_virtues({"Courage": 2, "SelfControl": 1, "Conscience": 4})
    char = gen_char(GameLine.WOD, Splat.MORTAL, Mortal, virtues=virtues)
    return char


@pytest.fixture
def cvampire() -> Vampire:
    return gen_char(
        GameLine.COFD,
        Splat.VAMPIRE,
        Vampire,
        blood_potency=7,
        vitae=20,
        max_vitae=20,
    )


@pytest.mark.parametrize(
    "char_fixture,traits",
    [
        ("wmortal", [("Courage", 2), ("SelfControl", 1), ("Conscience", 4)]),
        ("cvampire", [("Blood Potency", 7), ("Potency", 7)]),
    ],
)
def test_traits(request, char_fixture: str, traits: list[tuple[str, int]]):
    char: Character = request.getfixturevalue(char_fixture)

    for trait_name, rating in traits:
        found = char.match_traits(trait_name)

        assert len(found) == 1
        assert found[0].name == trait_name
        assert found[0].rating == rating
