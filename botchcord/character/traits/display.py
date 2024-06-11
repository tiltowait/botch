"""Character trait display functions."""

from collections import defaultdict

import discord

import bot
from botchcord.utils import CEmbed
from botchcord.utils.text import b
from core.characters import Character, Trait


def build_embed(bot: bot.BotchBot, char: Character) -> discord.Embed:
    embed = CEmbed(bot, char, title="Character Traits")

    for category in Trait.Category:
        add_trait_category(embed, char, category)

    return embed


def add_trait_category(
    embed: discord.Embed,
    char: Character,
    category: Trait.Category,
):
    traits = categorize_traits(category, char.traits)
    if traits:
        embed.add_field(name=category.upper(), value=" ", inline=False)
        for sub, traits in traits.items():
            add_trait_subcategory(embed, sub.title(), traits)


def add_trait_subcategory(
    embed: discord.Embed,
    name: str,
    traits: list[Trait],
    inline=True,
):
    """Add a trait category (column) to the embed."""
    embed.add_field(name=name, value=printout(traits), inline=inline)


def categorize_traits(category: Trait.Category, traits: list[Trait]) -> dict[str, list[Trait]]:
    """Categorize the traits based on their category and subcategory."""
    categorized = defaultdict(list)
    for trait in traits:
        if trait.category == category:
            categorized[trait.subcategory].append(trait)

    return categorized


def printout(traits: list[Trait]) -> str:
    """Create a list of traits."""
    return "\n".join(map(lambda t: f"{b(t.name + ':')} {t.rating}", traits))
