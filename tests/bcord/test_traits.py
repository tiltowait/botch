"""Test the traits display, creation, updating, and deletion interfaces."""

from functools import partial
from unittest.mock import Mock

import discord
import pytest

from botchcord.character.traits import display
from core.characters import Character, GameLine, Splat, Trait
from tests.characters import gen_char


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
def bot_mock() -> Mock:
    user = Mock()
    user.display_name = "tiltowait"
    user.guild_avatar = "https://example.com/img.png"

    bot = Mock()
    bot.get_user.return_value = user

    return bot


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


def test_printout(sample_traits: list[Trait]):
    printout = display.printout(sample_traits)
    assert printout == "**dexterity:** 2\n**strength:** 4\n**stamina:** 3"


def test_add_trait_subcategory(sample_traits: list[Trait]):
    embed = discord.Embed()
    display.add_trait_subcategory(embed, "physical", sample_traits)

    field = embed.fields[0]
    assert field.name == "physical"
    assert field.value == display.printout(sample_traits)
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
    traits = display.categorize_traits(Trait.Category.ATTRIBUTE, mixed_traits)

    def f(sub: Trait.Subcategory) -> list[Trait]:
        return [t for t in mixed_traits if t.subcategory == sub]

    assert traits[Trait.Subcategory.PHYSICAL] == f(Trait.Subcategory.PHYSICAL)
    assert traits[Trait.Subcategory.MENTAL] == f(Trait.Subcategory.MENTAL)
    assert traits[Trait.Subcategory.SOCIAL] == f(Trait.Subcategory.SOCIAL)
    assert extra[0] not in traits.values()


def test_add_trait_category(char: Character):
    cat = Trait.Category.ATTRIBUTE
    categorized = display.categorize_traits(cat, char.traits)

    embed = discord.Embed()
    display.add_trait_category(embed, char, cat)

    fields = embed.fields
    assert fields[0].name == cat.upper()
    assert fields[0].inline is False

    i = 1
    for k, v in categorized.items():
        field = fields[i]
        assert field.name == k.title()
        assert field.value == display.printout(v)
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

    embed = display.build_embed(bot_mock, char)

    assert embed.title == "Character Traits"
    assert embed.author.name == char.name
    assert embed.author.icon_url == bot_mock.get_user().guild_avatar
    assert len(embed.fields) == 6, "Empty categories should not be added"

    assert embed.fields[0].name == "ATTRIBUTES"
    assert embed.fields[0].value == " "
    assert embed.fields[0].inline is False

    categorized = display.categorize_traits(Trait.Category.ATTRIBUTE, char.traits)
    i = 1
    for c, t in categorized.items():
        field = embed.fields[i]
        assert field.name == c.title()
        assert field.value == display.printout(t)
        i += 1

    assert embed.fields[i].name == "ABILITIES"
    assert embed.fields[i].value == " "
    assert embed.fields[i].inline is False

    categorized = display.categorize_traits(Trait.Category.ABILITY, char.traits)
    i += 1
    for c, t in categorized.items():
        field = embed.fields[i]
        assert field.name == c.title(), c
        assert field.value == display.printout(t)
        i += 1
