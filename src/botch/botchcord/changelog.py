"""Fetch and display changelog from GitHub."""

import os

import aiohttp
import discord
from discord.ext.commands import Paginator as Chunker
from discord.ext.pages import Paginator

from botch.bot import AppCtx

CHANGELOG = "https://github.com/tiltowait/botch/releases/latest"


async def show(ctx: AppCtx, hidden: bool):
    """Display Botch's changelog."""
    try:
        tag, changelog = await fetch_changelog()
        paginator = Chunker(prefix="", suffix="", max_size=4000)

        for line in changelog.split("\n"):
            paginator.add_line(line)

        embeds = []
        for page in paginator.pages:
            embed = discord.Embed(title=f"Botch {tag}", description=page, url=CHANGELOG)
            if ctx.bot.user:
                embed.set_thumbnail(url=ctx.bot.user.display_avatar)
            embeds.append(embed)

        show_buttons = len(embeds) > 1
        paginator = Paginator(
            embeds,
            author_check=False,
            show_disabled=show_buttons,
            show_indicator=show_buttons,
        )
        await paginator.respond(ctx.interaction, ephemeral=hidden)

    except (aiohttp.ClientError, KeyError) as err:
        print(err)
        await ctx.respond(
            f"Unable to fetch changelog. [Click this link to view on GitHub.]({CHANGELOG})",
            ephemeral=hidden,
        )


async def fetch_changelog() -> tuple[str, str]:
    """Fetch changelog data."""
    token = os.getenv("GITHUB_TOKEN", "")
    print(token)
    header = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    async with aiohttp.ClientSession(headers=header, raise_for_status=True) as session:
        async with session.get(
            "https://api.github.com/repos/tiltowait/botch/releases/latest"
        ) as res:
            json = await res.json()
            return json["tag_name"], json["body"]
