"""Tests for the character wizard initializers."""

from unittest.mock import patch

import pytest

from botchcord.character.creation import wod
from core.characters import Splat
from core.characters.wod import Vampire


@pytest.mark.parametrize("splat", list(Splat))
def test_class_should_fail(splat: Splat):
    if splat == Splat.VAMPIRE:
        assert wod.creation_class(splat) == Vampire
    else:
        with pytest.raises(KeyError):
            _ = wod.creation_class(splat)


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
