"""Test the FastAPI app."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import core
from botchcord.character.web import get_schema_file
from core.characters import GameLine, Trait
from core.characters.wod import Ghoul, Mortal, Vampire
from web.app import app, cache
from web.models import CharacterData, Grounding, Virtue, WizardSchema


@pytest.fixture
def token() -> str:
    return "token"


@pytest.fixture
def wizard_schema():
    mock = Mock()
    mock.guild_id = 0
    mock.user_id = 1
    mock.traits.line = GameLine.WOD
    mock.guild_name = "The Fake Guild"
    mock.traits.category.return_value = Trait.Category.ATTRIBUTE
    mock.traits.subcategory.return_value = Trait.Subcategory.PHYSICAL

    return mock


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def character_data(wizard_schema):
    return {
        "token": cache.register(wizard_schema),
        "splat": "Mortal",
        "name": "Nadea Theron",
        "grounding": Grounding(path="Humanity", rating=7),
        "generation": None,
        "health": 6,
        "willpower": 7,
        "traits": {"Strength": 4, "Brawl": 3},
        "virtues": [
            Virtue(name="Conscience", rating=3),
            Virtue(name="Self-Control", rating=2),
            Virtue(name="Courage", rating=4),
        ],
    }


@pytest.fixture
def expected_message(character_data, wizard_schema):
    return {
        "message": f"Successfully created {character_data['name']} on {wizard_schema.guild_name}!"
    }


def test_get_wizard_schema_valid_token(client):
    ws = WizardSchema.create("Guildy", 0, 0, get_schema_file("vtm"))
    token = cache.register(ws)

    response = client.get(f"/character/create/{token}")
    assert response.status_code == 200
    assert response.json() == ws.model_dump(by_alias=True)


def test_get_wizard_schema_invalid_token(client):
    response = client.get("/character/create/invalid-token")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Invalid token. Either it expired, was already used, or never existed."
    }


@pytest.mark.parametrize(
    "splat,character_class",
    [
        ("Mortal", Mortal),
        ("Vampire", Vampire),
        ("Ghoul", Ghoul),
    ],
)
async def test_create_character(
    client,
    character_data,
    expected_message,
    wizard_schema,
    splat,
    character_class,
):
    character_data["splat"] = splat
    if splat == "Vampire":
        character_data["generation"] = 13

    response = client.post("/character/create", json=CharacterData(**character_data).model_dump())
    assert response.status_code == 200
    assert response.json() == expected_message

    char = await core.cache.fetchone(
        wizard_schema.guild_id, wizard_schema.user_id, character_data["name"]
    )
    assert isinstance(char, character_class)
    await core.cache.remove(char)
    assert wizard_schema.token not in cache
