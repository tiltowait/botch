"""Character selection utilities."""

import functools
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar, cast

import discord
from discord import ButtonStyle
from discord.ui import Button, Select

from bot import AppCtx
from config import GAME_LINE
from core.cache import cache
from core.characters import Character, GameLine, Splat
from errors import (
    CharacterIneligible,
    CharacterNotFound,
    NoCharacterSelected,
    NoMatchingCharacter,
)

T = TypeVar("T")
P = ParamSpec("P")


def haven(
    line: GameLine | str | None = GAME_LINE,
    splat: Splat | None = None,
    filter: Callable[[Character], bool] = lambda _: True,
) -> Callable[
    [Callable[Concatenate[AppCtx, Character, P], Coroutine[Any, Any, T]]],
    Callable[Concatenate[AppCtx, str | Character, P], Coroutine[Any, Any, T]],
]:
    def inner(
        func: Callable[Concatenate[AppCtx, Character, P], Coroutine[Any, Any, T]]
    ) -> Callable[Concatenate[AppCtx, str | Character, P], Coroutine[Any, Any, T]]:
        """A decorator that automatically selects a character."""

        @functools.wraps(func)
        async def wrapper(
            ctx: AppCtx,
            char: str | Character,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> T:
            if not isinstance(char, Character):
                haven = Haven(ctx, line, splat, char, filter)
                char = await haven.get_match()

            return await func(ctx, char, *args, **kwargs)

        return wrapper

    return inner


class Haven(discord.ui.View):
    """A View that presents a character selector if the character to use is
    ambiguous."""

    def __init__(
        self,
        ctx: AppCtx,
        line: GameLine | None,
        splat: Splat | None,
        character: str | Character | None,
        filter: Callable[[Character], bool] = lambda _: True,
    ):
        self.ctx = ctx
        self.line = line
        self.splat = splat
        self.character = character
        self.chars: list[Character] = []
        self.filter = filter
        self._populated = False
        self.selected: Character | None = None
        self.new_interaction: discord.Interaction | None = None

        super().__init__(timeout=60, disable_on_timeout=True)

    async def _populate(self):
        """Get the available characters."""
        if not self._populated:
            characters = await cache.fetchall(
                self.ctx.guild.id,
                self.ctx.user.id,
                line=self.line,
                splat=self.splat,
            )
            self.unfiltered = characters
            self.chars = [char for char in characters if self.filter(char)]
            self._populated = True

    async def get_match(self) -> Character:
        """Get the sole matching character, given the parameters. If there are
        multiple matches, then it presents a selection menu to the user.

        Returns: The sole matching or user-selected character.

        Raises:
            CharacterIneligible if the user specified a non-matching character.
            CharacterNotFound if the user specified a nonexistent character.
            NoMatchingCharacter if none of the user's characters match.

        """
        if isinstance(self.character, Character):
            # We were given a character already
            if self.filter(self.character):
                return self.character
            raise NoMatchingCharacter(f"**{self.character.name}** does not match.")

        await self._populate()
        if self.character:
            try:
                char = next(c for c in self.unfiltered if c.name.lower() == self.character.lower())
                if self.filter(char):
                    return char
                raise CharacterIneligible(f"**{char.name}** does not match." "")
            except StopIteration as err:
                raise CharacterNotFound(f"**{self.character}** not found.") from err

        if len(self.chars) == 1:
            return self.chars[0]

        if not self.chars:
            raise NoMatchingCharacter("No matching character found.")

        # User must select from among multiple matches
        self._add_buttons()
        await self.ctx.respond(embed=self._embed(), view=self, ephemeral=True)
        await self.wait()
        await self.ctx.delete()

        if self.selected is None:
            raise NoCharacterSelected
        return self.selected

    def _embed(self) -> discord.Embed:
        """The selection embed."""
        return discord.Embed(
            title="Select a character",
            description=f"Found `{len(self.chars)}` matching characters.",
        )

    def _add_buttons(self):
        """Add the selection buttons to this view."""
        if len(self.chars) <= 5:
            for char in self.chars:
                button = Button(label=char.name, style=ButtonStyle.primary)
                button.callback = self._callback
                self.add_item(button)
        else:
            sel = Select(placeholder="Select a character")
            sel.callback = self._callback
            for char in self.chars:
                sel.add_option(label=char.name)
            self.add_item(sel)

    async def _callback(self, interaction: discord.Interaction):
        """Set the selected character."""
        self.new_interaction = interaction
        self.stop()

        for i, child in enumerate(self.children):
            child = cast(Button, child)
            if child.custom_id == interaction.custom_id:
                self.selected = self.chars[i]
                break
