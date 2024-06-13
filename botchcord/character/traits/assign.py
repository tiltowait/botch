"""Functions for adding/updating character traits. Not inclusive of subtraits."""


import discord
from pyparsing import (
    Dict,
    Group,
    OneOrMore,
    ParseException,
    Suppress,
    Word,
    alphas,
    nums,
)

import bot
from botchcord.haven import haven
from botchcord.utils import CEmbed
from botchcord.utils.text import m
from core.characters import Character, Trait


@haven()
async def assign(
    ctx: discord.ApplicationContext,
    character: Character,
    user_input: str,
):
    """Assign the traits and inform the user."""
    parsed = parse_input(user_input)
    traits = assign_traits(character, parsed)
    embed = build_embed(ctx.bot, character, traits)

    await character.save()
    await ctx.respond(embed=embed, ephemeral=True)


def build_embed(
    bot: bot.BotchBot,
    char: Character,
    assignments: list[Trait],
) -> CEmbed:
    """Build the embed describing the trait assignments."""
    embed = CEmbed(
        bot,
        char,
        title="Traits assigned",
        description=describe_assignments(assignments),
    )
    return embed


def describe_assignments(traits: list[Trait]) -> str:
    """Create the embed description for the trait assignments."""
    return "\n".join(map(lambda t: f"{t.name}: {m(t.rating)}", traits))


def assign_traits(
    char: Character,
    assignments: dict[str, int],
    category=Trait.Category.CUSTOM,
    subcategory=Trait.Subcategory.BLANK,
) -> list[Trait]:
    """Assigns the new/updated traits and returns the traits in their canonical
    form; e.g. predefined traits become capitalized: brawl -> Brawl."""
    assigned = []
    for trait, rating in assignments.items():
        if char.has_trait(trait):
            t = char.update_trait(trait, rating)
        else:
            t = char.add_trait(trait, rating, category, subcategory)
        assigned.append(t)

    return assigned


def parse_input(user_input: str) -> dict[str, int]:
    """Parse the user's input and find all the traits and ratings."""
    alphascore = alphas + "_"
    equals = Suppress("=")
    trait = Group(Word(alphas, alphascore + nums) + equals + Word(nums))
    traits = Dict(OneOrMore(trait))

    try:
        parsed = traits.parse_string(user_input, parse_all=True)
    except ParseException:
        raise SyntaxError("Invalid syntax! **Example:** `Brawl=3 Strength=2`")

    # Create dictionary, converting ratings to ints
    traits_dict = {}
    seen = set()
    for trait, rating in parsed:
        if trait in seen:
            raise SyntaxError(f"Duplicate trait: {trait}")

        seen.add(trait)
        traits_dict[trait] = int(rating)

    return traits_dict
