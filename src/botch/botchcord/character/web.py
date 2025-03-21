"""Character web wizard command."""

import importlib.resources as resources
from datetime import timedelta
from pathlib import Path

import discord
from discord.utils import format_dt, utcnow

from botch import bot, web
from botch.config import GAME_LINE


async def wizard(ctx: bot.AppCtx, era: str):
    """Generate a link to the web wizard."""
    schema_file = get_schema_file(era)
    wizard_schema = web.models.WizardSchema.create(ctx.guild, ctx.user.id, str(schema_file))
    token = web.app.cache.register(wizard_schema)

    delta = utcnow() + timedelta(seconds=web.app.cache.ttl)
    expiration = format_dt(delta, "R")

    embed = discord.Embed(
        title="Click here to create your character",
        description=f"**Link expiration:** {expiration}.",
        url=web.app.wizard_url(token),
    )
    await ctx.respond(embed=embed, ephemeral=True)


def get_schema_file(era: str) -> str:
    trav = resources.files("botch.core.characters.schemas")
    path = Path(trav / GAME_LINE / f"{era}.json")  # type: ignore
    return str(path)
