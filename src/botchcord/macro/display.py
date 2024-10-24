"""Macro display functions and command implementation.

Macros are displayed inside paginated embeds. Each macro is made into its
own "entry", which is how we avoid them being split across pages."""

from discord.ext.commands import Paginator as Chunker
from discord.ext.pages import Page, Paginator

import bot
from botchcord.haven import haven
from botchcord.utils import CEmbed
from botchcord.utils.text import i, m
from config import GAME_LINE
from core.characters import Character, Macro
from core.characters.base import GameLine


@haven(filter=lambda c: len(c.macros) > 0)
async def display(ctx: bot.AppCtx, character: Character):
    """Display the macros paginator."""
    paginator = create_paginator(ctx.bot, character)
    await paginator.respond(ctx.interaction, ephemeral=True)


def create_paginator(bot: bot.BotchBot, char: Character) -> Paginator:
    """Create the macro paginator."""
    pages = []
    for page_content in paginate_macros(char.macros):
        embed = CEmbed(bot, char, title="Macros", description=page_content)
        pages.append(Page(embeds=[embed]))

    return Paginator(pages)


def paginate_macros(macros: list[Macro]) -> list[str]:
    """Paginate the macro entries."""
    chunker = Chunker(prefix=None, suffix=None)
    for entry in map(create_macro_entry, macros):
        chunker.add_line(entry)

    return chunker.pages


def create_macro_entry(macro: Macro) -> str:
    """Create a macro display entry."""
    is_cofd = GAME_LINE == GameLine.COFD
    target = "Again" if is_cofd else "Difficulty"

    lines = [
        f"### {macro.name}",
        f"**Pool:** {m(macro.pool_str)}",
        f"**{target}:** {macro.difficulty}",
    ]
    if is_cofd:
        lines.append(f"**Rote:** {'Yes' if macro.rote else 'No'}")
    if macro.comment:
        lines.append(i(macro.comment))

    return "\n".join(lines)
