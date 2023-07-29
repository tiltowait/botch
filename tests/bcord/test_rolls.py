"""Discord roll tests."""

from typing import Optional

import discord
import pytest

from botch.characters import Character, GameLine, Splat
from botch.rolls import Roll
from botchcord.roll import Color, build_embed, embed_color, embed_title, textify_dice
from tests.characters import gen_char


@pytest.fixture
def wod_vampire() -> Character:
    vampire = gen_char(GameLine.WOD, Splat.VAMPIRE, name="Nadea Theron")
    vampire.profile.images.append("https://tilt-assets.s3-us-west-1.amazonaws.com/avatar.jpg")
    return vampire


@pytest.fixture
def dice() -> list[int]:
    return [1, 2, 5, 6, 6, 8, 10]


@pytest.mark.parametrize(
    "target,expected,spec,line",
    [
        (2, "***~~1~~***, 2, 5, 6, 6, 8, 10", None, GameLine.WOD),
        (2, "***~~1~~***, 2, 5, 6, 6, 8, **10**", ["spec"], GameLine.WOD),
        (3, "***~~1~~***, ~~2~~, 5, 6, 6, 8, 10", None, GameLine.WOD),
        (3, "***~~1~~***, ~~2~~, 5, 6, 6, 8, **10**", ["spec"], GameLine.WOD),
        (8, "***~~1~~***, ~~2~~, ~~5~~, ~~6~~, ~~6~~, 8, **10**", ["spec"], GameLine.WOD),
        (10, "~~1~~, ~~2~~, ~~5~~, ~~6~~, ~~6~~, 8, **10**", None, GameLine.COFD),
        (8, "~~1~~, ~~2~~, ~~5~~, ~~6~~, ~~6~~, **8**, **10**", None, GameLine.COFD),
    ],
)
def test_textify_dice(
    target: int, expected: str, spec: Optional[list[str]], line: GameLine, dice: list[int]
):
    roll = Roll(line=line, num_dice=len(dice), dice=dice, target=target, specialties=spec)
    assert textify_dice(roll) == expected


@pytest.mark.parametrize(
    "successes,expected,line",
    [
        (0, Color.FAILURE, GameLine.WOD),
        (-1, Color.BOTCH, GameLine.WOD),
        (1, Color.MARGINAL_SUCCESS, GameLine.WOD),
        (2, Color.MODERATE_SUCCESS, GameLine.WOD),
        (3, Color.COMPLETE_SUCCESS, GameLine.WOD),
        (4, Color.EXCEPTIONAL_SUCCESS, GameLine.WOD),
        (5, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (6, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (7, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (8, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (9, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (10, Color.PHENOMENAL_SUCCESS, GameLine.WOD),
        (0, Color.FAILURE, GameLine.COFD),
        (1, Color.COMPLETE_SUCCESS, GameLine.COFD),
        (2, Color.COMPLETE_SUCCESS, GameLine.COFD),
        (3, Color.COMPLETE_SUCCESS, GameLine.COFD),
        (4, Color.COMPLETE_SUCCESS, GameLine.COFD),
        (5, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
        (6, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
        (7, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
        (8, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
        (9, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
        (10, Color.PHENOMENAL_SUCCESS, GameLine.COFD),
    ],
)
def test_embed_color(successes: int, expected: Color, line: GameLine):
    if successes < 0:
        dice = [1 for _ in range(abs(successes))]
    elif successes == 0:
        dice = [2]
    else:
        dice = [9 for _ in range(successes)]

    roll = Roll(line=line, num_dice=successes, target=6, dice=dice)
    assert embed_color(roll) == expected


@pytest.mark.parametrize(
    "successes,expected,line",
    [
        (-2, "Botch! (-2)", GameLine.WOD),
        (-1, "Botch! (-1)", GameLine.WOD),
        (0, "Failure", GameLine.WOD),
        (1, "Marginal (1)", GameLine.WOD),
        (2, "Moderate (2)", GameLine.WOD),
        (3, "Success (3)", GameLine.WOD),
        (4, "Exceptional (4)", GameLine.WOD),
        (5, "Phenomenal! (5)", GameLine.WOD),
        (6, "Phenomenal! (6)", GameLine.WOD),
        (0, "Failure", GameLine.COFD),
        (1, "Success (1)", GameLine.COFD),
        (2, "Success (2)", GameLine.COFD),
        (3, "Success (3)", GameLine.COFD),
        (4, "Success (4)", GameLine.COFD),
        (5, "Exceptional! (5)", GameLine.COFD),
        (6, "Exceptional! (6)", GameLine.COFD),
    ],
)
def test_embed_title(successes: int, expected: str, line: GameLine):
    if successes < 0:
        dice = [1 for _ in range(abs(successes))]
    elif successes == 0:
        dice = [2]
    else:
        dice = [9 for _ in range(successes)]

    roll = Roll(line=line, num_dice=successes, target=6, dice=dice)
    assert embed_title(roll) == expected


@pytest.mark.parametrize(
    "title,pool,target,spec,comment",
    [
        ("Success (3)", None, 6, None, None),
        ("Exceptional (4)", ["7"], 5, None, None),
        ("Exceptional (4)", ["4", "+", "3"], 5, None, None),
        ("Phenomenal! (5)", None, 5, ["Bipping"], None),
        ("Phenomenal! (5)", ["4", "+", "3"], 5, ["Bipping"], None),
    ],
)
def test_wod_text_embed_with_character(
    title: str,
    pool: list[str],
    target: int,
    spec: list[str],
    comment: str,
    dice: list[int],
    wod_vampire: Character,
):
    roll = Roll(
        line=GameLine.WOD,
        num_dice=len(dice),
        dice=dice,
        pool=pool,
        target=target,
        specialties=spec,
        character=wod_vampire,
    )

    embed = build_embed(None, roll, comment)

    # Work our way down from the top
    assert embed.author.name == wod_vampire.name
    assert embed.author.icon_url == wod_vampire.profile.main_image
    assert int(embed.color) == embed_color(roll)
    assert embed.title == title

    # Fields
    assert embed.fields[0].name == "Dice"
    assert embed.fields[0].value == str(roll.num_dice)
    assert embed.fields[1].name == "Difficulty"
    assert embed.fields[1].value == str(target)

    # The next fields are optional but follow a predictable pattern
    i = 2
    if spec:
        assert embed.fields[i].name == "Specialty"
        assert embed.fields[i].value == ", ".join(spec)
        i += 1
    if pool and len(pool) > 1:
        assert embed.fields[i].name == "Pool"
        assert embed.fields[i].value == " ".join(roll.pool)

    if comment:
        assert embed.footer.text == comment
    else:
        assert embed.footer.text == discord.Embed.Empty

    assert embed.description == textify_dice(roll)
