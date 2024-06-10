"""Specialty test suite."""

import pytest

import errors
from core.characters.base import Character, GameLine, Trait


@pytest.fixture
def subtraits() -> list[str]:
    return ["Kindred", "StreetFighting", "Kine"]


@pytest.fixture
def skill() -> Trait:
    """A basic trait."""
    return Trait(
        name="Brawl",
        rating=4,
        category=Trait.Category.ABILITY,
        subcategory=Trait.Subcategory.PHYSICAL,
    )


@pytest.mark.parametrize(
    "needle,exact,count,name,rating",
    [
        ("b", False, 1, "Brawl", 4),
        ("q", False, 0, None, None),
        ("b", True, 0, None, None),
        ("Brawl", True, 1, "Brawl", 4),
        ("brawl", True, 1, "Brawl", 4),
        ("BRAWL", True, 1, "Brawl", 4),
    ],
)
def test_basic_skill_matching(needle, exact, count, name, rating, skill):
    matches = skill.matching(needle, exact)
    assert len(matches) == count

    if matches:
        assert matches[0].name == name
        assert matches[0].rating == rating


def test_subtrait_addition(skill: Trait):
    assert len(skill.subtraits) == 0

    skill.add_subtraits("Kindred")
    assert len(skill.subtraits) == 1

    skill.add_subtraits("kindred")  # Also tests case-insensitivity
    assert len(skill.subtraits) == 1, "Two 'Kindred' specs were added"

    skill.add_subtraits("StreetFighting")
    assert len(skill.subtraits) == 2, "'StreetFighting' wasn't added"

    skill.add_subtraits(["One", "Two", "Two"])
    assert len(skill.subtraits) == 4, "List wasn't added"


def test_alphabetic_subtraits(skill: Trait):
    skill.add_subtraits(["Kine", "Kindred", "Apples"])
    skill.add_subtraits("Blip")
    assert skill.subtraits == ["Apples", "Blip", "Kindred", "Kine"]


def test_case_insensitive(skill: Trait):
    skill.add_subtraits(["Kine"])
    assert len(skill.subtraits) == 1
    assert skill.subtraits[0] == "Kine"

    skill.add_subtraits(["kine"])
    assert len(skill.subtraits) == 1
    assert skill.subtraits[0] == "Kine"


def test_subtrait_removal(skill: Trait):
    skill.add_subtraits(["One", "Two", "Three", "Four", "Five"])
    assert len(skill.subtraits) == 5

    skill.remove_subtraits(["Four", "Five"])
    assert len(skill.subtraits) == 3

    skill.remove_subtraits("One")
    assert len(skill.subtraits) == 2

    skill.remove_subtraits("One")
    assert len(skill.subtraits) == 2, "Nothing should have been removed"

    skill.remove_subtraits(["Two", "Three"])
    assert len(skill.subtraits) == 0, "Specialties should be gone"


@pytest.mark.parametrize(
    "needle,exact,count,expectations",
    [
        # Inexact
        (".z", False, 0, None),
        (".k.z", False, 0, None),
        ("b.kind", False, 1, [("Brawl (Kindred)", 4, False, "Brawl.Kindred")]),
        (".kind", False, 1, [("Brawl (Kindred)", 4, False, "Brawl.Kindred")]),
        ("brawl.kindred", False, 1, [("Brawl (Kindred)", 4, True, "Brawl.Kindred")]),
        (
            ".k",
            False,
            2,
            [
                ("Brawl (Kindred)", 4, False, "Brawl.Kindred"),
                ("Brawl (Kine)", 4, False, "Brawl.Kine"),
            ],
        ),
        (
            ".kind.s",
            False,
            1,
            [("Brawl (Kindred, StreetFighting)", 4, False, "Brawl.Kindred.StreetFighting")],
        ),
        # Exact
        ("Brawl", True, 1, [("Brawl", 4, True, "Brawl")]),
        ("brawl", True, 1, [("Brawl", 4, True, "Brawl")]),
        ("b", True, 0, None),
        ("brawl.kindred", True, 1, [("Brawl (Kindred)", 4, True, "Brawl.Kindred")]),
        ("brawl.kin", True, 0, None),
        (
            "Brawl.Kindred.StreetFighting",
            True,
            1,
            [("Brawl (Kindred, StreetFighting)", 4, True, "Brawl.Kindred.StreetFighting")],
        ),
        (":kindred", True, 0, None),
    ],
)
def test_subtrait_matching(
    needle: str,
    exact: bool,
    count: int,
    expectations: list[tuple[str, int, bool]],
    skill: Trait,
    subtraits: list[str],
):
    skill.add_subtraits(subtraits)
    assert len(skill.subtraits) == 3

    matches = skill.matching(needle, exact)
    assert len(matches) == count

    if matches:
        for match, expected in zip(matches, expectations):
            name, rating, is_exact, key = expected
            assert match.name == name
            assert match.rating == rating
            assert match.exact == is_exact
            assert match.key == key


