"""Macro CRUD tests."""

from functools import partial

import pytest

from botch import errors
from botch.core.characters import Character, Macro

mc = partial(
    Macro,
    pool=["Strength", "+", "Brawl", "-", 1],
    keys=["Strength", "+", "Brawl", "-", 1],
    target=6,
    rote=False,
    hunt=False,
    comment=None,
)


def test_macro_insertion(character: Character):
    character.add_macro(mc(name="A"))
    character.add_macro(mc(name="C"))
    character.add_macro(mc(name="b"))

    macro_names = [m.name for m in character.macros]
    assert macro_names == ["A", "b", "C"]


def test_macro_already_exists(character: Character):
    character.add_macro(mc(name="A"))
    with pytest.raises(errors.MacroAlreadyExists):
        character.add_macro(mc(name="A"))
        assert len(character.macros) == 1


def test_find_macro(character: Character):
    expected = mc(name="A")
    character.add_macro(mc(name="C"))
    character.add_macro(mc(name="b"))
    character.add_macro(expected)

    macro = character.find_macro("a")
    assert macro == expected

    assert character.find_macro("unknown") is None


def test_delete_macro(character: Character):
    character.add_macro(mc(name="A"))
    character.add_macro(mc(name="C"))
    character.add_macro(mc(name="b"))

    assert len(character.macros) == 3

    character.remove_macro("b")
    assert len(character.macros) == 2

    macro_names = [m.name for m in character.macros]
    assert macro_names == ["A", "C"]


def test_delete_macro_not_found(character: Character):
    character.add_macro(mc(name="A"))

    with pytest.raises(errors.MacroNotFound):
        character.remove_macro("fake")

    assert len(character.macros) == 1
