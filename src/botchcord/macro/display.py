"""Macro display functions and command implementation.

Macros are displayed inside paginated embeds. Each macro is made into its
own "entry", which is how we avoid them being split across pages."""

from discord.ext.commands import Paginator as Chunker
from discord.ext.pages import Paginator

import bot
from botchcord.haven import haven
from botchcord.utils import CEmbed
from botchcord.utils.text import b, i, m
from core.characters import Character, Macro


@haven(filter=lambda c: len(c.macros) > 0)
async def display(ctx: bot.AppCtx, character: Character):
    """Display the macros paginator."""
    paginator = create_paginator(ctx.bot, character)
    await paginator.respond(ctx.interaction, ephemeral=True)


def create_paginator(bot: bot.BotchBot, char: Character) -> Paginator:
    """Create the macro paginator."""
    embeds = []
    for page in paginate_macros(char.macros):
        embed = CEmbed(bot, char, title="Macros", description=page)
        embeds.append(embed)

    return Paginator(embeds)


def paginate_macros(macros: list[Macro]) -> list[str]:
    """Paginate the macro entries."""
    chunker = Chunker(prefix=None, suffix=None)
    for entry in map(create_macro_entry, macros):
        chunker.add_line(entry)

    return chunker.pages


def create_macro_entry(macro: Macro) -> str:
    """Create a macro display entry."""
    lines = [
        f"### {macro.name}",
        f"**Pool:** {m(macro.pool_str)}",
        f"**Difficulty:** {macro.difficulty}",
    ]
    if macro.comment:
        lines.append(i(macro.comment))

    return "\n".join(lines)
