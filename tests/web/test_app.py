"""Test the FastAPI app."""

import pytest
from fastapi.testclient import TestClient

from botchcord.character.web import get_schema_file
from web.app import app, cache
from web.models import WizardSchema


@pytest.fixture
def client():
    return TestClient(app)


def test_get_wizard_schema_valid_token(client):
    ws = WizardSchema.create("Guildy", 0, get_schema_file("vtm"))
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
