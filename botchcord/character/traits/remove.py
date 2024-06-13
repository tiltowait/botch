"""Trait removal command and methods."""

import discord
from pyparsing import OneOrMore, ParseException, Word, alphas, nums

import errors
from botchcord.haven import haven
from botchcord.utils import CEmbed
from core.characters import Character


@haven()
async def remove(ctx: discord.ApplicationContext, character: Character, user_input: str):
    """Remove the traits from the character and display the result."""
    parsed = parse_input(user_input)
    found, missing = remove_traits(character, parsed)
    embed = build_embed(ctx.bot, character, found, missing)

    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def build_embed(
    bot: discord.Bot, character: Character, removed: list[str], not_found: list[str]
) -> CEmbed:
    """Build the embed."""
    embed = CEmbed(bot, character, title="Traits removed")

    if removed:
        embed.add_field(name="Removed", value="\n".join(removed))
    if not_found:
        embed.add_field(name="Not found!", value="\n".join(not_found))

    if not_found and not removed:
        embed.color = discord.Color.red()

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
    alphascore = alphas + "_"
    trait = OneOrMore(Word(alphas, alphascore + nums))

    try:
        parsed = trait.parse_string(user_input, parse_all=True)
    except ParseException:
        raise SyntaxError("Invalid syntax! **Example:** `foo bar`")

    return list(parsed)
