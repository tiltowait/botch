"""Character display routines."""

from enum import StrEnum

import discord

import bot
import botchcord
import errors
from botchcord.haven import haven
from core.characters import Character, Damage, GameLine, Splat


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
    }
}


@haven()
async def display(ctx: discord.ApplicationContext, character: Character):
    user = ctx.bot.get_user(character.user)
    use_emojis = await botchcord.settings.use_emojis(ctx)
    embed = build_embed(
        ctx.bot,
        character,
        use_emojis,
        author_tag=user.display_name,
        icon_url=botchcord.get_avatar(user),
    )
    await ctx.respond(embed=embed)


def build_embed(
    bot: bot.BotchBot,
    character: Character,
    emojis: bool,
    *,
    fields: list[DisplayField] | None = None,
    title="",
    description="",
    thumbnail: str | None = None,
    author_tag: str | None = None,
    icon_url: str | None = None,
    image: str | None = None,
    footer: str | None = None,
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
            value=get_field_value(bot, character, field, emojis),
            inline=False,
        )
    if footer:
        embed.set_footer(text=footer)

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


def get_field_value(bot: bot.BotchBot, character: Character, field: DisplayField, use_emoji: bool):
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
        case DisplayField.GENERATION:
            return str(character.generation)
        case DisplayField.BLOOD_POOL:
            return f"```{character.blood_pool} / {character.max_bp}```"
        case DisplayField.EXPERIENCE:
            return f"```{character.experience.unspent} / {character.experience.lifetime}```"


def emojify_track(bot: bot.BotchBot, track: str) -> str:
    """Convert a track to emoji."""
    return " ".join(map(lambda e: bot.get_emoji(Damage.emoji_name(e)), track))


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
