"""Character renaming."""

from botch.bot import AppCtx
from botch.botchcord.haven import haven
from botch.botchcord.utils.text import b
from botch.core import cache
from botch.core.characters import Character
from botch.core.characters.base import GameLine
from botch.errors import CharacterAlreadyExists
from botch.utils import normalize_text


@haven()
async def rename(ctx: AppCtx, character: Character, new_name: str):
    """Rename a character."""
    new_name = normalize_text(new_name)
    await validate_name(character.guild, character.user, character.line, new_name)

    old_name = character.name
    character.name = new_name
    await character.save()

    await ctx.respond(f"Renamed {b(old_name)} to {b(new_name)}.", ephemeral=True)


async def validate_name(guild: int, user: int, line: GameLine, name: str):
    """Raises a CharacterAlreadyExists if the user has a character by that name."""
    current = await cache.fetchnames(guild, user, line)
    if name.lower() in map(str.lower, current):
        raise CharacterAlreadyExists(f"You already have a character named {b(name)}.")
