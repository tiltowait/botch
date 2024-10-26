"""Miscellaneous commands."""

import random

import discord
from discord import option
from discord.commands import slash_command
from discord.ext.commands import Cog

from bot import AppCtx, BotchBot
from botchcord.utils.text import m
from config import VERSION
from core.rolls import Roll


class MiscCog(Cog, name="Miscellaneous"):
    """Miscellaneous commands that don't belong to any other sections."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
    async def info(self, ctx: AppCtx):
        """View bot information."""
        embed = discord.Embed(title="Botch", description=f"**Version:** {m(VERSION)}")
        await ctx.respond(embed=embed)

    @slash_command(name="coin")
    async def coin_flip(self, ctx: AppCtx):
        """Flip a coin."""
        coin = random.choice(["Heads", "Tails"])
        await ctx.respond(coin)

    @slash_command()
    @option("lower", description="The lowest number possible")
    @option("upper", description="The highest number possible")
    async def random(self, ctx: AppCtx, lower: int, upper: int):
        """Generate a random number between `lower` and `upper`."""
        if lower >= upper:
            await ctx.send_error("Error", "`lower` must be less than `upper`.")
        else:
            number = random.randint(lower, upper)
            await ctx.respond(f"**[{lower}, {upper}]** -> {number}")


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(MiscCog(bot))
