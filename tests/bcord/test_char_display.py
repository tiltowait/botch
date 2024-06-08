"""Character display tests."""

import pytest

import errors
from core.characters import Experience, GameLine, Splat
from core.characters.wod import Vampire
from botchcord.character.display import (
    DisplayField,
    build_embed,
    get_default_fields,
    get_field_name,
    get_field_value,
    get_track_string,
)
from tests.characters import gen_char


@pytest.fixture
def wod_vamp():
    return gen_char(
        GameLine.WOD,
        Splat.VAMPIRE,
        cls=Vampire,
        experience=Experience(unspent=10, lifetime=20),
        generation=13,
        max_bp=10,
        blood_pool=9,
        virtues=[],
    )


def test_default_fields(character):
    print(character.line, character.splat)
    fields = get_default_fields(character)
    assert isinstance(fields, tuple)

    character.line = "fake"
    with pytest.raises(errors.CharacterTemplateNotFound):
        _ = get_default_fields(character)

    character.line = GameLine.WOD
    character.splat = "fake"
    with pytest.raises(errors.CharacterTemplateNotFound):
        _ = get_default_fields(character)


@pytest.mark.parametrize(
    "track,expected",
    [
        (".....", "5 Unhurt"),
        ("...//", "2 Bashing\n3 Unhurt"),
        ("..X//", "1 Lethal\n2 Bashing\n2 Unhurt"),
        (".*X//", "1 Aggravated\n1 Lethal\n2 Bashing\n1 Unhurt"),
    ],
)
def test_track_string(track: str, expected: str):
    assert expected == get_track_string(track)


@pytest.mark.parametrize(
    "field,expected",
    [
        (DisplayField.NAME, None),
        (DisplayField.HEALTH, None),
        (DisplayField.WILLPOWER, None),
        (DisplayField.GROUNDING, "Humanity"),
        (DisplayField.GENERATION, None),
        (DisplayField.BLOOD_POOL, None),
        (DisplayField.EXPERIENCE, "Experience (Unspent / Lifetime)"),
    ],
)
def test_get_field_name(field: DisplayField, expected: str | None, wod_vamp):
    expected = expected or field.value
    assert get_field_name(wod_vamp, field) == expected


@pytest.mark.parametrize(
    "field,expected",
    [
        (DisplayField.NAME, "Test"),
        (DisplayField.HEALTH, "7 Unhurt"),
        (DisplayField.WILLPOWER, "6 Unhurt"),
        (DisplayField.GROUNDING, "7"),
        (DisplayField.GENERATION, "13"),
        (DisplayField.BLOOD_POOL, "```9 / 10```"),
        (DisplayField.EXPERIENCE, "```10 / 20```"),
    ],
)
def test_get_field_value(field: DisplayField, expected: str | None, wod_vamp):
    expected = expected or field.value
    assert get_field_value(wod_vamp, field, False) == expected


def test_build_emoji(wod_vamp):
    embed = build_embed(wod_vamp, False, author_tag="Jimmy Maxwell")

    assert embed.title == wod_vamp.name
    assert embed.author.name == "Jimmy Maxwell"

    for i, field in enumerate(get_default_fields(wod_vamp)):
        expected_name = get_field_name(wod_vamp, field)
        expected_value = get_field_value(wod_vamp, field, False)

        assert embed.fields[i].name == expected_name
        assert embed.fields[i].value == expected_value