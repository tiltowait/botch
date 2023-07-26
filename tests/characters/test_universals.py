"""Basic character tests."""

import asyncio
from urllib.parse import urlparse

import pydantic
import pytest
import requests

import api
import errors
from characters import Character, Damage, Splat, Trait
from config import FC_BUCKET
from tests.characters import gen_char

# Using function-scoped fixture "character" from conftest


@pytest.fixture
def sample_image() -> str:
    return "https://i.tiltowait.dev/avatar.jpg"


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
    char = gen_char(Splat.VAMPIRE)
    char.add_trait("Brawl", 3)

    with pytest.raises(NotImplementedError):
        char.add_specialties("Brawl", ["Throws"])


def test_trait_not_found_str_value(character: Character):
    try:
        character.remove_trait("Foo")
    except errors.TraitNotFound as err:
        assert str(err) == f"**{character.name}** has no trait named `Foo`."


async def test_single_image_processing(sample_image):
    char = gen_char(Splat.VAMPIRE)
    await char.insert()

    inserted = await char.add_image(sample_image)
    assert urlparse(inserted).netloc == FC_BUCKET, f"{inserted} isn't in dev bucket"
    assert requests.get(inserted).status_code == 200, "Image not found"

    await char.delete_image(inserted)
    assert not char.profile.images

    wait_time = 10
    deleted = False
    for _ in range(wait_time):
        await asyncio.sleep(1)
        if requests.get(inserted).status_code == 404:
            deleted = True
            break
    assert deleted, f"{inserted} was never deleted within {wait_time} seconds"

    await char.delete()


async def test_image_uploading_and_char_deletion(sample_image):
    char = gen_char(Splat.VAMPIRE)
    await char.insert()

    inserted = await char.add_image(sample_image)
    assert urlparse(inserted).netloc == FC_BUCKET, f"{inserted} isn't in dev bucket"
    assert requests.get(inserted).status_code == 200, "Image not found"

    # Try character deletion
    images = [inserted]
    for _ in range(2):
        # Insert more images to make sure they're all deleted
        url = await char.add_image(sample_image)
        images.append(url)

    assert len(char.profile.images) == 3
    await char.delete()

    wait_time = 15
    for _ in range(wait_time):
        await asyncio.sleep(1)
        for url in images:
            if requests.get(url).status_code == 404:
                images.remove(url)
        if not images:
            break
    assert not images, "The images weren't deleted with the character"


async def test_image_deletion_flag(sample_image):
    char = gen_char(Splat.VAMPIRE)
    await char.insert()

    for _ in range(3):
        await char.add_image(sample_image)

    assert len(char.profile.images) == 3
    await char.delete_all_images()
    assert not char.profile.images
    assert not char.is_changed

    await char.delete()


@pytest.mark.parametrize(
    "bad_url", ["https://example.com/test.webp", f"https://{FC_BUCKET}/test.png"]
)
async def test_bad_deletions(bad_url):
    deleted = await api.delete_single_faceclaim(bad_url)
    assert not deleted
