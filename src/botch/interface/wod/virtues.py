"""WoD Virtue commands."""

import discord
from discord import SlashCommandGroup, option

from botch.bot import AppCtx, BotchBot
from botch.botchcord import options
from botch.botchcord.character import virtues
from botch.config import DOCS_URL
from botch.interface import BotchCog


class VirtuesCog(BotchCog, name="Virtues"):
    """Commands for setting and updating character Virtues."""

    virtues = SlashCommandGroup(
        "virtues",
        "Virtue commands",
        contexts={discord.InteractionContextType.guild},
    )

    def __init__(self, bot: BotchBot):
        self.bot = bot
        self.docs_url = f"{DOCS_URL}/reference/virtues"

    @virtues.command(name="set")
    @option(
        "virtue",
        description="The Virtue to set or change to",
        choices=["Conscience", "Conviction", "SelfControl", "Instinct", "Courage"],
    )
    @option("rating", description="The rating to give the Virtue", choices=list(range(6)))
    @options.character("The character to update")
    async def virtues_set(self, ctx: AppCtx, virtue: str, rating: int, character: str):
        """Update a Virtue's rating. You can also use this to change Virtues."""
        await virtues.update(ctx, character, virtue, rating)


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(VirtuesCog(bot))
