"""Test the traits display, creation, updating, and deletion interfaces."""

import importlib
from functools import partial
from unittest.mock import ANY, AsyncMock, Mock, patch

import discord
import pytest

from botch.botchcord.character.traits.display import (
    add_specialties_field,
    add_trait_category,
    add_trait_subcategory,
    build_embed,
    categorize_traits,
    display,
    format_specialties,
    printout,
)
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import b
from botch.core.characters import Character, GameLine, Splat, Trait
from botch.errors import TraitError, TraitSyntaxError
from tests.characters import gen_char

# __init__.py only exposes the assign function, so we have to import
# the module using importlib.
assign = importlib.import_module("botch.botchcord.character.traits.assign")
remove = importlib.import_module("botch.botchcord.character.traits.remove")


@pytest.fixture
def sample_traits() -> list[Trait]:
    tf = partial(
        Trait,
        category=Trait.Category.ATTRIBUTE,
        subcategory=Trait.Subcategory.PHYSICAL,
    )
    return [
        tf(name="dexterity", rating=2),
        tf(name="strength", rating=4),
        tf(name="stamina", rating=3),
    ]


@pytest.fixture
def mixed_traits() -> list[Trait]:
    """A longer list of traits."""
    tf = partial(Trait, category=Trait.Category.ATTRIBUTE, rating=1)
    physical = [
        tf(name="A", subcategory=Trait.Subcategory.PHYSICAL),
        tf(name="B", subcategory=Trait.Subcategory.PHYSICAL),
        tf(name="C", subcategory=Trait.Subcategory.PHYSICAL),
    ]
    mental = [
        tf(name="D", subcategory=Trait.Subcategory.MENTAL),
        tf(name="E", subcategory=Trait.Subcategory.MENTAL),
        tf(name="F", subcategory=Trait.Subcategory.MENTAL),
    ]
    social = [
        tf(name="G", subcategory=Trait.Subcategory.SOCIAL),
        tf(name="H", subcategory=Trait.Subcategory.SOCIAL),
        tf(name="I", subcategory=Trait.Subcategory.SOCIAL),
    ]
    return physical + mental + social


@pytest.fixture
def specced(sample_traits: list[Trait]) -> list[Trait]:
    sample_traits[0].add_subtraits(["first", "second"])
    sample_traits[2].add_subtraits(["third"])
    return sample_traits


@pytest.fixture
def char(mixed_traits) -> Character:
    char = gen_char(GameLine.WOD, Splat.VAMPIRE, name="Nadea Theron")
    for trait in mixed_traits:
        char.traits.append(trait)  # Direct add instead of using add_trait()
    return char


# TRAITS DISPLAY


def test_printout(sample_traits: list[Trait]):
    pout = printout(sample_traits)
    assert pout == "**dexterity:** 2\n**strength:** 4\n**stamina:** 3"


def test_add_trait_subcategory(sample_traits: list[Trait]):
    embed = discord.Embed()
    add_trait_subcategory(embed, "physical", sample_traits)

    field = embed.fields[0]
    assert field.name == "physical"
    assert field.value == printout(sample_traits)
    assert field.inline is True


def test_categorize_traits(mixed_traits: list[Trait]):
    extra = [
        Trait(
            name="Z",
            category=Trait.Category.ABILITY,
            subcategory=Trait.Subcategory.SKILLS,
            rating=1,
        )
    ]
    mixed_traits += extra
    traits = categorize_traits(Trait.Category.ATTRIBUTE, mixed_traits)

    def f(sub: Trait.Subcategory) -> list[Trait]:
        return [t for t in mixed_traits if t.subcategory == sub]

    assert traits[Trait.Subcategory.PHYSICAL] == f(Trait.Subcategory.PHYSICAL)
    assert traits[Trait.Subcategory.MENTAL] == f(Trait.Subcategory.MENTAL)
    assert traits[Trait.Subcategory.SOCIAL] == f(Trait.Subcategory.SOCIAL)
    assert extra[0] not in traits.values()


def test_add_trait_category(char: Character):
    cat = Trait.Category.ATTRIBUTE
    categorized = categorize_traits(cat, char.traits)

    embed = discord.Embed()
    add_trait_category(embed, char, cat)

    fields = embed.fields
    assert fields[0].name == " "
    assert fields[0].value == b(cat.upper())
    assert fields[0].inline is False

    i = 1
    for k, v in categorized.items():
        field = fields[i]
        assert field.name == k.title()
        assert field.value == printout(v)
        i += 1


