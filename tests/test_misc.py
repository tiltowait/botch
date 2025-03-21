"""Miscellaneous tests."""

import importlib
import os
from unittest import mock

import mongomock_motor
import pytest

from botch import config, db, utils


# Mock the necessary components
@pytest.mark.asyncio
async def test_db_init():
    with (
        mock.patch.dict(os.environ, {"MONGO_URL": "mock_url", "MONGO_DB": "mock_db"}),
        mock.patch("botch.db.init_beanie") as mock_init_beanie,
    ):
        # Use AsyncMongoMockClient as the mock client
        client = mongomock_motor.AsyncMongoMockClient()
        database = client["mock_db"]

        # Mock the AsyncIOMotorClient to return the AsyncMongoMockClient
        with mock.patch("botch.db.AsyncIOMotorClient", return_value=client):
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


def test_debug_guilds():
    os.environ["DEBUG"] = "1,2,3"
    importlib.reload(config)
    assert config.DEBUG_GUILDS == [1, 2, 3]


def test_command_record():
    ctx = mock.Mock()

    ctx.command.qualified_name = "roll"
    ctx.selected_options = [{"name": "pool", "value": 6}]
    ctx.guild.id = 0
    ctx.user.id = 1
    ctx.interaction.locale = "en-US"
    ctx.command.type = 1

    record = db.CommandRecord.from_context(ctx)

    assert record.command == ctx.command.qualified_name
    assert record.options == ctx.selected_options
    assert record.guild == ctx.guild.id
    assert record.user == ctx.user.id
    assert record.locale == ctx.interaction.locale
    assert record.type == ctx.command.type
