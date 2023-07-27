"""Roll tests."""

import pytest

import errors
from characters import Character, GameLine
from rolls.parse import RollParser
from rolls.roll import Roll


@pytest.fixture
def dice() -> list[int]:
    return [1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10]


def test_cofd_explosions():
    # Ensure we get more dice, on average, than the pool
    trials = 10000
    pool = 10

    def _average_rolled(target: int) -> float:
        total = 0
        for _ in range(trials):
            roll = Roll(line=GameLine.COFD, dice=pool, target=target)
            roll.roll()
            total += len(roll.rolled)

            # Make sure we rolled the correct number of dice irrespective of
            # any explosions.
            assert len(roll.rolled) - sum(d >= target for d in roll.rolled) == pool

        return total / trials

    average_t10 = _average_rolled(10)
    average_t9 = _average_rolled(9)
    average_t8 = _average_rolled(8)

    assert average_t8 > average_t9 > average_t10 > 10


@pytest.mark.parametrize(
    "difficulty,expected,wp,specialties",
    [
        (2, 14, False, None),
        (2, 15, True, None),
        (2, 15, False, ["Spec"]),
        (2, 16, True, ["Spec"]),
        (3, 12, False, None),
        (3, 13, True, None),
        (3, 13, False, ["Spec"]),
        (3, 14, True, ["Spec"]),
        (4, 10, False, None),
        (4, 11, True, None),
        (4, 11, False, ["Spec"]),
        (4, 12, True, ["Spec"]),
        (5, 8, False, None),
        (5, 9, True, None),
        (5, 9, False, ["Spec"]),
        (5, 10, True, ["Spec"]),
        (6, 6, False, None),
        (6, 7, True, None),
        (6, 7, False, ["Spec"]),
        (6, 8, True, ["Spec"]),
        (7, 4, False, None),
        (7, 5, True, None),
        (7, 5, False, ["Spec"]),
        (7, 6, True, ["Spec"]),
        (8, 2, False, None),
        (8, 3, True, None),
        (8, 3, False, ["Spec"]),
        (8, 4, True, ["Spec"]),
        (9, 0, False, None),
        (9, 1, True, None),
        (9, 1, False, ["Spec"]),
        (9, 2, True, ["Spec"]),
        (10, -2, False, None),
        (10, 1, True, None),
        (10, -1, False, ["Spec"]),
        (10, 1, True, ["Spec"]),
    ],
)
def test_wod_successes(
    difficulty: int, expected: int, wp: bool, specialties: list[str], dice: list[int]
):
    roll = Roll(
        line=GameLine.WOD,
        target=difficulty,
        dice=len(dice),
        wp=wp,
        specialties=specialties,
    )
    # roll.roll()
    roll.rolled = dice

    assert roll.successes == expected


@pytest.mark.parametrize("pool", list(range(10)))
def test_cofd_specialties(pool: int):
    # We use target = 11 so we never explode
    roll = Roll(line=GameLine.COFD, dice=pool, target=11, specialties=["Yes"]).roll()
    assert len(roll.rolled) == pool + 1


def test_cofd_successes(dice: list[int]):
    roll = Roll(line=GameLine.COFD, dice=len(dice), target=10)
    roll.rolled = dice
    assert roll.successes == 5


@pytest.mark.parametrize(
    "syntax,pool,wp,specialties",
    [
        ("stren + br", ["Strength", "+", "Brawl"], False, None),
        ("stren + br.kin + wp", ["Strength", "+", "Brawl (Kindred)", "+", "WP"], True, ["Kindred"]),
    ],
)
def test_roll_parsing(
    syntax: str, pool: list[str], wp: bool, specialties: list[str], skilled: Character
):
    target = 6 if skilled.line == GameLine.WOD else 10
    p = RollParser(syntax, skilled).parse()
    roll = Roll.from_parser(p, target).roll()

    # We don't test output or dice count, because those are tested above
    assert roll.syntax == syntax
    assert roll.pool == pool
    assert roll.specialties == specialties
    assert roll.wp == wp
    assert roll.character == skilled


def test_autos():
    roll = Roll(line=GameLine.WOD, dice=0, target=6, autos=2).roll()
    assert roll.successes == 2

    roll.rolled = [1]
    assert roll.successes == 1
    roll.rolled = [1, 1]
    assert roll.successes == 0
    roll.rolled = [1, 1, 1]
    assert roll.successes == -1


def test_missing_game_line():
    p = RollParser("3", None)
    with pytest.raises(errors.MissingGameLine):
        Roll.from_parser(p, 6)
