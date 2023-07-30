"""Character cache."""


import bisect

import errors
from botch.characters import Character


class CharCache:
    """The character cache simply manages characters based on user,
    name, and guild. It does not perform any access control."""

    def __init__(self):
        self._cache = {}

    @staticmethod
    def key(guild: int, user: int) -> str:
        """The cache key, which is simply guild.user."""
        return f"{guild}.{user}"

    async def count(self, guild: int, user: int) -> int:
        """Get the number of characters the user has."""
        chars = await self.fetchall(guild, user)
        return len(chars)

    async def fetchall(self, guild: int, user: int) -> list[Character]:
        """Fetch the user's characters."""
        key = self.key(guild, user)
        if key not in self._cache:
            chars = await Character.find(Character.guild == guild, Character.user == user).to_list()
            self._cache[key] = chars
        return self._cache[key]

    async def fetchnames(self, guild: int, user: int) -> list[str]:
        """Fetch just the characters' names."""
        chars = await self.fetchall(guild, user)
        return [char.name for char in chars]

    async def fetchone(self, guild: int, user: int, name: str) -> Character:
        """Fetch a single character by name."""
        name = name.casefold()
        chars = await self.fetchall(guild, user)
        for char in chars:
            if char.name.casefold() == name.casefold():
                return char
        raise errors.CharacterNotFound

    async def register(self, character: Character):
        """Insert the character and register it in the cache."""
        # Fetch the characters first, otherwise we'll end up with an extra
        # character in the list after insort if this is the first fetchone has
        # been used for this user.
        chars = await self.fetchall(character.guild, character.user)
        await character.insert()
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
