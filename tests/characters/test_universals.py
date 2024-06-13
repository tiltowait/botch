"""Basic character tests."""

import random
from unittest.mock import patch

import pydantic
import pytest

import api
import errors
from config import FC_BUCKET
from core.characters import Character, Damage, GameLine, Splat, Trait
from tests.characters import gen_char

# Using function-scoped fixture "character" from conftest


@pytest.fixture
def sample_image() -> str:
    return "https://i.tiltowait.dev/avatar.jpg"


@pytest.mark.parametrize("splat", list(Splat) + ["invalid"])
async def test_splat_constraints(splat: str):
    if splat not in list(Splat):
        with pytest.raises(pydantic.ValidationError):
            gen_char(GameLine.WOD, splat)
    else:
        gen_char(GameLine.WOD, splat)


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


def test_remove_trait(character: Character):
    trait = "Foo"
    character.add_trait("Foo", 1)
    assert character.has_trait(trait)
    assert character.has_trait(trait.lower())
    removed = character.remove_trait(trait.lower())

    assert removed == trait
    assert not character.has_trait(trait)

    with pytest.raises(errors.TraitNotFound):
        character.remove_trait("Fake")


def test_remove_core_trait(skilled: Character):
    b = "Brawl"
    t = skilled.find_traits("Brawl")
    assert t
    assert t[0].name == b
    assert t[0].rating != 0

    skilled.remove_trait(b)
    t = skilled.find_traits(b)
    assert t, "Core trait should not have been removed!"
    assert t[0].name == b
    assert t[0].rating == 0


def test_add_specialties_not_implemented():
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    char.add_trait("Brawl", 3)

    with pytest.raises(NotImplementedError):
        char.add_specialties("Brawl", ["Throws"])


def test_trait_not_found_str_value(character: Character):
    try:
        character.remove_trait("Foo")
    except errors.TraitNotFound as err:
        assert str(err) == f"**{character.name}** has no trait named `Foo`."


async def test_single_image_processing(sample_image):
    """Test the image processing logic but not the API itself."""
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    await char.insert()

    with patch(
        "core.characters.base.api.upload_faceclaim",
        return_value=f"https://{FC_BUCKET}/123a/456b.webp",
    ) as mock_add:
        inserted = await char.add_image(sample_image)

        mock_add.assert_called_once_with(char, sample_image)
        assert len(char.profile.images) == 1
        assert inserted in map(str, char.profile.images)  # Images are type Url

    with patch(
        "core.characters.base.api.delete_single_faceclaim",
        return_value=True,
    ) as mock_delete:
        await char.delete_image(inserted)

        mock_delete.assert_called_once_with(inserted)
        assert not char.profile.images

    await char.delete()


async def test_multiple_image_deletion(sample_image):
    char = gen_char(GameLine.WOD, Splat.VAMPIRE)
    await char.insert()

    def randurl(*args, **kwargs):
        return f"https://{FC_BUCKET}/{random.randint(1, 1000)}/{random.randint(1, 1000)}.webp"

    with patch("core.characters.base.api.upload_faceclaim", side_effect=randurl) as mock_add:
        # Insert some images
        urls = []
        for _ in range(3):
            url = await char.add_image(sample_image)
            urls.append(url)

        mock_add.assert_called_with(char, sample_image)
        assert mock_add.call_count == len(urls)
        assert len(set(urls)) == len(urls)
        assert [str(i) for i in char.profile.images] == urls, "The image URLs don't match"

    with patch("core.characters.base.api.delete_character_faceclaims") as mock_delete:
        # Make sure delete_all_images() clears profile.images
        await char.delete_all_images()
        assert not char.is_changed
        assert not char.profile.images, "The image URLs were not removed from the character!"

        await char.delete()

        mock_delete.assert_called_with(char)
        assert mock_delete.call_count == 2


@pytest.mark.parametrize(
    "bad_url", ["https://example.com/test.webp", f"https://{FC_BUCKET}/test.png"]
)
async def test_bad_deletions(bad_url):
    deleted = await api.delete_single_faceclaim(bad_url)
    assert not deleted
