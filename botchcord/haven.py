"""Character selection utilities."""

import functools

import discord

from core.cache import cache
from core.characters import Character, GameLine, Splat


def haven(line: GameLine | None = None, splat: Splat | None = None):
    def inner(func):
        """A decorator that automatically selects a character."""
        functools.wraps(func)

        async def wrapper(ctx, char, *args, **kwargs):
            if not isinstance(char, Character):
                haven = Haven(ctx, line, splat, char)
                if (char := await haven.get_match()) is None:
                    # TODO: Present the selector
                    pass

            return await func(ctx, char, *args, **kwargs)

        return wrapper

    return inner


class Haven(discord.ui.View):
    """A View that presents a character selector if the character to use is
    ambiguous."""

    def __init__(
        self,
        ctx: discord.ApplicationContext,
        line: GameLine | None,
        splat: Splat | None,
        character: str | Character | None,
    ):
        self.ctx = ctx
        self.line = line
        self.splat = splat
        self.character = character
        self.chars: list[Character] | None = None

    async def _populate(self):
        """Get the available characters."""
        if self.chars is None:
            self.chars = await cache.fetchall(
                self.ctx.guild.id,
                self.ctx.user.id,
                line=self.line,
                splat=self.splat,
            )

    async def get_match(self) -> Character | None:
        """Get the match, assuming there's only one. If there are multiple,
        returns None."""
        await self._populate()
        if self.chars and len(self.chars) == 1:
            return self.chars[0]
        return None