@pytest.mark.parametrize(
    "needle,exact,count,expectations",
    [
        # Inexact
        ("z", False, 0, None),
        ("b", False, 1, ["Brawl"]),
        ("b.kind", False, 1, ["Brawl.Kindred"]),
        ("b.k", False, 2, ["Brawl.Kindred", "Brawl.Kine"]),
        ("b.kine.kind", False, 1, ["Brawl.Kindred.Kine"]),
        # Exact
        ("z", True, 0, None),
        ("b", True, 0, None),
        ("Brawl", True, 1, ["Brawl"]),
        ("brawl.kindred", True, 1, ["Brawl.Kindred"]),
    ],
)
def test_expansion(
    needle: str,
    exact: bool,
    count: int,
    expectations: list[str],
    skill: Trait,
    subtraits: list[str],
):
    skill.add_subtraits(subtraits)
    assert len(skill.subtraits) == 3

    expansions = skill.expanding(needle, exact)
    assert len(expansions) == count

    for expansion in expansions:
        assert expansion in expectations


def test_duplicate_matching(skill, subtraits):
    skill.add_subtraits(subtraits)
    match = skill.matching(".k.k", False)
    assert match[0].name == "Brawl (Kindred, Kine)"


def test_incomplete_duplicate_matching(skill, subtraits):
    skill.add_subtraits(subtraits)
    skill.add_subtraits(["Knives", "Suplexing"])
    matches = skill.matching(".s.k", False)
    assert len(matches) == 6


@pytest.mark.parametrize(
    "skill,subtraits,should_raise",
    [
        ("Fighting", ["Throws", "Grappling"], False),
        ("Fighting", ["Throws"], False),
        ("FakeSkill", None, True),
    ],
)
def test_character_add_subtraits(
    skill: str, subtraits: list[str], should_raise: bool, skilled: Character
):
    if should_raise:
        with pytest.raises(errors.TraitNotFound):
            skilled.add_subtraits(skill, subtraits)
    else:
        copied, delta = skilled.add_subtraits(skill, subtraits)
        found = skilled.find_traits(skill)
        trait = found[0]

        assert len(found) == 1
        assert trait.name == skill
        assert trait.subtraits == sorted(subtraits), "Subtraits should be sorted"
        assert copied == trait
        assert delta == sorted(subtraits)


@pytest.mark.parametrize(
    "skill,add,remove,expected,should_raise",
    [
        ("Fighting", ["Throws", "Grappling"], ["Throws", "Grappling"], [], False),
        ("Fighting", ["Throws", "Grappling"], ["Throws"], ["Grappling"], False),
        (
            "Fighting",
            ["Throws", "Grappling", "Kindred"],
            ["Throws"],
            ["Grappling", "Kindred"],
            False,
        ),
        ("FakeSkill", None, None, None, True),
    ],
)
def test_character_remove_subtraits(
    skill: str,
    add: list[str],
    remove: list[str],
    expected: list[str],
    should_raise: bool,
    skilled: Character,
):
    if should_raise:
        with pytest.raises(errors.TraitNotFound):
            skilled.remove_subtraits(skill, add)
    else:
        skilled.add_subtraits(skill, add)
        copied, delta = skilled.remove_subtraits(skill, remove)
        found = skilled.find_traits(skill)
        trait = found[0]

        assert len(found) == 1
        assert copied == trait
        assert delta == sorted(remove)
        assert trait.name == skill
        assert trait.subtraits == expected


def test_wod_vs_cofd_subtraits(skilled: Character, line: GameLine):
    skilled.line = line

    skilled.add_subtraits("Brawl", ["Blocking"])

    if line == GameLine.COFD:
        with pytest.raises(errors.InvalidTrait):
            skilled.add_subtraits("Strength", ["Vicious"])
    else:
        skilled.add_subtraits("Strength", ["Vicious"])
