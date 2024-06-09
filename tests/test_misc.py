"""Miscellaneous tests."""

import os
from unittest import mock

import mongomock_motor
import pytest

import db
import utils


# Mock the necessary components
@pytest.mark.asyncio
async def test_db_init():
    with mock.patch.dict(os.environ, {"MONGO_URL": "mock_url", "MONGO_DB": "mock_db"}), mock.patch(
        "db.init_beanie"
    ) as mock_init_beanie:

        # Use AsyncMongoMockClient as the mock client
        client = mongomock_motor.AsyncMongoMockClient()
        database = client["mock_db"]

        # Mock the AsyncIOMotorClient to return the AsyncMongoMockClient
        with mock.patch("db.AsyncIOMotorClient", return_value=client):
            await db.init()

            # Ensure the mocks were called as expected
            mock_init_beanie.assert_called_once_with(
                database=database,
                document_models=db.DOCUMENT_MODELS,
            )


@pytest.mark.parametrize(
    "sample,expected",
    [
        ("one two", "one two"),
        ("one", "one"),
        ("one  two", "one two"),
        (" one two  three ", "one two three"),
    ],
)
def test_normalize_text(sample: str, expected: str):
    assert expected == utils.normalize_text(sample)


@pytest.mark.parametrize(
    "generation,bp",
    [
        (3, 60),
        (4, 50),
        (5, 40),
        (6, 30),
        (7, 20),
        (8, 15),
        (9, 14),
        (10, 13),
        (11, 12),
        (12, 11),
        (13, 10),
        (14, 10),
        (15, 10),
    ],
)
def test_max_vtm_bp(generation: int, bp: int):
    assert utils.max_vtm_bp(generation) == bp


@pytest.mark.parametrize(
    "generation,max_trait",
    [
        (3, 10),
        (4, 9),
        (5, 8),
        (6, 7),
        (7, 6),
        (8, 5),
        (9, 5),
        (10, 5),
        (11, 5),
        (12, 5),
        (13, 5),
        (14, 5),
        (15, 5),
    ],
)
def test_max_vtm_trait(generation: int, max_trait: int):
    assert utils.max_vtm_trait(generation) == max_trait
