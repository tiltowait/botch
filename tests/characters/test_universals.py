"""Basic character tests."""

import pydantic
import pytest

import errors
from characters import Character, Damage, Splat, Trait
from tests.characters import gen_char

# Using function-scoped fixture "character" from conftest


@pytest.mark.parametrize("splat", list(Splat) + ["invalid"])
async def test_splat_constraints(splat: str):
    if splat not in list(Splat):
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            gen_char(splat)
    else:
        gen_char(splat)


async def test_char_saving(character):
    char = await character.insert()
    found = await Character.find_one(Character.id == char.id)

    assert found == char


async def test_state_management(character):
    await character.insert()
    character.name = "New name"
    assert character.is_changed
    assert character.get_changes() == {"name": "New name"}

    await character.save_changes()

    assert not character.is_changed
    await character.save_changes()
    assert character.get_changes() == {}


@pytest.mark.parametrize("tracker", ["health", "willpower"])
def test_set_damage(tracker, character: Character):
    assert set(getattr(character, tracker)) == set(Damage.NONE), "Should start with no damage"
    track_len = len(getattr(character, tracker))

    dmgs = [
        (0, 0, 3),
        (0, 1, 3),
        (2, 1, 3),
        (2, 1, 0),
    ]
    for bashing, lethal, agg in dmgs:
        none = track_len - (bashing + lethal + agg)

        character.set_damage(tracker, Damage.AGGRAVATED, agg)
        character.set_damage(tracker, Damage.LETHAL, lethal)
        track = character.set_damage(tracker, Damage.BASHING, bashing)

        assert (
            track
            == Damage.NONE * none
            + Damage.BASHING * bashing
            + Damage.LETHAL * lethal
            + Damage.AGGRAVATED * agg
        )


async def test_trait_basics(character: Character):
    await character.insert()
    strength = character.add_trait("Strength", 3, Trait.Category.ATTRIBUTE)
    with pytest.raises(errors.TraitAlreadyExists):
        character.add_trait("Strength", 3, Trait.Category.ATTRIBUTE)

    stamina = character.add_trait("Stamina", 2, Trait.Category.ATTRIBUTE)

    found = character.find_traits("st")
    assert len(found) == 2
    assert found[0] == stamina
    assert found[1] == strength

    assert character.has_trait("strength")
    assert not character.has_trait("st")

    assert character.find_traits("str") == [strength]
    assert character.is_changed


def test_update_trait(skilled: Character):
    updated = skilled.update_trait("Brawl", 5)
    assert updated.name == "Brawl"
    assert updated.rating == 5

    found = skilled.find_traits("brawl")
    assert updated == found[0]

    with pytest.raises(errors.TraitNotFound):
        skilled.update_trait("Fake", 2)


def test_remove_trait(skilled: Character):
    assert skilled.has_trait("Brawl")
    removed = skilled.remove_trait("brawl")

    assert removed == "Brawl"
    assert not skilled.has_trait("Brawl")

    with pytest.raises(errors.TraitNotFound):
        skilled.remove_trait("Fake")


def test_add_specialties_not_implemented():
    char = gen_char(Splat.VTM)
    char.add_trait("Brawl", 3)

    with pytest.raises(NotImplementedError):
        char.add_specialties("Brawl", ["Throws"])


def test_trait_not_found_str_value(character: Character):
    try:
        character.remove_trait("Foo")
    except errors.TraitNotFound as err:
        assert str(err) == f"**{character.name}** has no trait named `Foo`."
