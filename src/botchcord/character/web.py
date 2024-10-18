"""Character web wizard command."""

import importlib.resources as resources
from pathlib import Path

import discord

import bot
import web
from config import GAME_LINE


async def wizard(ctx: bot.AppCtx, era: str):
    """Generate a link to the web wizard."""
    schema_file = get_schema_file(era)
    wizard_schema = web.models.WizardSchema.create(
        ctx.guild.name,
        ctx.guild.id,
        ctx.user.id,
        str(schema_file),
    )
    token = web.app.cache.register(wizard_schema)

    minutes = web.app.cache.ttl // 60
    embed = discord.Embed(
        title="Click here to create your character",
        description=f"This link is valid for **{minutes} minutes**.",
        url=web.app.wizard_url(token),
    )
    await ctx.respond(embed=embed, ephemeral=True)


def get_schema_file(era: str) -> str:
    trav = resources.files("core.characters.schemas")
    path = Path(trav / GAME_LINE / f"{era}.json")  # type: ignore
    return str(path)