async def test_add_custom_category(char: Character):
    char.add_trait("custom", 1)
    embed = discord.Embed()
    add_trait_category(embed, char, Trait.Category.CUSTOM)

    assert embed.fields[0].name == " "


def test_build_embed(bot_mock, char: Character, mixed_traits: list[Trait]):
    extra = [
        Trait(
            name="Z",
            category=Trait.Category.ABILITY,
            subcategory=Trait.Subcategory.SKILLS,
            rating=1,
        )
    ]
    mixed_traits.extend(extra)
    char.traits.append(extra[0])

    embed = build_embed(bot_mock, char)

    assert embed.title == "Character Traits"
    assert embed.author is not None
    assert embed.author.name == char.name
    assert embed.author.icon_url == bot_mock.get_user().guild_avatar
    assert len(embed.fields) == 6, "Empty categories should not be added"

    assert embed.fields[0].name == " "
    assert embed.fields[0].value == b("ATTRIBUTES")
    assert embed.fields[0].inline is False

    categorized = categorize_traits(Trait.Category.ATTRIBUTE, char.traits)
    i = 1
    for c, t in categorized.items():
        field = embed.fields[i]
        assert field.name == c.title()
        assert field.value == printout(t)
        i += 1

    assert embed.fields[i].name == " "
    assert embed.fields[i].value == b("ABILITIES")
    assert embed.fields[i].inline is False

    categorized = categorize_traits(Trait.Category.ABILITY, char.traits)
    i += 1
    for c, t in categorized.items():
        field = embed.fields[i]
        assert field.name == c.title(), c
        assert field.value == printout(t)
        i += 1


async def test_display(bot_mock, char: Character, mixed_traits: list[Trait]):
    ctx = AsyncMock()
    ctx.bot = bot_mock
    ctx.respond.return_value = 3

    for trait in mixed_traits:
        char.traits.append(trait)

    await display(ctx, char)
    ctx.respond.assert_called_once_with(embed=ANY, ephemeral=True)


# TRAITS ADDING


@pytest.mark.parametrize(
    "text,expected",
    [
        ("t=2", {"t": 2}),
        (" t=2", {"t": 2}),
        ("t =2", {"t": 2}),
        ("t= 2", {"t": 2}),
        ("t=2", {"t": 2}),
        ("t = 2", {"t": 2}),
        ("t =   2 ", {"t": 2}),
        ("t=2; u=3", {"t": 2, "u": 3}),
        ("Brawl=4; Academics=3", {"Brawl": 4, "Academics": 3}),
        ("Animal Ken=3; Brawl=2 ", {"Animal Ken": 3, "Brawl": 2}),
    ],
)
def test_parse_input(text: str, expected: dict[str, int]):
    parsed = assign.parse_input(text)
    assert parsed == expected


def test_parse_input_fails_too_long():
    with pytest.raises(TraitError):
        assign.parse_input("This is way too long to ever allow=2")


@pytest.mark.parametrize("text", ["t", "t=", "t==1", "1=1", "1t=1", "=1", "1=t", "t=t", "a=1 b=2"])
def test_parse_errors(text: str):
    with pytest.raises(TraitSyntaxError):
        _ = assign.parse_input(text)


@pytest.mark.parametrize(
    "assignments,custom",
    [
        ("strength=1; brawl=5", False),
        ("Apples=3; Barp=2", True),
        ("Animal Ken=3", True),
    ],
)
def test_assign_traits(assignments: str, custom: bool, skilled: Character):
    parsed = assign.parse_input(assignments)
    assign.assign_traits(skilled, parsed)

    for trait, rating in parsed.items():
        for t in skilled.traits:
            if t.name.casefold() == trait.casefold():
                assert t.rating == rating
                if custom:
                    assert t.category == Trait.Category.CUSTOM
                else:
                    assert t.category != Trait.Category.CUSTOM


def test_describe_assignments():
    tf = partial(
        Trait,
        category=Trait.Category.ATTRIBUTE,
        subcategory=Trait.Subcategory.PHYSICAL,
    )
    traits = [
        tf(name="Strength", rating=3),
        tf(name="Dexterity", rating=2),
    ]
    desc = assign.describe_assignments(traits)
    assert desc == "Strength: `3`\nDexterity: `2`"


def test_build_assignment_embed(bot_mock, skilled: Character):
    parsed = assign.parse_input("strength=2 ; brawl=3")
    traits = assign.assign_traits(skilled, parsed)
    embed = assign.build_embed(bot_mock, skilled, traits)

    assert isinstance(embed, CEmbed)
    assert embed.title == "Traits assigned"
    assert embed.description == "Strength: `2`\nBrawl: `3`"
    assert embed.author is not None
    assert embed.author.name == skilled.name


