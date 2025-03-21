"""Various roll-parsing tests."""

import pytest

from botch import errors
from botch.core.characters import Character, GameLine, Splat
from botch.core.rolls.parse import RollParser
from tests.characters import gen_char


@pytest.mark.parametrize(
    "syntax,expected",
    [
        ("3", [3]),
        ("foo", ["foo"]),
        ("3 + foo", [3, "+", "foo"]),
        ("foo + 3", ["foo", "+", 3]),
        ("foo.bar", ["foo.bar"]),
        (". - ..", [".", "-", ".."]),
        ("foo + .bar - 2", ["foo", "+", ".bar", "-", 2]),
        ("foo3", None),
        ("3foo", None),
        ("foo.3", None),
        ("3.bar", None),
        ("3 / 2", None),
        ("3 3", None),
        ("foo bar", ["foo bar"]),
        ("foo  bar", ["foo bar"]),
        ("foo bar + baz", ["foo bar", "+", "baz"]),
        ("foo 3", None),
        ("3 foo", None),
        ("animal_ken + 3", ["animal_ken", "+", 3]),
        ("animal_ken.scrubbing", ["animal_ken.scrubbing"]),
        ("skill.underscore_spec", ["skill.underscore_spec"]),
        (
            "un_skill.un_spec + 3 - skill_un + .un_spec + skill",
            ["un_skill.un_spec", "+", 3, "-", "skill_un", "+", ".un_spec", "+", "skill"],
        ),
    ],
)
def test_roll_prep(syntax: str, expected: list[str | int]):
    p = RollParser(syntax, None)

    if not expected:
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
    assert p.num_dice == expected


def test_can_parse():
    a = gen_char(GameLine.WOD, Splat.VAMPIRE)
    a.add_trait("Strength", 2)
    a.add_trait("Brawl", 5)
    a.add_trait("aaa", 1)
    a.add_trait("aaaa", 1)

    assert RollParser.can_roll(a, "stren+br")
    assert RollParser.can_roll(a, "a")  # ambiguous traits are allowed
    assert not RollParser.can_roll(a, "stren+fake")
