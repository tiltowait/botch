"""Functions for adding/updating character traits. Not inclusive of subtraits."""

from pyparsing import DelimitedList, Dict, Group, ParseException, Suppress, Word, nums

from botch import bot, errors
from botch.botchcord.haven import haven
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import m
from botch.core.characters import Character, Trait
from botch.core.utils.parsing import TRAIT


@haven()
async def assign(ctx: bot.AppCtx, character: Character, user_input: str):
    """Assign the traits and inform the user."""
    parsed = parse_input(user_input)
    traits = assign_traits(character, parsed, subcategory=Trait.Subcategory.CUSTOM)
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
    equals = Suppress("=")
    trait = Group(TRAIT + equals + Word(nums))
    traits = Dict(DelimitedList(trait, delim=";"))  # type: ignore

    try:
        parsed = traits.parse_string(user_input, parse_all=True)
    except ParseException:
        raise errors.TraitSyntaxError("Invalid syntax!\n\n**Example:** `Brawl=3; Strength=2`")

    # Create dictionary, converting ratings to ints
    traits_dict: dict[str, int] = {}
    seen: set[str] = set()
    duplicates = set()
    for trait_name, rating in parsed:
        if len(trait_name) > 20:
            raise errors.TraitError("Traits cannot be more than 20 characters long.")
        if trait_name in seen:
            duplicates.add(trait_name)

        seen.add(trait_name)
        traits_dict[trait_name] = int(rating)

    if duplicates:
        raise errors.TraitSyntaxError(
            "Duplicate trait(s):\n" + "\n".join(f"* {m(dup)}" for dup in duplicates)
        )

    return traits_dict
