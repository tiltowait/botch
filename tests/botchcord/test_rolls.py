"""Discord roll tests."""

from typing import Optional
from unittest.mock import ANY, AsyncMock, Mock, patch

import discord
import pytest
from cachetools import TTLCache

import core
import errors
from bot import AppCtx
from botchcord.roll import DICE_CAP, DICE_CAP_MESSAGE, Color, add_wp, build_embed
from botchcord.roll import chance as chance_cmd
from botchcord.roll import embed_color, embed_title, emoji_name, emojify_dice
from botchcord.roll import roll as roll_cmd
from botchcord.roll import textify_dice
from core.characters import Character, Damage, GameLine, Splat, Trait
from core.rolls import Roll
from core.rolls.parse import RollParser
from tests.characters import gen_char


@pytest.fixture(autouse=True)
async def clear_cache():
    core.cache._cache = TTLCache(maxsize=100, ttl=1800)
    yield
    core.cache._cache = TTLCache(maxsize=100, ttl=1800)


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
    target: int,
    expected: str,
    spec: Optional[list[str]],
    line: GameLine,
    dice: list[int],
):
    roll = Roll(
        line=line,
        guild=0,
        user=0,
        num_dice=len(dice),
        dice=dice,
        target=target,
        specialties=spec,
    )
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

    roll = Roll(line=line, guild=0, user=0, num_dice=successes, target=6, dice=dice)
    assert embed_color(roll) == expected


@pytest.mark.parametrize(
    "successes,expected,line",
    [
        (-2, "🤣 Botch! (-2)", GameLine.WOD),
        (-1, "🤣 Botch! (-1)", GameLine.WOD),
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

    roll = Roll(line=line, guild=0, user=0, num_dice=successes, target=6, dice=dice)
    assert embed_title(roll) == expected


@pytest.mark.parametrize(
    "dice,should_botch",
    [
        ([1, 1, 10], False),
        ([1, 5], True),
    ],
)
def test_botch_logic(dice: list[int], should_botch: bool):
    roll = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=len(dice), target=6, dice=dice)
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
    syntax: str,
    pool: str,
    extra_specs: list[str],
    wod_vampire: Character,
):
    rp = RollParser(syntax, wod_vampire).parse()
    roll = Roll.from_parser(rp, 0, 0, 6)
    roll.add_specs(extra_specs)

    embed = build_embed(Mock(), roll, extra_specs, None, False)

    f = 2
    if extra_specs:
        assert embed.fields[f].name == "Bonus spec" if len(extra_specs) == 1 else "Bonus specs"
        assert embed.fields[f].value == ", ".join(extra_specs)
        f += 1
    assert embed.fields[f].name == "Pool"
    assert embed.fields[f].value == pool


@pytest.mark.parametrize(
    "line,syntax,emojis",
    [
        (GameLine.WOD, "5", True),
        (GameLine.WOD, "5", False),
        (GameLine.WOD, "5+wp", True),
        (GameLine.WOD, "5+wp", False),
        (GameLine.COFD, "5+wp", True),
        (GameLine.COFD, "5+wp", False),
    ],
)
def test_wod_roll_embed_with_willpower(
    line: GameLine,
    syntax: str,
    emojis: bool,
    ctx: AppCtx,
):
    rp = RollParser(syntax, None).parse()
    roll = Roll.from_parser(rp, 0, 0, 6, line)

    embed = build_embed(ctx, roll, None, None, emojis)
    assert embed.description is not None
    if roll.wp and line == GameLine.WOD:
        assert embed.description.endswith(" *+ WP*")
    else:
        assert not embed.description.endswith(" *+ WP*")


@pytest.mark.parametrize(
    "autos",
    [0, 1, 2],
)
def test_roll_embed_with_autos(autos: int, ctx: AppCtx):
    rp = RollParser("5", None).parse()
    roll = Roll.from_parser(rp, 0, 0, 6, autos=autos)
    embed = build_embed(ctx, roll, None, None, False)

    assert embed.description is not None
    if autos == 0:
        assert "auto" not in embed.description
    elif autos == 1:
        assert embed.description.endswith(f" *+ {autos} auto*")
    else:
        assert embed.description.endswith(f" *+ {autos} autos*")


def test_build_embed_author_no_char():
    rp = RollParser("6", None).parse()
    roll = Roll.from_parser(rp, 0, 0, 6, GameLine.WOD)

    ctx = Mock()
    ctx.author = Mock(spec=discord.User)  # Make it a User to finish testing get_avatar()
    ctx.author.display_name = "Jimmy Maxwell"
    ctx.author.display_avatar = "https://example.com/icon.png"

    embed = build_embed(ctx, roll, None, None, True)
    assert embed.author is not None
    assert embed.author.name == "Jimmy Maxwell"
    assert embed.author.icon_url == "https://example.com/icon.png"
    assert isinstance(ctx.author, discord.User)


