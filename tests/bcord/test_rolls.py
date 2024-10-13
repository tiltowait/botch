"""Discord roll tests."""

import re
from types import SimpleNamespace as SN
from typing import Optional
from unittest.mock import ANY, AsyncMock

import pytest

import core
import errors
from bot import AppCtx, BotchBot
from botchcord.roll import (
    DICE_CAP,
    DICE_CAP_MESSAGE,
    Color,
    build_embed,
    embed_color,
    embed_title,
    emoji_name,
    emojify_dice,
)
from botchcord.roll import roll as roll_cmd
from botchcord.roll import textify_dice
from core.characters import Character, GameLine, Splat, Trait
from core.rolls import Roll
from core.rolls.parse import RollParser
from tests.characters import gen_char


class EmojiMock:
    """For mocking the ctx.bot.get_emoji() calls."""

    def get_emoji(self, name):
        if re.match(r"^(ss?|f|b)\d+$", name):
            return name  # The real deal adds \u200b, but we don't need that here
        raise errors.EmojiNotFound


@pytest.fixture
def ctx() -> SN:
    return SN(bot=EmojiMock())


@pytest.fixture(autouse=True)
async def clear_cache():
    core.cache._cache = {}
    yield
    core.cache._cache = {}


@pytest.fixture
def wod_vampire() -> Character:
    vampire = gen_char(GameLine.WOD, Splat.VAMPIRE, name="Nadea Theron")
    vampire.profile.add_image("https://tilt-assets.s3-us-west-1.amazonaws.com/avatar.jpg")
    vampire.add_trait("Strength", 3, Trait.Category.ATTRIBUTE)
    vampire.add_trait("Brawl", 4, Trait.Category.ABILITY)
    vampire.add_subtraits("Brawl", ["Throws"])
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
    "dice,should_botch",
    [
        ([1, 1, 10], False),
        ([1, 5], True),
    ],
)
def test_botch_logic(dice: list[int], should_botch: bool):
    roll = Roll(line=GameLine.WOD, num_dice=len(dice), target=6, dice=dice)
    if should_botch:
        assert "Botch!" in embed_title(roll)
    else:
        assert "Botch!" not in embed_title(roll)


@pytest.mark.parametrize(
    "syntax,pool,extra_specs",
    [
        ("strength + brawl", "Strength + Brawl", ["Throws"]),
        ("strength + brawl.throws", "Strength + Brawl (Throws)", []),
    ],
)
def test_wod_roll_embed_with_specialties(
    syntax: str, pool: str, extra_specs: list[str], wod_vampire: Character
):
    rp = RollParser(syntax, wod_vampire).parse()
    roll = Roll.from_parser(rp, 6)
    roll.specialties.extend(extra_specs)

    embed = build_embed(None, roll, extra_specs, None, False)

    f = 2
    if extra_specs:
        assert embed.fields[f].name == "Bonus spec" if len(extra_specs) == 1 else "Bonus specs"
        assert embed.fields[f].value == ", ".join(extra_specs)
        f += 1
    assert embed.fields[f].name == "Pool"
    assert embed.fields[f].value == pool


