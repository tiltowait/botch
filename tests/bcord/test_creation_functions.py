"""Tests for the character wizard initializers."""

from unittest.mock import patch

import pytest

from botchcord.character.creation import wod
from core.characters import Splat
from core.characters.wod import Ghoul, Mortal, Vampire


@pytest.fixture
def mock_wizard_start():
    with patch("botchcord.wizard.Wizard.start") as mock:
        yield mock


@pytest.mark.parametrize(
    "splat,cls",
    [
        (Splat.MORTAL, Mortal),
        (Splat.GHOUL, Ghoul),
        (Splat.VAMPIRE, Vampire),
    ],
)
def test_class_should_fail(splat: Splat, cls):
    assert wod.creation_class(splat) == cls


async def test_create_mortal(mock_wizard_start, ctx):
    await wod.create(
        ctx,
        Splat.MORTAL,
        "Jimmy Maxwell",
        7,
        6,
        "Humanity",
        5,
        "Conscience",
        3,
        "SelfControl",
        2,
        5,
        None,
    )
    mock_wizard_start.assert_called_once_with(ctx.interaction)


async def test_create_ghoul(mock_wizard_start, ctx):
    await wod.create(
        ctx,
        Splat.MORTAL,
        "Jimmy Maxwell",
        7,
        6,
        "Humanity",
        5,
        "Conscience",
        3,
        "SelfControl",
        2,
        5,
        None,
        bond_strength=3,
    )
    mock_wizard_start.assert_called_once_with(ctx.interaction)


@patch("botchcord.wizard.Wizard.start")
async def test_create_vampire(mock_wizard, ctx):
    await wod.create(
        ctx,
        Splat.VAMPIRE,
        "Jimmy Maxwell",
        7,
        6,
        "Humanity",
        5,
        "Conscience",
        3,
        "SelfControl",
        2,
        5,
        None,
        generation=13,
        max_bp=None,
    )
    mock_wizard.assert_called_once_with(ctx.interaction)
