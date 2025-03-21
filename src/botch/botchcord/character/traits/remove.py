"""Trait removal command and methods."""

import discord
from pyparsing import DelimitedList, ParseException

from botch import bot, errors
from botch.botchcord.haven import haven
from botch.botchcord.utils import CEmbed
from botch.core.characters import Character
from botch.core.utils.parsing import TRAIT


@haven()
async def remove(ctx: bot.AppCtx, character: Character, user_input: str):
    """Remove the traits from the character and display the result."""
    parsed = parse_input(user_input)
    found, missing = remove_traits(character, parsed)
    embed = build_embed(ctx.bot, character, found, missing)

    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def build_embed(
    bot: bot.BotchBot, character: Character, removed: list[str], not_found: list[str]
) -> CEmbed:
    """Build the embed."""
    embed = CEmbed(bot, character, title="Traits removed")

    if removed:
        embed.add_field(name="Removed", value="\n".join(removed))
    if not_found:
        embed.add_field(name="Not found!", value="\n".join(not_found))

    if not_found and not removed:
        embed.colour = discord.Colour.red()

    return embed


def remove_traits(
    character: Character,
    traits: list[str],
) -> tuple[list[str], list[str]]:
    """Remove the traits from the character. Does not persist changes to the
    database."""
    removed = []
    not_found = []

    for trait in traits:
        try:
            t = character.remove_trait(trait)
            removed.append(t)
        except errors.TraitNotFound:
            not_found.append(trait)

    return removed, not_found


def parse_input(user_input: str) -> list[str]:
    """Parse the input into the list of traits to delete."""
    trait = DelimitedList(TRAIT, delim=";")

    try:
        parsed = trait.parse_string(user_input, parse_all=True)
    except ParseException:
        raise errors.TraitSyntaxError("Invalid syntax!\n\n**Example:** `foo; bar`")

    return list(parsed)
