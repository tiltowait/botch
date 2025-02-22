"""Character cache."""

import bisect

from cachetools import TTLCache

import errors
from core.characters import Character, GameLine, Splat
from utils import normalize_text


class CharCache:
    """The character cache simply manages characters based on user,
    name, and guild. It does not perform any access control."""

    def __init__(self):
        self._cache: TTLCache[str, list[Character]] = TTLCache(maxsize=100, ttl=1800)

    @staticmethod
    def key(guild: int, user: int) -> str:
        """The cache key, which is simply guild.user."""
        return f"{guild}.{user}"

    async def count(
        self, guild: int, user: int, line: GameLine | None = None, splat: Splat | None = None
    ) -> int:
        """Get the number of characters the user has."""
        chars = await self.fetchall(guild, user, line=line, splat=splat)
        return len(chars)

    async def fetchall(
        self, guild: int, user: int, line: GameLine | None = None, splat: Splat | None = None
    ) -> list[Character]:
        """Fetch the user's characters."""
        key = self.key(guild, user)
        if key not in self._cache:
            chars = await Character.find(
                Character.guild == guild,
                Character.user == user,
                with_children=True,
            ).to_list()

            self._cache[key] = sorted(chars, key=lambda c: c.name.casefold())

        chars = self._cache[key]
        if line is not None:
            chars = [char for char in chars if char.line == line]
        if splat is not None:
            chars = [char for char in chars if char.splat == splat]

        return chars

    async def fetchnames(
        self,
        guild: int,
        user: int,
        line: GameLine | None = None,
        splat: Splat | None = None,
    ) -> list[str]:
        """Fetch just the characters' names."""
        chars = await self.fetchall(guild, user, line=line, splat=splat)
        return [char.name for char in chars]

    async def fetchone(
        self,
        guild: int,
        user: int,
        name: str,
        line: GameLine | None = None,
        splat: Splat | None = None,
    ) -> Character:
        """Fetch a single character by name."""
        name = name.casefold()
        chars = await self.fetchall(guild, user, line=line, splat=splat)
        for char in chars:
            if char.name.casefold() == name.casefold():
                return char
        raise errors.CharacterNotFound(f"**{name}** not found.")

    async def has_character(self, guild: int, user: int, name: str) -> bool:
        """Whether the user has a character by the given name.

        Args:
            guild (int): The guild to check
            user (int): The user owning the character
            name (str): The name to check

        Returns:
            True if the user already has a character by that name.
        """
        chars = await self.fetchall(guild, user)
        name = normalize_text(name).casefold()
        for char in chars:
            if char.name.casefold() == name:
                return True

        return False

    async def register(self, character: Character):
        """Insert the character and register it in the cache."""
        # Fetch the characters first, otherwise we'll end up with an extra
        # character in the list after insort if this is the first fetchone has
        # been used for this user.
        chars = await self.fetchall(character.guild, character.user)
        await character.save()
        bisect.insort(chars, character, key=lambda c: c.name.casefold())

    async def remove(self, character: Character):
        """Delete the character from the database and remove from the cache."""
        chars = await self.fetchall(character.guild, character.user)
        try:
            chars.remove(character)
            await character.delete()
        except ValueError:
            raise errors.CharacterNotFound(
                f"**{character.name}** not found. Perhaps it was already deleted?"
            )


cache = CharCache()
