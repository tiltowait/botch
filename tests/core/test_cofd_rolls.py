"""CofD roll tests."""

from typing import Generator
from unittest.mock import Mock, patch

import pytest

from botch.core.characters import GameLine
from botch.core.rolls.roll import Roll


@pytest.fixture
def mock_d10() -> Generator[Mock, None, None]:
    with patch("botch.core.rolls.roll.d10") as mock:
        yield mock


@pytest.fixture
def roll() -> Roll:
    return Roll(
        line=GameLine.COFD,
        guild=0,
        user=0,
        num_dice=5,
        target=10,
    )


@pytest.mark.parametrize(
    "dice,expected,success_str",
    [
        ([5, 5, 5, 5, 5], 0, "Failure"),
        ([8, 5, 5, 5, 5], 1, "Success"),
        ([8, 5, 5, 8, 8], 3, "Success"),
        ([8, 8, 8, 8, 8], 5, "Exceptional!"),
    ],
)
def test_plain_success_count(
    mock_d10: Mock,
    roll: Roll,
    dice: list[int],
    expected: int,
    success_str: str,
):
    mock_d10.side_effect = dice

    roll.roll()
    assert roll.successes == expected
    assert roll.success_str == success_str


@pytest.mark.parametrize(
    "target, dice,expected",
    [
        (10, [5, 5, 5, 5, 5], 5),
        (10, [10, 5, 5, 5, 5, 5], 6),
        (10, [10, 5, 5, 5, 5, 10, 5], 7),
        (10, [10, 5, 5, 8, 9, 10, 10, 5], 8),
        (9, [5, 5, 5, 9, 8, 5], 6),
        (9, [5, 5, 10, 9, 8, 5, 5], 7),
        (8, [5, 5, 5, 7, 8, 5], 6),
        (8, [5, 5, 5, 9, 8, 5, 7], 7),
        (8, [5, 5, 5, 9, 8, 5, 10, 7], 8),
    ],
)
def test_explosions(mock_d10: Mock, roll: Roll, target: int, dice: list[str], expected: int):
    mock_d10.side_effect = dice
    roll.target = target
    roll.roll()

    assert len(roll.dice) == expected


def test_blessed(mock_d10: Mock, roll: Roll):
    mock_d10.side_effect = [5] * 5 + [8] * 5
    roll.blessed = True
    roll.roll()

    assert roll.dice == [8] * 5


def test_blighted(mock_d10: Mock, roll: Roll):
    mock_d10.side_effect = [8] * 5 + [5] * 5
    roll.blighted = True
    roll.roll()

    assert roll.dice == [5] * 5


def test_rote(mock_d10: Mock, roll: Roll):
    mock_d10.side_effect = [8, 5, 5, 5, 5] + [6] * 4
    roll.rote = True
    roll.roll()

    assert roll.dice == [8, 6, 6, 6, 6]


def test_rote_explodes(mock_d10: Mock, roll: Roll):
    second = [10, 6, 6, 6, 6, 6]
    mock_d10.side_effect = [5] * 5 + second
    roll.rote = True
    roll.roll()

    assert roll.dice == second


def test_blessed_rote(mock_d10: Mock, roll: Roll):
    mock_d10.side_effect = [5] * 5 + [6] * 5 + [8] * 5
    roll.blessed = True
    roll.rote = True
    roll.roll()

    assert roll.dice == [8] * 5
    assert roll.successes == 5


def test_complex_rote(mock_d10: Mock, roll: Roll):
    mock_d10.side_effect = [10, 8, 5, 5, 8, 10, 7, 10, 8, 7, 10, 8, 5, 5, 10, 8, 6]
    roll.rote = True
    roll.wp = True
    roll.roll()

    assert roll.dice == [10, 8, 8, 10, 10, 8, 10, 8, 5, 5, 10, 8, 6]
    assert roll.dice_readout == "5 *+ 5X* *+ WP*"


def test_selects_longer_roll(mock_d10: Mock, roll: Roll):
    first = [8, 5, 5, 5, 5]
    second = [10, 6, 6, 6, 6, 6]
    mock_d10.side_effect = first + second
    roll.blessed = True
    roll.roll()

    assert roll.dice == second


@pytest.mark.parametrize(
    "dice,wp,specs,expected",
    [
        ([5, 5, 5, 5, 5], False, False, "5"),
        ([5, 5, 5, 5, 5, 5, 5, 5], True, False, "5 *+ WP*"),
        ([5, 5, 5, 5, 5, 5, 5, 5, 5], True, True, "6 *+ WP*"),
        ([5, 5, 5, 5, 5, 5], False, True, "6"),
        ([5, 5, 5, 5, 10, 5], False, False, "5 *+ 1X*"),
        ([5, 5, 5, 5, 10, 5, 5, 10, 5, 5], True, False, "5 *+ 2X* *+ WP*"),
        ([5, 5, 5, 5, 10, 5, 5], False, True, "6 *+ 1X*"),
        ([5, 5, 5, 5, 10, 5, 5, 5, 5, 5], True, True, "6 *+ 1X* *+ WP*"),
    ],
)
def test_dice_readout(
    mock_d10: Mock,
    roll: Roll,
    dice: list[int],
    wp: bool,
    specs: bool,
    expected: str,
):
    mock_d10.side_effect = dice
    roll.wp = wp
    if specs:
        roll.add_specs(["spec"])
    roll.roll()

    assert roll.dice_readout == expected


def test_readout_8_again(mock_d10: Mock, roll: Roll):
    dice = [10, 5, 5, 5, 9, 5, 5, 5, 8, 5, 5, 5]
    mock_d10.side_effect = dice
    roll.target = 8
    roll.wp = True
    roll.add_specs(["spec"])
    roll.roll()

    assert roll.dice == dice
    assert roll.dice_readout == "6 *+ 3X* *+ WP*"


def test_cofd_successes(roll: Roll):
    assert roll._cofd_successes([1, 2, 8]) == 1
