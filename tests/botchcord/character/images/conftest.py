"""Common mocks for image commands."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
async def mock_char_cd() -> AsyncGenerator[AsyncMock, None]:
    # We already have a base character fixture, but its save method
    # isn't mocked
    with patch.multiple(
        "core.characters.base.Character", save=AsyncMock(), delete=AsyncMock()
    ) as mocked:
        yield mocked
