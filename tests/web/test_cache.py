import time
from string import ascii_letters, digits
from unittest.mock import MagicMock

import pytest
from cachetools import TTLCache

from web.cache import WizardCache
from web.models import WizardSchema


@pytest.fixture
def wizard_cache() -> WizardCache:
    return WizardCache()


def test_init(wizard_cache: WizardCache):
    assert isinstance(wizard_cache._cache, TTLCache)
    assert wizard_cache._cache.maxsize == 100
    assert wizard_cache._cache.ttl == 1200
    assert wizard_cache.token_size == 12


def test_contains(wizard_cache: WizardCache):
    mock_schema = MagicMock(spec=WizardSchema)
    token = wizard_cache.register(mock_schema)
    assert token in wizard_cache
    assert "non_existent_token" not in wizard_cache


def test_generate_token(wizard_cache: WizardCache):
    token = wizard_cache._generate_token()
    assert len(token) == wizard_cache.token_size
    assert all(c in ascii_letters + digits + "_" for c in token)


def test_register(wizard_cache: WizardCache):
    mock_schema = MagicMock(spec=WizardSchema)
    token = wizard_cache.register(mock_schema)
    assert token in wizard_cache._cache
    assert wizard_cache._cache[token] == mock_schema


def test_get_existing_token(wizard_cache: WizardCache):
    mock_schema = MagicMock(spec=WizardSchema)
    token = wizard_cache.register(mock_schema)
    retrieved_schema = wizard_cache.get(token)
    assert retrieved_schema == mock_schema


def test_get_non_existing_token(wizard_cache: WizardCache):
    with pytest.raises(ValueError):
        wizard_cache.get("non_existent_token")


def test_remove_existing_token(wizard_cache: WizardCache):
    mock_schema = MagicMock(spec=WizardSchema)
    token = wizard_cache.register(mock_schema)
    assert token in wizard_cache
    wizard_cache.remove(token)
    assert token not in wizard_cache


def test_remove_non_existing_token(wizard_cache: WizardCache):
    wizard_cache.remove("non_existent_token")  # Should not raise an exception


def test_ttl_expiration():
    wizard_cache = WizardCache(ttl=2)
    mock_schema = MagicMock(spec=WizardSchema)
    token = wizard_cache.register(mock_schema)
    assert token in wizard_cache

    time.sleep(1)
    assert token in wizard_cache

    time.sleep(1)
    assert token not in wizard_cache
