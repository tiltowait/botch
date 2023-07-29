"""Roll command implementation."""

import re
from enum import IntEnum
from typing import Optional

import discord

import botchcord
import utils
from botch.characters import GameLine
from botch.rolls import Roll
from botch.rolls.parse import RollParser


class Color(IntEnum):
    BOTCH = 0xFF0000
    FAILURE = 0x777777
    MARGINAL_SUCCESS = 0xB2FCB2
    MODERATE_SUCCESS = 0x66E166
    COMPLETE_SUCCESS = 0x38DE38
    EXCEPTIONAL_SUCCESS = 0x00FF00
    PHENOMENAL_SUCCESS = 0x5865F2


async def roll(
    ctx: discord.ApplicationContext,
    pool: str,
    difficulty: int,
    specialties: Optional[str],
    comment: Optional[str],
):
    """Perform and display the specified roll. The roll is saved to the database."""
    rp = RollParser(pool, None).parse()
    roll = Roll.from_parser(rp, difficulty, GameLine.WOD).roll()

    if specialties:
        split = re.split(r"[\s*,\s*]", utils.normalize_text(specialties))
        if roll.specialties is None:
            roll.specialties = split
        else:
            roll.specialties.extend(split)

    embed = build_embed(ctx, roll, comment)
    await ctx.respond(embed=embed)
    # await roll.insert()


def build_embed(ctx: discord.ApplicationContext, roll: Roll, comment: str) -> discord.Embed:
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

    # TODO: Emojis
    embed = discord.Embed(
        title=embed_title(roll),
        description=textify_dice(roll),
        color=embed_color(roll),
    )
    embed.add_field(name="Dice", value=str(roll.num_dice))

    if roll.wod:
        embed.add_field(name="Difficulty", value=str(roll.target))
    if roll.specialties:
        embed.add_field(
            name="Specialty" if len(roll.specialties) == 1 else "Specialties",
            value=", ".join(roll.specialties),
        )
    if roll.pool and len(roll.pool) > 1:
        embed.add_field(name="Pool", value=" ".join(roll.pool), inline=False)

    embed.set_author(name=author_name, icon_url=icon or discord.Embed.Empty)

    if comment:
        embed.set_footer(text=comment)

    return embed


def embed_title(roll: Roll):
    """Generate the title for the embed."""
    title = roll.success_str
    if roll.successes != 0:
        title += f" ({roll.successes})"
    return title


def textify_dice(roll: Roll):
    """Convert the dice into text."""

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
        return Color.BOTCH
    if roll.successes == 0:
        return Color.FAILURE
    if roll.successes >= 5:
        # CofD calls this exceptional, but we use the WoD convention here
        return Color.PHENOMENAL_SUCCESS

    if roll.cofd:
        # It's a regular success
        return Color.COMPLETE_SUCCESS

    # The number of successes is between 1 and 4, so we can just construct
    # the enum rather than switching through
    match roll.successes:
        case 1:
            return Color.MARGINAL_SUCCESS
        case 2:
            return Color.MODERATE_SUCCESS
        case 3:
            return Color.COMPLETE_SUCCESS
        case 4:
            return Color.EXCEPTIONAL_SUCCESS
        case _:
            raise ValueError("Unexpected success count")
