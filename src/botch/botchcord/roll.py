"""Roll command implementation."""

import re
from enum import IntEnum
from typing import Optional

import discord

from botch import bot, botchcord, errors, utils
from botch.botchcord.character.display import DisplayField, add_display_field
from botch.botchcord.haven import Haven
from botch.config import GAME_LINE
from botch.core.characters import Character, Damage, GameLine, Tracker
from botch.core.rolls import Roll, d10
from botch.core.rolls.parse import RollParser

DICE_CAP = 40
DICE_CAP_MESSAGE = "***Too many to show.***"


class Color(IntEnum):
    """Roll result colors from worst to best outcome.

    BOTCH: Bright red
    FAILURE: Gray
    MARGINAL_SUCCESS: Light green
    MODERATE_SUCCESS: Medium green
    COMPLETE_SUCCESS: Bright green
    EXCEPTIONAL_SUCCESS: Pure green
    PHENOMENAL_SUCCESS: Discord blurple"""

    BOTCH = 0xFF0000
    FAILURE = 0x777777
    MARGINAL_SUCCESS = 0xB2FCB2
    MODERATE_SUCCESS = 0x66E166
    COMPLETE_SUCCESS = 0x38DE38
    EXCEPTIONAL_SUCCESS = 0x00FF00
    PHENOMENAL_SUCCESS = 0x5865F2


def add_wp(pool: str) -> str:
    """Add '+ WP' to the pool syntax if it's not there already."""
    if not re.search(r"\bWP\b", pool, re.I):
        return pool + " + WP"
    return pool


async def roll(
    ctx: bot.AppCtx,
    pool: str,
    target: int,
    specialties: Optional[str],
    wp: bool,
    rote: bool,
    comment: Optional[str],
    character: Optional[str | Character],
    *,
    autos=0,
    blessed=False,
    blighted=False,
    owner: discord.Member | None = None,
):
    """Perform and display the specified roll. The roll is saved to the database."""
    if wp:
        pool = add_wp(pool)

    rp = RollParser(pool, None)
    if rp.needs_character or character:
        haven = Haven(
            ctx, GAME_LINE, None, character, owner, lambda c: RollParser.can_roll(c, pool)
        )
        try:
            if character := await haven.get_match():
                rp.character = character
        except errors.CharacterIneligible:
            raise errors.RollError(f"**{character}** is unable to roll `{pool}`.")
        except errors.NoMatchingCharacter:
            raise errors.RollError(f"No characters able to roll `{pool}`.")

    rp.parse()
    roll = Roll.from_parser(
        rp,
        ctx.guild.id,
        ctx.user.id,
        target,
        GAME_LINE,
        rote,
        autos,
        blessed,
        blighted,
    ).roll()

    extra_specs = []
    if specialties:
        extra_specs = re.split(r"\s*,\s*", utils.normalize_text(specialties))
        extra_specs = [e for e in extra_specs if e]  # Remove any empty strings
        roll.add_specs(extra_specs)

    if roll.wp and character:
        character.increment_damage(Tracker.WILLPOWER, Damage.BASHING)

    emojis = await botchcord.settings.use_emojis(ctx)
    embed = build_embed(ctx, roll, extra_specs, comment, emojis)

    await ctx.respond(embed=embed)
    await roll.save()


async def chance(ctx: bot.AppCtx):
    """Roll a chance die."""
    die = d10()
    if await botchcord.settings.use_emojis(ctx):
        diemoji = ctx.bot.find_emoji(emoji_name(die, 10, 10, True))
    else:
        diemoji = str(die)

    if die == 1:
        title = "🤣 Critical failure!"
        color = Color.BOTCH.value
    elif die < 10:
        title = "Failure"
        color = Color.FAILURE.value
    else:
        title = "Marginal success!"
        color = Color.MARGINAL_SUCCESS.value

    embed = discord.Embed(title=title, description=diemoji, colour=color)
    embed.set_author(name=ctx.author.display_name, icon_url=botchcord.get_avatar(ctx.author))

    await ctx.respond(embed=embed)


