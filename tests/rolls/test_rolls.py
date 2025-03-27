"""Roll tests."""

from unittest.mock import patch

import pytest

from botch import errors
from botch.core.characters import Character, GameLine
from botch.core.rolls.parse import RollParser, evaluate
from botch.core.rolls.roll import Roll

TRIALS = 1000


@pytest.fixture
def dice() -> list[int]:
    return [1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10]


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("1+2", 3),
        ("1+2-3", 0),
        ("4-6", -2),
    ],
)
def test_evaluate(expr: str, expected: int):
    assert evaluate(expr) == expected


def test_cofd_explosions():
    # Ensure we get more dice, on average, than the pool
    pool = 10

    def _average_rolled(target: int) -> float:
        total = 0
        for _ in range(TRIALS):
            roll = Roll(line=GameLine.COFD, guild=0, user=0, num_dice=pool, target=target)
            roll.roll()
            total += len(roll.dice)

            # Make sure we rolled the correct number of dice irrespective of
            # any explosions.
            assert len(roll.dice) - sum(d >= target for d in roll.dice) == pool

        return total / TRIALS

    average_t10 = _average_rolled(10)
    average_t9 = _average_rolled(9)
    average_t8 = _average_rolled(8)

    assert average_t8 > average_t9 > average_t10 > 10


@pytest.mark.parametrize(
    "line,dice,specs,wp,expected",
    [
        # None of the options should change WoD readout
        (GameLine.WOD, [5] * 5, None, False, "5"),
        (GameLine.WOD, [5] * 5, ["a"], False, "5"),
        (GameLine.WOD, [5] * 5, None, True, "5"),
        (GameLine.COFD, [5] * 5, None, False, "5"),
        (GameLine.COFD, [5] * 6, None, False, "5 *+ [1]*"),
        (GameLine.COFD, [5] * 9, None, True, "5 *+ [1]* *+ WP*"),
        (GameLine.COFD, [5] * 8, None, True, "5 *+ WP*"),
        (GameLine.COFD, [5] * 6, ["a"], False, "6"),
        (GameLine.COFD, [5] * 7, ["a"], False, "6 *+ [1]*"),
        (GameLine.COFD, [5] * 9, ["a"], True, "6 *+ WP*"),
        (GameLine.COFD, [5] * 10, ["a"], True, "6 *+ [1]* *+ WP*"),
    ],
)
def test_dice_readout(
    line: GameLine, dice: list[int], specs: list[str] | None, wp: bool, expected: str
):
    roll = Roll(
        line=line,
        guild=0,
        user=0,
        num_dice=5,
        target=10,
        specialties=specs,
        dice=dice,
        wp=wp,
    )
    assert roll.dice_readout == expected


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
        (11, -3, False, None),  # Unrealistic case
        (10, 1, True, None),
        (10, 0, False, ["Spec"]),
        (10, 1, True, ["Spec"]),
    ],
)
def test_wod_successes(
    difficulty: int, expected: int, wp: bool, specialties: list[str], dice: list[int]
):
    roll = Roll(
        line=GameLine.WOD,
        guild=0,
        user=0,
        target=difficulty,
        num_dice=len(dice),
        dice=dice,
        wp=wp,
        specialties=specialties,
    )
    assert roll.successes == expected


@pytest.mark.parametrize("pool", list(range(10)))
def test_cofd_specialties(pool: int):
    # We use target = 11 so we never explode
    roll = Roll(
        line=GameLine.COFD, guild=0, user=0, num_dice=pool, target=11, specialties=["Yes"]
    ).roll()
    assert len(roll.dice) == pool + 1


def test_cofd_successes(dice: list[int]):
    roll = Roll(line=GameLine.COFD, guild=0, user=0, num_dice=len(dice), target=10, dice=dice)
    assert roll.successes == 5


async def test_roll_spec_coalescing():
    # Without specs
    roll = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=5, target=6).roll()
    assert roll.specialties == []
    await roll.insert()
    assert roll.specialties is None

    # Now with specs
    roll = Roll(
        line=GameLine.WOD,
        guild=0,
        user=0,
        num_dice=5,
        target=6,
        specialties=["Throws"],
    ).roll()
    assert roll.specialties == ["Throws"]
    await roll.insert()
    assert roll.specialties == ["Throws"]