def test_build_embed_rote_again():
    rp = RollParser("6", None).parse()
    roll = Roll.from_parser(rp, 0, 0, 8, GameLine.COFD, True)

    ctx = Mock()
    ctx.author = Mock(spec=discord.User)  # Make it a User to finish testing get_avatar()
    ctx.author.display_name = "Jimmy Maxwell"
    ctx.author.display_avatar = "https://example.com/icon.png"

    embed = build_embed(ctx, roll, None, None, True)
    assert embed.author is not None
    assert embed.author.name == "Jimmy Maxwell • Rote • 8-again"


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
    pool: list[str | int],
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
        guild=0,
        user=0,
        num_dice=len(dice),
        dice=dice,
        pool=pool,
        specialties=spec,
        target=target,
        character=wod_vampire,
    )

    embed = build_embed(Mock(), roll, spec, comment, False)

    # Work our way down from the top
    assert embed.author is not None
    assert embed.author.name == wod_vampire.name
    assert embed.author.icon_url == wod_vampire.profile.main_image
    assert embed.color is not None
    assert embed.color.value == embed_color(roll)
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
        assert roll.pool
        assert embed.fields[i].value == " ".join(map(str, roll.pool))

    if comment:
        assert embed.footer is not None
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
        ctx.bot.find_emoji("this should fail")


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
    target: int,
    expected: list[str] | str,
    spec: list[str],
    line: GameLine,
    dice: list[int],
    ctx: Mock,
):
    roll = Roll(
        line=line,
        guild=0,
        user=0,
        num_dice=len(dice),
        dice=dice,
        target=target,
        specialties=spec,
    )
    expected = " ".join(expected)
    assert emojify_dice(ctx, roll) == expected


def test_dice_caps(ctx):
    r = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=DICE_CAP, target=6).roll()
    assert textify_dice(r) != DICE_CAP_MESSAGE
    assert emojify_dice(ctx, r) != DICE_CAP_MESSAGE

    r = Roll(line=GameLine.WOD, guild=0, user=0, num_dice=DICE_CAP + 1, target=6).roll()
    assert textify_dice(r) == DICE_CAP_MESSAGE
    assert emojify_dice(ctx, r) == DICE_CAP_MESSAGE


@pytest.mark.parametrize(
    "pool,char,specs,raises",
    [
        ("strength+brawl", None, None, False),
        ("strength+brawl", None, "Vicious", False),
        ("strength+brawl", "Nadea Theron", None, False),
        ("strength+brawl+1", "Nadea Theron", None, False),
        ("strength+brawl+wp", "Nadea Theron", None, False),
        ("5+wp", None, None, False),
        ("strength+brawl", "Nadea", None, True),
        ("fake", "Nadea", None, True),
        ("fake", "Nadea Theron", None, True),
        ("fake", None, None, True),
    ],
)
@patch("bot.BotchBot.find_emoji")
async def test_roll_command(
    mock_find_emoji: Mock,
    ctx: AppCtx,
    mock_respond: AsyncMock,
    pool: str,
    char: str | None,
    specs: str | None,
    raises: bool,
    wod_vampire: Character,
):
    mock_find_emoji.return_value = "."

    assert ctx.interaction.guild is not None
    assert ctx.interaction.user is not None
    ctx.interaction.guild.id = wod_vampire.guild
    ctx.interaction.user.id = wod_vampire.user
    ctx.interaction.guild.name = "Test Guild"

    await core.cache.register(wod_vampire)  # Register so Haven finds her

    if raises:
        if char is None or char == wod_vampire.name:
            with pytest.raises(errors.RollError):
                await roll_cmd(ctx, pool, 6, specs, False, False, None, char)
        else:
            with pytest.raises(errors.CharacterNotFound):
                await roll_cmd(ctx, pool, 6, specs, False, False, None, char)

    else:
        await roll_cmd(ctx, pool, 6, specs, False, False, None, char)
        mock_respond.assert_awaited_once_with(embed=ANY)

        assert mock_respond.await_args is not None
        embed = mock_respond.await_args.kwargs["embed"]

        if "wp" in pool:
            if char:
                assert wod_vampire.willpower.count(Damage.BASHING) == 1
                assert embed.fields[-1].name == "Willpower"
            else:
                assert embed.fields[-1].name != "Willpower"
        else:
            if char:
                assert wod_vampire.willpower.count(Damage.BASHING) == 0
            assert embed.fields[-1].name != "Willpower"


@pytest.mark.parametrize(
    "die, title",
    [
        (8, "Failure"),
        (1, "Critical failure"),
        (10, "Marginal success"),
    ],
)
@patch("bot.BotchBot.find_emoji")
@patch("botchcord.roll.emoji_name")
@patch("botchcord.roll.d10")
async def test_chance_cmd(
    find_emoji_mock: Mock,
    emoji_mock: Mock,
    d10_mock: Mock,
    ctx: AppCtx,
    mock_respond: AsyncMock,
    die: int,
    title: str,
):
    find_emoji_mock.return_value = die
    emoji_mock.return_value = die
    d10_mock.return_value = die

    await chance_cmd(ctx)
    mock_respond.assert_awaited_once_with(embed=ANY)

    embed: discord.Embed = mock_respond.await_args.kwargs["embed"]  # type:ignore
    assert embed.title is not None
    assert title in embed.title


@pytest.mark.parametrize(
    "pool,expected",
    [
        ("strength+brawl", "strength+brawl + WP"),
        ("strength+brawl+wp", "strength+brawl+wp"),
        ("wp+strength+brawl", "wp+strength+brawl"),
        ("strength + wp", "strength + wp"),
        ("1", "1 + WP"),
        ("strength+wp+brawl", "strength+wp+brawl"),
        ("wpwp", "wpwp + WP"),
        ("STRENGTH + WP", "STRENGTH + WP"),
        ("wP", "wP"),
    ],
)
def test_add_wp(pool: str, expected: str):
    assert add_wp(pool) == expected
