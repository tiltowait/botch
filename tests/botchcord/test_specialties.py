"""Specialties UI test. (Everything but Discord stuff."""

from contextlib import nullcontext as does_not_raise
from unittest.mock import ANY, AsyncMock

import pytest

from botch import errors
from botch.bot import AppCtx
from botch.botchcord.character.specialties.adjust import (
    _make_embed,
    add_specialties,
    remove_specialties,
    validate_tokens,
)
from botch.botchcord.character.specialties.adjust import assign as assign_cmd
from botch.botchcord.character.specialties.adjust import remove as remove_cmd
from botch.botchcord.character.specialties.tokenize import tokenize
from botch.botchcord.utils.text import b
from botch.core.characters import Character, GameLine, Splat
from tests.characters import gen_char


@pytest.fixture
def character() -> Character:
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    for trait, rating in dict(Brawl=1, Craft=2, Oblivion=3).items():
        char.add_trait(trait, rating)
    return char


@pytest.fixture
def specced(character: Character) -> Character:
    character.add_subtraits("Brawl", ["Kindred", "Kine"])
    character.add_subtraits("Craft", ["Knives"])
    return character


def test_specialties_fails_too_long(specced: Character):
    with pytest.raises(errors.TraitError):
        specced.add_subtraits("Brawl", "This thing is way too long to ever be allowed")


@pytest.mark.parametrize(
    "syntax,_expected",
    [
        ("brawl=kindred", [("brawl", ["kindred"])]),
        ("brawl=kindred,kine", [("brawl", ["kindred", "kine"])]),
        (
            "brawl=kindred ; occult=bahari",
            [("brawl", ["kindred"]), ("occult", ["bahari"])],
        ),
        (
            "brawl=kindred,kine; occult=bahari",
            [("brawl", ["kindred", "kine"]), ("occult", ["bahari"])],
        ),
        ("brawl = kindred,", [("brawl", ["kindred"])]),
        ("brawl = kindred, kine", [("brawl", ["kindred", "kine"])]),
        ("animal_ken=squirrels", [("animal_ken", ["squirrels"])]),
        (
            "animal ken=badgers; subterfuge=impeccable lies,glib;",
            [("animal ken", ["badgers"]), ("subterfuge", ["impeccable lies", "glib"])],
        ),
    ],
)
def test_valid_syntax(syntax: str, _expected: list[tuple[str, list[str]]]):
    tokens = tokenize(syntax)
    assert len(tokens) == len(_expected)

    for received, expected in zip(tokens, _expected):
        r_trait, r_specs = received
        e_trait, e_specs = expected

        assert r_trait == e_trait
        assert r_specs == e_specs


@pytest.mark.parametrize(
    "syntax",
    [
        "b",  # No specialty given
        "9",  # Invalid character
        "brawl=kindred=kine,test",  # Multi equals
        "brawl=kindred, kine=test",
    ],
)
def test_invalid_syntax(syntax: str):
    with pytest.raises(errors.InvalidSyntax):
        _ = tokenize(syntax)


@pytest.mark.parametrize(
    "syntax,expected",
    [
        ("brawl=Kindred", [("Brawl", ["Kindred"], ["Kindred"])]),
        ("brawl=Kindred,Kine", [("Brawl", ["Kindred", "Kine"], ["Kindred", "Kine"])]),
        (
            "brawl=Kindred ;craft=Knives",
            [("Brawl", ["Kindred"], ["Kindred"]), ("Craft", ["Knives"], ["Knives"])],
        ),
    ],
)
def test_add_specialties(syntax: str, expected: list, character: Character):
    traits = add_specialties(character, syntax)
    assert len(traits) == len(expected)

    for trait, expected in zip(traits, expected):
        trait, delta = trait
        e_trait, e_specs, e_delta = expected
        assert trait.name == e_trait
        assert trait.subtraits == e_specs
        assert delta == e_delta


@pytest.mark.parametrize(
    "syntax,expected",
    [
        ("brawl=Kindred,Kine", ["Kine"]),
        ("brawl=Kindred,Werewolves,Kine", ["Kine", "Werewolves"]),
    ],
)
def test_add_specialties_intersection(syntax: str, expected: list[str], character: Character):
    """Ensure that the delta filters out duplicates."""
    character.add_subtraits("Brawl", "Kindred")

    _, delta = add_specialties(character, syntax)[0]
    assert delta == expected


