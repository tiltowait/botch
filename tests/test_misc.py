"""Miscellaneous tests."""

import pytest

import utils


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
