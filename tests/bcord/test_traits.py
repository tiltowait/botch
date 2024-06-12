"""Test the traits display, creation, updating, and deletion interfaces."""

import importlib
from functools import partial
from unittest.mock import ANY, AsyncMock, patch

import discord
import pytest

from botchcord.character.traits.display import (
    add_trait_category,
    add_trait_subcategory,
    build_embed,
    categorize_traits,
    display,
    printout,
)
from botchcord.utils import CEmbed
from botchcord.utils.text import b
from core.characters import Character, GameLine, Splat, Trait
from tests.characters import gen_char

# __init__.py only exposes the assign function, so we have to import
# the module using importlib.
assign = importlib.import_module("botchcord.character.traits.assign")


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
def ctx(bot_mock) -> AsyncMock:
    ctx = AsyncMock()
    ctx.bot = bot_mock
    ctx.respond.return_value = None

    return ctx


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


def test_build_embed(bot_mock, char: Character, mixed_traits: list[Trait]):
    extra = [
        Trait(
            name="Z",
            category=Trait.Category.ABILITY,
            subcategory=Trait.Subcategory.SKILLS,
            rating=1,
        )
    ]
    mixed_traits.append(extra)
    char.traits.append(extra[0])

    embed = build_embed(bot_mock, char)

    assert embed.title == "Character Traits"
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
        ("t1=2", {"t1": 2}),
        (" t1=2", {"t1": 2}),
        ("t1 =2", {"t1": 2}),
        ("t1= 2", {"t1": 2}),
        ("t1=2", {"t1": 2}),
        ("t1 = 2", {"t1": 2}),
        ("t1 =   2 ", {"t1": 2}),
        ("t1=2 t2=3", {"t1": 2, "t2": 3}),
        ("Brawl=4 Academics=3", {"Brawl": 4, "Academics": 3}),
    ],
)
def test_parse_input(text: str, expected: dict[str, int]):
    parsed = assign.parse_input(text)
    assert parsed == expected


@pytest.mark.parametrize("text", ["t", "t=", "t==1", "1=1", "1t=1", "=1", "1=t", "t=t"])
def test_parse_errors(text: str):
    with pytest.raises(SyntaxError):
        _ = assign.parse_input(text)


@pytest.mark.parametrize(
    "assignments,custom",
    [
        ("strength=1 brawl=5", False),
        ("Apples=3 Barp=2", True),
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
    tf = partial(Trait, category=Trait.Category.ATTRIBUTE, subcategory=Trait.Subcategory.PHYSICAL)
    traits = [
        tf(name="Strength", rating=3),
        tf(name="Dexterity", rating=2),
    ]
    desc = assign.describe_assignments(traits)
    assert desc == "Strength: `3`\nDexterity: `2`"


def test_build_assignment_embed(bot_mock, skilled: Character):
    parsed = assign.parse_input("strength=2 brawl=3")
    traits = assign.assign_traits(skilled, parsed)
    embed = assign.build_embed(bot_mock, skilled, traits)

    assert isinstance(embed, CEmbed)
    assert embed.title == "Traits assigned"
    assert embed.description == "Strength: `2`\nBrawl: `3`"
    assert embed.author.name == skilled.name


async def test_assign(ctx, skilled: Character):
    with patch("core.characters.Character.save", return_value=None):
        await assign.assign(ctx, skilled, "brawl=2")

        ctx.respond.assert_called_once_with(embed=ANY, ephemeral=True)
        skilled.save.assert_called_once()
