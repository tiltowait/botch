"""Character display routines."""

import logging
from enum import StrEnum

import discord

from botch import bot, botchcord, errors
from botch.botchcord.haven import haven
from botch.botchcord.utils import CEmbed
from botch.botchcord.utils.text import b
from botch.core.characters import Character, Damage, GameLine, Splat
from botch.core.characters.cofd import Mummy

logger = logging.getLogger("CHAR DISPLAY")


class DisplayField(StrEnum):
    """Character display fields."""

    NAME = "Name"
    HEALTH = "Health"
    WILLPOWER = "Willpower"
    GROUNDING = "Grounding"
    SEKHEM = "Sekhem"
    GENERATION = "Generation"
    BLOOD_POOL = "Blood Pool"
    EXPERIENCE = "Experience"
    BLOOD_POTENCY = "Blood Potency"
    VITAE = "Vitae"
    PILLARS = "Pillars"


DEFAULT_FIELDS = {
    GameLine.COFD: {
        Splat.MORTAL: (
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.EXPERIENCE,
        ),
        Splat.VAMPIRE: (
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.EXPERIENCE,
            DisplayField.BLOOD_POTENCY,
            DisplayField.VITAE,
        ),
        Splat.MUMMY: (
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.SEKHEM,
            DisplayField.PILLARS,
            DisplayField.EXPERIENCE,
        ),
    },
    GameLine.WOD: {
        Splat.MORTAL: (
            # DisplayField.NAME,
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.EXPERIENCE,
        ),
        Splat.GHOUL: (
            # DisplayField.NAME,
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.EXPERIENCE,
        ),
        Splat.VAMPIRE: (
            # DisplayField.NAME,
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
            DisplayField.GENERATION,
            DisplayField.BLOOD_POOL,
            DisplayField.EXPERIENCE,
        ),
    },
}


@haven()
async def display(ctx: bot.AppCtx, character: Character, *, owner: discord.Member | None = None):
    """Display a character."""
    if owner:
        logger.info("Admin %s invoking %s's %s", ctx.author.name, owner.name, character.name)

    use_emojis = await botchcord.settings.use_emojis(ctx)
    embed = build_embed(
        ctx.bot,
        character,
        use_emojis,
    )
    await ctx.respond(embed=embed)


def build_embed(
    bot: bot.BotchBot,
    character: Character,
    emojis: bool,
    *,
    fields: tuple[DisplayField, ...] | None = None,
    title="",
    description="",
    thumbnail: str | None = None,
    author_tag: str | None = None,
    icon_url: str | None = None,
    image: str | None = None,
    footer: str | None = None,
) -> CEmbed:
    """Build the character embed."""
    embed = CEmbed(bot, character, title=title or character.name, description=description)

    if not fields:
        fields = get_default_fields(character)
    for field in fields:
        if field == DisplayField.EXPERIENCE:
            # TODO: Re-enable if/when XP is implemented
            continue
        add_display_field(embed, bot, character, field, emojis)
        # embed.add_field(
        #     name=get_field_name(character, field),
        #     value=get_field_value(bot, character, field, emojis),
        #     inline=False,
        # )
    if footer:
        embed.set_footer(text=footer)

    return embed


def add_display_field(
    embed: discord.Embed,
    bot: bot.BotchBot,
    character: Character,
    field: DisplayField,
    use_emojis: bool,
    inline=False,
):
    """Add a specified display field to an embed."""
    if field_value := get_field_value(bot, character, field, use_emojis):
        embed.add_field(
            name=get_field_name(character, field),
            value=field_value,
            inline=inline,
        )


def get_field_name(character: Character, field: DisplayField) -> str:
    """Return the display field's name."""
    match field:
        case DisplayField.GROUNDING:
            return character.grounding.path
        case DisplayField.EXPERIENCE:
            return "Experience (Unspent / Lifetime)"
        case _:
            return field.value


def get_field_value(
    bot: bot.BotchBot,
    character: Character,
    field: DisplayField,
    use_emoji: bool,
) -> str | None:
    """Get the value for a particular field."""
    match field:
        case DisplayField.NAME:
            return character.name
        case DisplayField.HEALTH:
            if use_emoji:
                return emojify_track(bot, character.health)
            return get_track_string(character.health)
        case DisplayField.WILLPOWER:
            if use_emoji:
                return emojify_track(bot, character.willpower)
            return get_track_string(character.willpower)
        case DisplayField.GROUNDING:
            return str(character.grounding.rating)
        case DisplayField.SEKHEM:
            return character.sekhem
        case DisplayField.GENERATION:
            return str(character.generation)
        case DisplayField.BLOOD_POOL:
            return f"```{character.blood_pool} / {character.max_bp}```"
        case DisplayField.EXPERIENCE:
            return f"```{character.experience.unspent} / {character.experience.lifetime}```"
        case DisplayField.BLOOD_POTENCY:
            return f"```{character.blood_potency}```"
        case DisplayField.VITAE:
            return f"```{character.vitae} / {character.max_vitae}```"
        case DisplayField.PILLARS:
            return get_pillars(character)


def emojify_track(bot: bot.BotchBot, track: str) -> str:
    """Convert a track to emoji."""
    return " ".join(map(lambda e: bot.find_emoji(Damage.emoji_name(e)), reversed(track)))


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


def get_default_fields(character: Character) -> tuple[DisplayField, ...]:
    """Get the appropriate default fields for the character."""
    if character.line not in DEFAULT_FIELDS:
        raise errors.CharacterTemplateNotFound(f"Unknown game line `{character.line}`.")

    line = DEFAULT_FIELDS[character.line]
    if character.splat not in line:
        raise errors.CharacterTemplateNotFound(f"Unknown splat `{character.splat}`.")

    return line[character.splat]


def get_pillars(mummy: Character) -> str | None:
    """Get the Mummy's Pillars."""
    if not isinstance(mummy, Mummy):
        return None

    lines = []
    for pillar in mummy.pillars:
        lines.append(f"{b(pillar.name)}: {pillar.temporary} / {pillar.rating}")

    return "\n".join(lines)
