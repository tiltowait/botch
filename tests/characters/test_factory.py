"""Tests of the character creation factory."""

import random
from collections import OrderedDict

import pytest

import errors
from characters import Damage, GameLine, Grounding, Splat, Trait
from characters.factory import Factory
from characters.wod import Vampire, gen_virtues


@pytest.fixture
def factory():
    args = {
        "name": "Test",
        "guild": 0,
        "user": 0,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * 6,
        "grounding": Grounding(path="Humanity", rating=7),
        "virtues": gen_virtues(
            {
                "Conscience": 3,
                "SelfControl": 2,
                "Courage": 4,
            }
        ),
    }
    return Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, args)


def test_invalid_schema():
    with pytest.raises(errors.MissingSchema):
        f = Factory("fake", "fake", None, None)


def test_valid_schema():
    f = Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, {"name": "Billy"})
    assert isinstance(f.schema, dict)


def test_get_traits(factory: Factory):
    for trait_category in factory.categories.values():
        assert trait_category in list(Trait.Category)


def test_assignment(factory: Factory):
    assigned = OrderedDict()

    while trait := factory.next_trait():
        rating = random.randint(0, 5)
        assigned[trait] = rating
        factory.assign_next(rating)

    assert assigned == factory.assignments


def test_premature_create(factory):
    with pytest.raises(errors.Unfinished):
        factory.create()


async def test_create(factory):
    assigned = OrderedDict()

    while trait := factory.next_trait():
        rating = random.randint(0, 5)
        assigned[trait] = rating
        factory.assign_next(rating)

    character = factory.create()
    assert isinstance(character, Vampire)

    for trait, rating in assigned.items():
        found = character.find_traits(trait)
        assert len(found) == 1
        assert found[0].name == trait
        assert found[0].rating == rating