def build_embed(
    ctx: bot.AppCtx,
    roll: Roll,
    extra_specs: list[str] | None,
    comment: str | None,
    emojis: bool,
) -> discord.Embed:
    """Build the roll embed."""
    # We work our way top-down
    icon = None
    if roll.character:
        author_name = roll.character.name
        icon = roll.character.profile.main_image
    else:
        author_name = ctx.author.display_name
    if not icon:
        icon = botchcord.get_avatar(ctx.author)
    if roll.blessed:
        author_name += " • Blessed"
    elif roll.blighted:
        author_name += " • Blighted"
    if roll.rote:
        author_name += " • Rote"
    if roll.again < 10:
        author_name += f" • {roll.again}-again"

    if emojis:
        try:
            dice_description = emojify_dice(ctx, roll)
        except errors.EmojiNotFound:
            dice_description = textify_dice(roll)
    else:
        dice_description = textify_dice(roll)

    if roll.autos:
        auto_str = "auto" if roll.autos == 1 else "autos"
        dice_description += f" *+ {roll.autos} {auto_str}*"
    if roll.line == GameLine.WOD and roll.wp:
        dice_description += " *+ WP*"

    embed = discord.Embed(
        title=embed_title(roll),
        description=dice_description,
        color=embed_color(roll),
    )
    embed.add_field(name="Dice", value=roll.dice_readout)

    if roll.wod:
        embed.add_field(name="Difficulty", value=str(roll.target))
    if roll.specialties and extra_specs:
        embed.add_field(
            name="Bonus spec" if len(roll.specialties) == 1 else "Bonus specs",
            value=", ".join(roll.specialties),
        )
    if roll.uses_traits:
        assert roll.pool is not None
        embed.add_field(name="Pool", value=" ".join(map(str, roll.pool)), inline=False)
    if roll.wp and roll.character:
        add_display_field(embed, ctx.bot, roll.character, DisplayField.WILLPOWER, emojis)

    embed.set_author(name=author_name, icon_url=icon or None)

    if comment:
        embed.set_footer(text=comment)

    return embed


def embed_title(roll: Roll):
    """Generate the title for the embed."""
    title = roll.success_str
    if roll.successes != 0:
        title += f" ({roll.successes})"
    return title


def emojify_dice(ctx: bot.AppCtx, roll: Roll) -> str:
    """Generate the emoji for the roll."""
    if len(roll.dice) > DICE_CAP:
        return DICE_CAP_MESSAGE
    special = roll.again  # Will be 11 if WoD
    if roll.wod and roll.specialties:
        special = 10

    emojis = []
    for e in map(lambda d: emoji_name(d, roll.difficulty, special, roll.wod), roll.dice):
        emojis.append(ctx.bot.find_emoji(e))

    return " ".join(emojis)


def emoji_name(die: int, success: int, special: int, botchable: bool) -> str:
    """Generate the emoji name for a die.

    Args:
        die (int): The die in question
        success (int): What counts as a success
        special (int): If this number is hit, it's a special success

    Returns the emoji name."""
    if botchable and die == 1:
        emoji = "b1"
    elif die >= success:
        emoji = f"s{die}"
        if die >= special:
            emoji = f"s{emoji}"
    else:
        emoji = f"f{die}"
    return emoji


def textify_dice(roll: Roll) -> str:
    """Convert the dice into text."""
    if len(roll.dice) > DICE_CAP:
        return DICE_CAP_MESSAGE

    #   * Failures: strikethrough
    #   * Ones: Bold-italic (WoD)
    #   * Tens (spec): Bold
    #   * Explosions: Bold
    text = []
    for die in roll.dice:
        d = str(die)
        if die < roll.difficulty:
            d = f"~~{d}~~"
        if roll.wod:
            if die == 1:
                d = f"***{d}***"
            if die == 10 and roll.specialties:
                d = f"**{d}**"
        elif die >= roll.again:
            d = f"**{d}**"

        text.append(d)

    return ", ".join(text)


def embed_color(roll: Roll) -> int:
    """Determine the embed color for the roll."""
    if roll.successes < 0:
        return Color.BOTCH.value
    if roll.successes == 0:
        return Color.FAILURE.value
    if roll.successes >= 5:
        return Color.PHENOMENAL_SUCCESS.value

    if roll.cofd:
        return Color.COMPLETE_SUCCESS.value

    # Use a dictionary for WoD success levels
    wod_success_colors = {
        1: Color.MARGINAL_SUCCESS,
        2: Color.MODERATE_SUCCESS,
        3: Color.COMPLETE_SUCCESS,
        4: Color.EXCEPTIONAL_SUCCESS,
    }

    return wod_success_colors[roll.successes].value
