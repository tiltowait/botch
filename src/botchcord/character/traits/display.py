"""Character trait display functions."""

import logging
from collections import defaultdict

import discord

import bot
from botchcord.haven import haven
from botchcord.utils import CEmbed
from botchcord.utils.text import b, m
from core.characters import Character, Trait

logger = logging.getLogger("TRAITS")


@haven()
async def display(ctx: bot.AppCtx, character: Character, *, owner: discord.Member | None = None):
    """Display the character's traits."""
    if owner:
        logger.info("%s listing %s's %s's traits", ctx.author.name, owner.name, character.name)

    embed = build_embed(ctx.bot, character)
    await ctx.respond(embed=embed, ephemeral=True)


def build_embed(bot: bot.BotchBot, char: Character) -> discord.Embed:
    embed = CEmbed(bot, char, title="Character Traits")

    for category in Trait.Category:
        add_trait_category(embed, char, category)
    add_specialties_field(embed, char)

    return embed


def add_trait_category(
    embed: discord.Embed,
    char: Character,
    category: Trait.Category,
):
    traits = categorize_traits(category, char.display_traits)
    if traits:
        if category == Trait.Category.CUSTOM:
            category = " "  # type: ignore
        embed.add_field(name=" ", value=b(category.upper()), inline=False)
        for _sub, _traits in traits.items():
            add_trait_subcategory(embed, _sub.title(), _traits)


def add_trait_subcategory(
    embed: discord.Embed,
    name: str,
    traits: list[Trait],
    inline=True,
):
    """Add a trait category (column) to the embed."""
    embed.add_field(name=name, value=printout(traits), inline=inline)


def add_specialties_field(embed: discord.Embed, char: Character):
    """Add a field displaying specialties."""
    lines = format_specialties(char.traits)
    if lines:
        if embed.fields[-2].value != "** **":
            # For consistency's sake, let's add that blank embed first
            embed.add_field(name=" ", value="** **", inline=False)
        embed.add_field(name="Specialties", value="\n".join(lines))


def format_specialties(traits: list[Trait]) -> list[str]:
    """Given a list of traits, prep the formatted lines for the embed."""
    return [f"**{t.name}:** {', '.join(map(m, t.subtraits))}" for t in traits if t.subtraits]


def categorize_traits(category: Trait.Category, traits: list[Trait]) -> dict[str, list[Trait]]:
    """Categorize the traits based on their category and subcategory."""
    categorized = defaultdict(list)
    for trait in traits:
        if trait.category == category:
            categorized[trait.subcategory.value].append(trait)

    return categorized


def printout(traits: list[Trait]) -> str:
    """Create a list of traits."""
    return "\n".join(map(lambda t: f"{b(t.name + ':')} {t.rating}", traits))
