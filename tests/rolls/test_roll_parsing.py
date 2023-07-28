"""Various roll-parsing tests."""

import errors
import pytest

from botch.characters import Character, GameLine
from botch.rolls.parse import RollParser


@pytest.mark.parametrize(
    "syntax,expected,should_fail",
    [
        ("3", [3], False),
        ("foo", ["foo"], False),
        ("3 + foo", [3, "+", "foo"], False),
        ("foo + 3", ["foo", "+", 3], False),
        ("foo.bar", ["foo.bar"], False),
        (". - ..", [".", "-", ".."], False),
        ("foo + .bar - 2", ["foo", "+", ".bar", "-", 2], False),
        ("foo3", None, True),
        ("3foo", None, True),
        ("foo.3", None, True),
        ("3.bar", None, True),
        ("3 / 2", None, True),
        ("3 3", None, True),
        ("foo bar", None, True),
        ("foo 3", None, True),
        ("3 foo", None, True),
    ],
)
def test_roll_prep(syntax: str, expected: list[str | int], should_fail: bool):
    p = RollParser(syntax, None)

    if should_fail:
        with pytest.raises(errors.InvalidSyntax):
            p.tokenize()
    else:
        parsed = p.tokenize()
        assert parsed == expected


@pytest.mark.parametrize(
    "syntax,needs_character",
    [
        ("3", False),
        ("3 + 2 - 1", False),
        ("foo", True),
        ("foo + 3", True),
        ("3 - foo", True),
        (".", True),
        ("3 + .", True),
        (". + 3", True),
        ("3 + wp", False),
        ("3 + WP", False),
        ("W+P", True),
    ],
)
def test_needs_character(syntax: str, needs_character: bool):
    p = RollParser(syntax, None)
    assert needs_character == p.needs_character


@pytest.mark.parametrize(
    "syntax,spec",
    [
        (".", True),
        ("3", False),
        ("3 + 2", False),
        ("foo", False),
        ("foo + bar.baz", True),
    ],
)
def test_spec_detection(syntax: str, spec: bool):
    p = RollParser(syntax, None)
    assert p.specialty_used == spec


@pytest.mark.parametrize(
    "syntax,pool,equation,dice,error",
    [
        ("3 + 2", [3, "+", 2], [3, "+", 2], 5, None),
        ("stren + br - 3", ["Strength", "+", "Brawl", "-", 3], [2, "+", 3, "-", 3], 2, None),
        ("stren + .k", ["Strength", "+", "Brawl (Kindred)"], [2, "+", 3], 5, None),
        ("str", None, None, None, errors.AmbiguousTraitError),
        ("brawl + foo", None, None, None, errors.TraitNotFound),
    ],
)
def test_parse(syntax, pool, equation, error, dice, skilled: Character):
    p = RollParser(syntax, skilled)

    if error is not None:
        with pytest.raises(error):
            p.parse()
    else:
        p.parse()
        assert p.pool == pool
        assert p.equation == equation


@pytest.mark.parametrize(
    "syntax,willpower",
    [
        ("stren + br", False),
        ("stren + br + wp", True),
        ("3", False),
    ],
)
def test_willpower_in_roll(syntax: str, willpower: bool, skilled: Character):
    p = RollParser(syntax, skilled)
    p.parse()
    assert p.using_wp == willpower


@pytest.mark.parametrize(
    "syntax,willpower,expected",
    [
        ("strength + brawl", False, 5),
        ("strength + brawl + wp", True, 5),
        ("wp", True, 0),
        ("3", False, 3),
        ("3 + WP", True, 3),
    ],
)
def test_willpower_roll_impact(
    syntax: str, willpower: bool, expected: int, skilled: Character, line: GameLine
):
    skilled.line = line  # Safe to do only on the base class

    p = RollParser(syntax, skilled)
    p.parse()

    assert p.using_wp == willpower
    assert p.dice == expected
