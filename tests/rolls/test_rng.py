"""Miscellaneous roll tests."""

import pytest

from core.rolls.roll import d10


def test_single_d10():
    for _ in range(10000):
        num = d10()
        assert isinstance(num, int)
        assert 1 <= num <= 10


@pytest.mark.parametrize("count", [n for n in range(1, 101)])
def test_multiple_d10s(count: int):
    dice = d10(count)
    assert len(dice) == count
    assert all(1 <= d <= 10 for d in dice)
