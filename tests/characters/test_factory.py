"""Tests of the character creation factory."""

import json
import random
from collections import OrderedDict

import pytest

import errors
from core.characters import Damage, GameLine, Grounding, Splat, Trait
from core.characters.factory import Factory, Schema
from core.characters.wod import Vampire, gen_virtues


@pytest.fixture
def factory() -> Factory:
    args = {
        "name": "Test",
        "guild": 0,
        "user": 0,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * 6,
        "grounding": Grounding(path="Humanity", rating=7),
        "generation": 8,
        "max_bp": 15,
        "blood_pool": 15,
        "virtues": gen_virtues(
            {
                "Conscience": 3,
                "SelfControl": 2,
                "Courage": 4,
            }
        ),
    }
    return Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, args)


def test_load_schema():
    loc = "core/characters/schemas/wod/vtm.json"
    schema = Schema.load(loc)
    assert isinstance(schema, Schema)


def test_invalid_schema():
    with pytest.raises(errors.MissingSchema):
        _ = Factory("fake", "fake", None, None)  # type: ignore


def test_valid_schema():
    f = Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, {"name": "Billy"})
    assert isinstance(f.schema, Schema)


def test_wod_trait_categories_and_subcategories(factory: Factory):
    with open("./core/characters/schemas/wod/vtm.json") as f:
        data = json.load(f)

    sections = ["inherent", "learned"]
    for section in sections:
        cat = data[section]
        cat_name = cat["category"]
        assert cat_name in list(Trait.Category), "Unrecognized category"

        # Check each subcategory and make sure Schema reports them correctly
        for sub in cat["subcategories"]:
            sub_name = sub["name"]
            assert sub_name in list(Trait.Subcategory)

            for trait in sub["traits"]:
                assert factory.schema.category(trait) == cat_name
                assert factory.schema.subcategory(trait) == sub_name

    # We've automated the check, but let's do some manual ones just for peace
    # of mind.
    schema = factory.schema
    assert schema.category("Brawl") == Trait.Category.ABILITY
    assert schema.subcategory("Brawl") == Trait.Subcategory.TALENTS
    assert schema.subcategory("Academics") == Trait.Subcategory.KNOWLEDGES

    with pytest.raises(ValueError):
        schema.category("fake")

    with pytest.raises(ValueError):
        schema.subcategory("fake")


def test_assignment(factory: Factory):
    assigned = OrderedDict()

    assert factory.remaining > 0
    while trait := factory.next_trait():
        rating = random.randint(0, 5)
        assigned[trait] = rating
        factory.assign_next(rating)

    assert assigned == factory.assignments
    assert factory.remaining == 0


def test_premature_create(factory):
    with pytest.raises(errors.Unfinished):
        factory.create()


def test_peek_last(factory: Factory):
    assert factory.peek_last() is None

    trait = factory.next_trait()
    factory.assign_next(3)
    assert factory.peek_last() == (trait, 3)

    trait2 = factory.next_trait()
    factory.assign_next(4)
    assert factory.peek_last() == (trait2, 4)


def test_create(factory):
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