@pytest.mark.parametrize(
    "title,pool,target,spec,comment",
    [
        ("Success (3)", None, 6, None, None),
        ("Exceptional (4)", ["7"], 5, None, None),
        ("Exceptional (4)", ["4", "+", "3"], 5, None, None),
        ("Phenomenal! (5)", None, 5, ["Bipping"], None),
        ("Phenomenal! (5)", ["4", "+", "3"], 5, ["Bipping", "Tripping"], "Comment"),
        ("Phenomenal! (5)", ["Strength", "+", "Brawl"], 5, ["Bipping", "Tripping"], "Comment"),
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
    # Normally, Roll.specialties and build_embed.extra_spec will be different;
    # however, because we aren't using trait pools in these rolls, there's no
    # issue in this section
    roll = Roll(
        line=GameLine.WOD,
        num_dice=len(dice),
        dice=dice,
        pool=pool,
        specialties=spec,
        target=target,
        character=wod_vampire,
    )

    embed = build_embed(None, roll, spec, comment, False)

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
        assert embed.fields[i].name == "Bonus spec" if len(spec) == 1 else "Bonus specs"
        assert embed.fields[i].value == ", ".join(spec)
        i += 1
    if roll.uses_traits:
        assert embed.fields[i].name == "Pool"
        assert embed.fields[i].value == " ".join(roll.pool)

    if comment:
        assert embed.footer.text == comment
    else:
        assert embed.footer is None

    assert embed.description == textify_dice(roll)


@pytest.mark.parametrize(
    "die,target,special,botchable,expected",
    [
        (1, 6, 10, True, "b1"),
        (1, 6, 10, False, "f1"),
        (2, 2, 10, False, "s2"),
        (2, 6, 10, True, "f2"),
        (3, 3, 10, True, "s3"),
        (3, 6, 10, True, "f3"),
        (4, 4, 10, True, "s4"),
        (4, 6, 10, True, "f4"),
        (5, 5, 10, True, "s5"),
        (5, 6, 10, True, "f5"),
        (10, 6, 11, True, "s10"),
        (10, 6, 10, True, "ss10"),
    ],
)
def test_emoji_name(die: int, target: int, special: int, botchable: bool, expected: str):
    assert emoji_name(die, target, special, botchable) == expected


def test_emoji_error(ctx):
    with pytest.raises(errors.EmojiNotFound):
        ctx.bot.get_emoji("this should fail")


@pytest.mark.parametrize(
    "target,expected,spec,line",
    [
        (6, ["b1", "f2", "f5", "s6", "s6", "s8", "s10"], None, GameLine.WOD),
        (6, ["b1", "f2", "f5", "s6", "s6", "s8", "ss10"], ["spec"], GameLine.WOD),
        (5, ["b1", "f2", "s5", "s6", "s6", "s8", "s10"], None, GameLine.WOD),
        (5, ["b1", "f2", "s5", "s6", "s6", "s8", "ss10"], ["spec"], GameLine.WOD),
        (8, ["f1", "f2", "f5", "f6", "f6", "ss8", "ss10"], ["spec"], GameLine.COFD),
        (8, ["f1", "f2", "f5", "f6", "f6", "ss8", "ss10"], None, GameLine.COFD),
        (10, ["f1", "f2", "f5", "f6", "f6", "s8", "ss10"], ["spec"], GameLine.COFD),
    ],
)
def test_emojify_dice(
    target: int, expected: list[str], spec: list[str], line: GameLine, dice: list[int], ctx: SN
):
    roll = Roll(line=line, num_dice=len(dice), dice=dice, target=target, specialties=spec)
    expected = " ".join(expected)
    assert emojify_dice(ctx, roll) == expected


def test_dice_caps(ctx):
    r = Roll(line=GameLine.WOD, num_dice=DICE_CAP, target=6).roll()
    assert textify_dice(r) != DICE_CAP_MESSAGE
    assert emojify_dice(ctx, r) != DICE_CAP_MESSAGE

    r = Roll(line=GameLine.WOD, num_dice=DICE_CAP + 1, target=6).roll()
    assert textify_dice(r) == DICE_CAP_MESSAGE
    assert emojify_dice(ctx, r) == DICE_CAP_MESSAGE


@pytest.mark.parametrize(
    "pool,char,specs,raises",
    [
        ("strength+brawl", None, None, False),
        ("strength+brawl", None, "Vicious", False),
        ("strength+brawl", "Nadea Theron", None, False),
        ("strength+brawl+1", "Nadea Theron", None, False),
        ("strength+brawl", "Nadea", None, True),
        ("fake", "Nadea", None, True),
        ("fake", "Nadea Theron", None, True),
        ("fake", None, None, True),
    ],
)
async def test_roll_command(
    pool: str,
    char: str | None,
    specs: str | None,
    raises: bool,
    wod_vampire: Character,
):
    bot = BotchBot()
    inter = AsyncMock()
    inter.user.id = wod_vampire.user
    inter.guild.id = wod_vampire.guild
    ctx = AppCtx(bot, inter)

    await core.cache.register(wod_vampire)  # Register so Haven finds her

    if raises:
        if char is None or char == wod_vampire.name:
            with pytest.raises(errors.RollError):
                await roll_cmd(ctx, pool, 6, specs, None, char)
        else:
            with pytest.raises(errors.CharacterNotFound):
                await roll_cmd(ctx, pool, 6, specs, None, char)

    else:
        await roll_cmd(ctx, pool, 6, specs, None, char)
        ctx.respond.assert_called_once_with(embed=ANY)