@patch("botch.core.rolls.Roll.save")
async def test_add_specs(mocked):
    roll = Roll(
        line=GameLine.WOD,
        guild=0,
        user=0,
        num_dice=5,
        target=6,
    ).roll()
    mocked.side_effect = roll.reset_specialties

    assert roll.specialties == []
    await roll.save()
    mocked.assert_awaited_once()

    assert roll.specialties is None
    roll.add_specs(["spec"])
    assert roll.specialties == ["spec"]


@pytest.mark.parametrize(
    "syntax,pool,wp,specialties",
    [
        ("stren + br", ["Strength", "+", "Brawl"], False, []),
        ("stren + br.kin + wp", ["Strength", "+", "Brawl (Kindred)", "+", "WP"], True, ["Kindred"]),
    ],
)
def test_roll_parsing(
    syntax: str, pool: list[str], wp: bool, specialties: list[str], skilled: Character
):
    target = 6 if skilled.line == GameLine.WOD else 10
    p = RollParser(syntax, skilled).parse()
    roll = Roll.from_parser(p, 0, 0, target).roll()

    # We don't test output or dice count, because those are tested above
    assert roll.syntax == syntax
    assert roll.pool == pool
    assert roll.specialties == specialties
    assert roll.wp == wp
    assert roll.character == skilled


def test_needs_character():
    with pytest.raises(errors.RollError):
        RollParser("strength + brawl", None).parse()


def test_autos():
    roll = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=0, target=6, autos=2).roll()
    assert roll.successes == 2

    roll.dice = [1]
    assert roll.successes == 1
    roll.dice = [1, 1]
    assert roll.successes == 0
    roll.dice = [1, 1, 1]
    assert roll.successes == 0  # autos override botch possibility


@pytest.mark.parametrize(
    "dice,expected",
    [
        ([1], "🤣 Botch!"),
        ([2], "Failure"),
        ([8], "Marginal"),
        ([8, 8], "Moderate"),
        ([8, 8, 8], "Success"),
        ([8, 8, 8, 8], "Exceptional"),
        ([8, 8, 8, 8, 8], "Phenomenal!"),
        ([8, 8, 8, 8, 8, 8], "Phenomenal!"),
    ],
)
def test_wod_success_str(dice: list[int], expected: str):
    roll = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=0, dice=dice, target=6)
    assert roll.success_str == expected


@pytest.mark.parametrize(
    "dice,expected",
    [
        ([1], "Failure"),
        ([2], "Failure"),
        ([8], "Success"),
        ([8, 8], "Success"),
        ([8, 8, 8], "Success"),
        ([8, 8, 8, 8], "Success"),
        ([8, 8, 8, 8, 8], "Exceptional!"),
        ([8, 8, 8, 8, 8, 8], "Exceptional!"),
    ],
)
def test_cofd_success_str(dice: list[int], expected: str):
    roll = Roll(line=GameLine.COFD, guild=0, user=0, num_dice=0, dice=dice, target=10)
    assert roll.success_str == expected


def test_cofd_wp():
    # Set target to 11 so there are no explosions
    roll = Roll(line=GameLine.COFD, guild=0, user=0, num_dice=10, target=11, wp=True).roll()
    assert len(roll.dice) == 13


def test_cofd_rote():
    def _average_successes(rote: bool):
        total = 0
        for _ in range(TRIALS):
            total += (
                Roll(line=GameLine.COFD, guild=0, user=0, num_dice=10, target=10, rote=rote)
                .roll()
                .successes
            )
        return total / TRIALS

    assert _average_successes(True) > _average_successes(False)


@pytest.mark.parametrize(
    "spec,expected",
    [
        (None, None),
        ([], None),
        (["spec"], ["spec"]),
    ],
)
async def test_roll_spec_coalescence(spec: list[str] | None, expected: list[str] | None):
    r = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=5, target=6, specialties=spec).roll()
    assert r.specialties == spec
    await r.insert()

    r2 = await Roll.find_one()
    assert r2 is not None
    assert r.id == r2.id
    assert r2.specialties == expected


def test_remaining_eval():
    assert evaluate("-1") == -1, "unary op didn't run"
    with pytest.raises(TypeError):
        evaluate("noop")
