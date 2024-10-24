"""Web cache."""

import secrets
from string import ascii_letters, digits

from cachetools import TTLCache

from config import GAME_LINE
from web.models import WizardSchema


class WizardCache:
    """Maintains a cache for character creation wizard web tokens."""

    def __init__(self, ttl: int = 1200, token_size: int = 12):
        self._cache: TTLCache[str, WizardSchema] = TTLCache(maxsize=100, ttl=ttl)
        self.ttl = ttl
        self.token_size = token_size

    def __contains__(self, token: str) -> bool:
        return token in self._cache

    def _generate_token(self) -> str:
        """Generates a securerandom token."""
        prefix = f"{GAME_LINE}_"
        token = "".join(
            secrets.choice(ascii_letters + digits) for _ in range(self.token_size - len(prefix))
        )
        return f"{prefix}{token}"

    def register(self, schema: WizardSchema) -> str:
        """Caches the schema, then returns the access token."""
        token = self._generate_token()
        self._cache[token] = schema

        return token

    def get(self, token: str) -> WizardSchema:
        """Get the schema associated with the token."""
        if token not in self._cache:
            raise ValueError

        return self._cache[token]

    def remove(self, token: str):
        """Deregister the web token."""
        if token in self._cache:
            del self._cache[token]
