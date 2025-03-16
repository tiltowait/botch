"""Miscellaneous commands."""

import random

import discord
from discord import option
from discord.commands import slash_command
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord.utils.text import m
from config import VERSION, DOCS_URL
from src.interface import BotchCog

# Create a subclass of discord.ui.View for the documentation link
class DocumentationView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__()
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link,
            label="Documentation",
            url=url
        ))

class MiscCog(BotchCog, Cog, name="Miscellaneous"):
    """Miscellaneous commands that don't belong to any other sections."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
    async def info(self, ctx: AppCtx):
        """View bot information."""
        assert ctx.bot.user is not None
        embed = discord.Embed(title=ctx.bot.user.name, description=f"**Build:** {m(VERSION)}")

        # Create an instance of our View subclass
        view = DocumentationView(DOCS_URL)

        await ctx.respond(embed=embed, view=view)

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

    @slash_command()
    async def preferences(self, ctx: AppCtx):
        """View and edit bot preferences."""
        view = botchcord.settings.SettingsView(ctx)
        await view.respond()

    @slash_command()
    @option(
        "hidden", description="Make the changelog visible only to you (default true).", default=True
    )
    async def changelog(self, ctx: AppCtx, hidden: bool):
        """Show the latest changelog."""
        await botchcord.changelog.show(ctx, hidden)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(MiscCog(bot))