async def test_assign(ctx, skilled: Character):
    with patch("botch.core.characters.Character.save", return_value=None):
        await assign.assign(ctx, skilled, "brawl=2")

        ctx.respond.assert_called_once_with(embed=ANY, ephemeral=True)
        skilled.save.assert_called_once()  # pyright: ignore


def test_parse_duplicates():
    with pytest.raises(TraitSyntaxError):
        assign.parse_input("strength=3 strength=5")


# TRAIT DELETION


@pytest.mark.parametrize(
    "user_input,expected",
    [
        ("foo", ["foo"]),
        ("  foo   ", ["foo"]),
        ("foo bar", ["foo bar"]),
        ("foo   bar", ["foo bar"]),
        ("foo; bar; baz", ["foo", "bar", "baz"]),
        ("foo bar; baz", ["foo bar", "baz"]),
    ],
)
def test_parse_deletion_input(user_input: str, expected: list[str]):
    parsed = remove.parse_input(user_input)
    assert parsed == expected


@pytest.mark.parametrize("user_input", ["1", "foo.bar", "1foo", "foo 3", ""])
def test_parse_deletion_error(user_input: str):
    with pytest.raises(TraitSyntaxError):
        _ = remove.parse_input(user_input)


@pytest.mark.parametrize(
    "found,not_found",
    [
        (["foo", "bar"], []),
        (["foo", "bar"], ["baz", "zoq"]),
    ],
)
def test_remove_traits(
    found: list[str],
    not_found: list[str],
    character: Character,
):
    for trait in found:
        character.add_trait(trait, 1)
        assert character.has_trait(trait)

    f, m = remove.remove_traits(character, found + not_found)
    assert f == found
    assert m == not_found


def test_remove_core_traits(skilled: Character):
    t = skilled.find_traits("Strength")
    assert t[0].rating != 0

    f, m = remove.remove_traits(skilled, ["Strength"])

    assert f == ["Strength"]
    assert not m

    t = skilled.find_traits("Strength")
    assert t[0].rating == 0


@pytest.mark.parametrize(
    "found,missing",
    [
        (["Strength", "Brawl"], []),
        (["Strength"], ["Foo"]),
        ([], ["Foo", "Bar"]),
    ],
)
def test_build_removal_embed(found: list[str], missing: list[str], bot_mock, skilled: Character):
    embed = remove.build_embed(bot_mock, skilled, found, missing)

    user = bot_mock.get_user()
    assert embed.title == "Traits removed"
    assert embed.author.name == skilled.name
    assert embed.author.icon_url == user.guild_avatar

    if found:
        assert embed.fields[0].name == "Removed"
        assert embed.fields[0].value == "\n".join(found)
        assert embed.fields[0].inline

    if missing:
        # Last field, since there may be none found
        assert embed.fields[-1].name == "Not found!"
        assert embed.fields[-1].value == "\n".join(missing)
        assert embed.fields[-1].inline

    if missing and not found:
        assert embed.color == discord.Color.red()


async def test_remove(ctx, skilled: Character, mock_char_save):
    await remove.remove(ctx, skilled, "foo bar")
    ctx.respond.assert_called_once_with(embed=ANY, ephemeral=True)
    mock_char_save.assert_called_once()


def test_format_specialties(specced: list[Trait]):
    lines = format_specialties(specced)

    assert len(specced) == 3
    assert len(lines) == 2, "format_specialties should have filtered out non-specs"
    assert lines[0] == "**dexterity:** `first`, `second`"
    assert lines[1] == "**stamina:** `third`"


def test_add_specialties_field(specced: list[Trait]):
    embed = discord.Embed()
    # add_specialties_field checks the field two before it, so we need to add
    # some blank fields to get it to behave
    embed.add_field(name=" ", value="** **")
    embed.add_field(name=" ", value="** **")
    char = Mock()
    char.traits = specced
    add_specialties_field(embed, char)

    assert len(embed.fields) == 3
    assert embed.fields[-1].name == "Specialties"
    assert embed.fields[-1].value == "\n".join(format_specialties(specced))


def test_specialties_field_not_added(sample_traits):
    embed = discord.Embed()
    char = Mock()
    char.traits = sample_traits
    add_specialties_field(embed, char)

    assert not embed.fields


def test_build_embed_has_specs(bot_mock, char: Character, specced: list[Trait]):
    char.traits = specced
    embed = build_embed(bot_mock, char)

    assert embed.fields[-1].name == "Specialties"
    assert embed.fields[-1].value == "\n".join(format_specialties(specced))
    assert embed.fields[-1].inline
