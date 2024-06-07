"""Character display routines."""

from enum import StrEnum

import discord

import errors
from botch.characters import Character, Damage, GameLine, Splat


class DisplayField(StrEnum):
    """Character display fields."""

    NAME = "Name"
    HEALTH = "Health"
    WILLPOWER = "Willpower"
    GROUNDING = "Grounding"
    GENERATION = "Generation"
    BLOOD_POOL = "Blood Pool"
    EXPERIENCE = "Experience"


DEFAULT_FIELDS = {
    GameLine.WOD: {
        Splat.MORTAL: (
            DisplayField.NAME,
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.EXPERIENCE,
        ),
        Splat.VAMPIRE: (
            DisplayField.NAME,
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.GENERATION,
            DisplayField.BLOOD_POOL,
            DisplayField.EXPERIENCE,
        ),
    }
}


def build_embed(
    character: Character,
    emojis: bool,
    *,
    fields: list[DisplayField] | None = None,
    title="",
    description="",
    thumbnail: str = discord.Embed.Empty,
    author_tag: str = discord.Embed.Empty,
    icon_url: str = discord.Embed.Empty,
    image: str = discord.Embed.Empty,
):
    """Build the character embed."""
    embed = discord.Embed(title=title or character.name, description=description)
    embed.set_author(name=author_tag, icon_url=icon_url)
    embed.set_thumbnail(url=thumbnail)

    if not fields:
        fields = get_default_fields(character)
    for field in fields:
        embed.add_field(
            name=get_field_name(character, field),
            value=get_field_value(character, field, emojis),
            inline=False,
        )

    return embed


def get_field_name(character: Character, field: DisplayField):
    """Return the display field's name."""
    match field:
        case DisplayField.GROUNDING:
            return character.grounding.path
        case DisplayField.EXPERIENCE:
            return "Experience (Unspent / Lifetime)"
        case _:
            return field.value


def get_field_value(character: Character, field: DisplayField, use_emoji: bool):
    """Get the value for a particular field."""
    match field:
        case DisplayField.NAME:
            return character.name
        case DisplayField.HEALTH:
            if use_emoji:
                raise NotImplementedError("Track emoji are not yet implemented")
            return get_track_string(character.health)
        case DisplayField.WILLPOWER:
            if use_emoji:
                raise NotImplementedError("Track emoji are not yet implemented")
            return get_track_string(character.willpower)
        case DisplayField.GROUNDING:
            return str(character.grounding.rating)
        case DisplayField.GENERATION:
            return str(character.generation)
        case DisplayField.BLOOD_POOL:
            return f"```{character.blood_pool} / {character.max_bp}```"
        case DisplayField.EXPERIENCE:
            return f"```{character.experience.unspent} / {character.experience.lifetime}```"


def get_track_string(track: str) -> str:
    """Get a track's description."""
    counts = []
    if aggravated := track.count(Damage.AGGRAVATED):
        counts.append(f"{aggravated} Aggravated")
    if lethal := track.count(Damage.LETHAL):
        counts.append(f"{lethal} Lethal")
    if bashing := track.count(Damage.BASHING):
        counts.append(f"{bashing} Bashing")
    if unhurt := track.count(Damage.NONE):
        counts.append(f"{unhurt} Unhurt")

    return "\n".join(counts)


def get_default_fields(character: Character) -> tuple:
    """Get the appropriate default fields for the character."""
    if character.line not in DEFAULT_FIELDS:
        raise errors.CharacterTemplateNotFound(f"Unknown game line `{character.line}`.")

    line = DEFAULT_FIELDS[character.line]
    if character.splat not in line:
        raise errors.CharacterTemplateNotFound(f"Unknown splat `{character.splat}`.")

    return line[character.splat]