@pytest.mark.parametrize(
    "syntax",
    [
        "Performance=Piano",  # Only invalid
        "Brawl=Kindred; Performance=Piano",  # One valid, one invalid
    ],
)
def test_fail_add_specialties(syntax: str, character: Character):
    with pytest.raises(errors.TraitError):
        _ = add_specialties(character, syntax)


@pytest.mark.parametrize(
    "syntax,expected",
    [
        ("Brawl=Kindred", [("Brawl", ["Kine"], ["Kindred"])]),
        ("Brawl=Kindred,Kine", [("Brawl", [], ["Kindred", "Kine"])]),
        (
            "Brawl=Kindred; Craft=Knives",
            [("Brawl", ["Kine"], ["Kindred"]), ("Craft", [], ["Knives"])],
        ),
    ],
)
def test_remove_specialties(syntax: str, expected: list, specced: Character):
    traits = remove_specialties(specced, syntax)
    assert len(traits) == len(expected)

    for trait, expected in zip(traits, expected):
        trait, delta = trait
        e_trait, e_specs, e_delta = expected

        assert trait.name == e_trait
        assert trait.subtraits == e_specs
        assert delta == e_delta


@pytest.mark.parametrize(
    "exception,skill,specs",
    [
        (does_not_raise(), "Brawl", ["Kindred"]),
        (does_not_raise(), "Brawl", ["Kindred", "Kine"]),
        (pytest.raises(errors.TraitError), "Brawl", ["Brawl"]),
        (pytest.raises(errors.TraitError), "Brawl", ["Kindred", "Brawl"]),
        (pytest.raises(errors.TraitError), "NotASkill", ["ShouldFail"]),
        (
            pytest.raises(errors.TraitError),
            "BRAWL",
            ["brawl"],
        ),  # Test case-insensitivity
    ],
)
def test_validate_tokens(exception, skill: str, specs: list[str], character: Character):
    with exception:
        validate_tokens(character, [(skill, specs)])


@pytest.mark.parametrize(
    "assignments,fails",
    [
        ("brawl=Grappling,Biting; craft=Sailboats", False),
        ("b", True),
    ],
)
async def test_assign_cmd(
    mock_respond: AsyncMock,
    mock_char_save: AsyncMock,
    ctx: AppCtx,
    character: Character,
    assignments: str,
    fails: bool,
):
    if fails:
        with pytest.raises(errors.InvalidSyntax):
            await assign_cmd(ctx, character, assignments)
    else:
        await assign_cmd(ctx, character, assignments)
        mock_respond.assert_called_once_with(embed=ANY, ephemeral=True)
        mock_char_save.assert_awaited_once()


@pytest.mark.parametrize(
    "assignments,fails",
    [
        ("brawl=Grappling,Biting; craft=Sailboats", False),
        ("b", True),
    ],
)
async def test_remove_cmd(
    mock_respond: AsyncMock,
    mock_char_save: AsyncMock,
    ctx: AppCtx,
    character: Character,
    assignments: str,
    fails: bool,
):
    if fails:
        with pytest.raises(errors.InvalidSyntax):
            await remove_cmd(ctx, character, assignments)
    else:
        await remove_cmd(ctx, character, assignments)
        mock_respond.assert_called_once_with(embed=ANY, ephemeral=True)
        mock_char_save.assert_awaited_once()


def test_validate_tokens_multi_missing(character: Character):
    tokens = [("First", ["Spec"]), ("Second", ["Spec"])]
    with pytest.raises(errors.TraitError) as exc_info:
        validate_tokens(character, tokens)

    assert (
        str(exc_info.value)
        == f"{b(character.name)} doesn't have the following traits: `First`, `Second`."
    )


def test_adding_subtraits_to_subtraited(ctx: AppCtx, specced: Character):
    specced.traits[1].add_subtraits(["Painting"])
    additions = [[specced.traits[1], ["Painting"]]]
    embed = _make_embed(ctx, specced, additions, "Specialties added")

    assert embed.description is not None
    assert "***All:*** *Knives*, *Painting*" in embed.description, "Should show all specs"
