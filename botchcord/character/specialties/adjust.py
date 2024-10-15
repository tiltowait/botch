"""Specialties addition and removal."""

from enum import Enum

import errors
from bot import AppCtx
from botchcord.character.specialties.tokenize import tokenize
from botchcord.haven import haven
from botchcord.utils import CEmbed
from core.characters import Character
from utils import format_join


class Action(Enum):
    """An enum representing the action state."""

    ADD = 0
    REMOVE = 1


@haven()
async def assign(ctx: AppCtx, character: Character, syntax: str):
    """Add specialties to one or more of the character's traits."""
    await _add_or_remove(ctx, character, syntax, Action.ADD)


@haven()
async def remove(ctx: AppCtx, character: Character, syntax: str):
    """Remove specialties from one or more of the character's traits."""
    await _add_or_remove(ctx, character, syntax, Action.REMOVE)


async def _add_or_remove(
    ctx: AppCtx,
    character: Character,
    syntax: str,
    _action: Action,
):
    """Perform the actual work of adding or removing a spec."""
    if _action == Action.ADD:
        action = add_specialties
        title = "Specialties added"
    else:
        action = remove_specialties
        title = "Specialties removed"

    additions = action(character, syntax)
    embed = _make_embed(ctx, character, additions, title)

    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def _make_embed(
    ctx: AppCtx,
    character: Character,
    additions: list,
    title: str,
):
    """Create the embed."""
    entries = []
    for trait, delta in additions:
        delta_str = format_join(delta, ", ", "`", "*No change*")

        entry = f"**{trait.name}:** {delta_str}"
        if len(delta) != len(trait.subtraits):
            specs_str = format_join(trait.subtraits, ", ", "*", "*None*")
            entry += f"\n***All:*** {specs_str}\n"
            entry = "\n" + entry
        entries.append(entry)

    content = "\n".join(entries).strip()
    embed = CEmbed(ctx.bot, character, title=title, description=content)
    embed.set_footer(
        text="See all attributes, skills, custom traits, and specialties with /traits list."
    )

    return embed


def add_specialties(character: Character, syntax: str) -> list:
    """Add specialties to the character."""
    return _mod_specialties(character, syntax, True)


def remove_specialties(character: Character, syntax: str) -> list:
    """Remove specialties from a character."""
    return _mod_specialties(character, syntax, False)


def _mod_specialties(character: Character, syntax: str, adding: bool):
    """Do the actual work of adding or removing specialties."""
    tokens = tokenize(syntax)
    validate_tokens(character, tokens)

    # We have the traits; add the specialties
    traits = []
    for trait, specs in tokens:
        if adding:
            new_trait, delta = character.add_subtraits(trait, specs)
        else:
            new_trait, delta = character.remove_subtraits(trait, specs)
        traits.append((new_trait, delta))

    return traits


def validate_tokens(character: Character, tokens: list[tuple[str, list[str]]]):
    """Raise an exception if the character is missing one of the traits."""
    missing = []
    errs = []
    for trait, subtraits in tokens:
        if not character.has_trait(trait):
            missing.append(trait)
        if not errs:
            for subtrait in map(str.lower, subtraits):
                if subtrait == trait.lower():
                    errs.append("A subtrait can't have the same name as the parent trait.")

    if missing:
        if len(missing) == 1:
            # We want the part of the error with the character name to come first
            errs.insert(0, f"**{character.name}** has no trait named `{missing[0]}`.")
        else:
            missing = ", ".join(map(lambda t: f"`{t}`", missing))
            errs.insert(0, f"**{character.name}** doesn't have the following traits: {missing}.")

    if errs:
        raise errors.TraitError("\n\n".join(errs))
