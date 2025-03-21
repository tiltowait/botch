"""Specialties addition and removal."""

from enum import Enum

from botch import errors
from botch.bot import AppCtx
from botch.botchcord.character.specialties.tokenize import tokenize
from botch.botchcord.haven import haven
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import b, i, m
from botch.core.characters import Character
from botch.utils import format_join


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


async def _add_or_remove(ctx: AppCtx, character: Character, syntax: str, action: Action):
    """Perform the actual work of adding or removing a spec."""
    action_func = add_specialties if action == Action.ADD else remove_specialties
    title = "Specialties added" if action == Action.ADD else "Specialties removed"

    additions = action_func(character, syntax)
    embed = _make_embed(ctx, character, additions, title)

    await ctx.respond(embed=embed, ephemeral=True)
    await character.save()


def _make_embed(ctx: AppCtx, character: Character, additions: list, title: str) -> CEmbed:
    """Create the embed."""
    entries = []
    for trait, delta in additions:
        delta_str = format_join(delta, ", ", "`", "*No change*")
        entry = f"**{trait.name}:** {delta_str}"
        if len(delta) != len(trait.subtraits):
            specs_str = format_join(trait.subtraits, ", ", "*", i("None"))
            entry = f"\n{entry}\n***All:*** {specs_str}\n"
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

    mod_func = character.add_subtraits if adding else character.remove_subtraits
    return [mod_func(trait, specs) for trait, specs in tokens]


def validate_tokens(character: Character, tokens: list[tuple[str, list[str]]]):
    """Raise an exception if the character is missing one of the traits."""
    missing = [trait for trait, _ in tokens if not character.has_trait(trait)]
    errs = []

    if missing:
        if len(missing) == 1:
            errs.append(f"{b(character.name)} has no trait named `{missing[0]}`.")
        else:
            missing_str = ", ".join(m(t) for t in missing)
            errs.append(f"{b(character.name)} doesn't have the following traits: {missing_str}.")

    for trait, subtraits in tokens:
        if any(subtrait.lower() == trait.lower() for subtrait in subtraits):
            errs.append("A subtrait can't have the same name as the parent trait.")
            break

    if errs:
        raise errors.TraitError("\n\n".join(errs))
