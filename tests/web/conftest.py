"""Common fixtures."""

from unittest.mock import Mock

import pytest


@pytest.fixture
def guild():
    guild = Mock()
    guild.name = "The Fake Guild"
    guild.id = 1
    guild.icon.url = "https://example.com/icon.png"

    return guild
