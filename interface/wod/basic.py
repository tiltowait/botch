"""Command interface for basic WoD commands."""

import discord
from discord import option
from discord.commands import slash_command
from discord.ext.commands import Cog

import botchcord
from bot import BotchBot
from botchcord import options


class BasicCog(Cog, name="Basic WoD Commands"):
    """The "Basic" cog contains non-help commands usable by anyone without a
    character in the bot (though some commands have enhanced functionality if
    the user has a character)."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
    @option("pool", description="The dice pool. May be a number or trait + attribute equation")
    @options.promoted_choice("difficulty", "The roll's difficulty", start=2, end=10, first=6)
    @option(
        "specialty",
        description="A specialty to apply to the roll. You may also use trait.spec syntax in pool.",
        required=False,
    )
    @option(
        "comment",
        description="A comment to show alongside the roll",
        required=False,
        max_length=300,
    )
    async def roll(
        self,
        ctx: discord.ApplicationContext,
        pool: str,
        difficulty: int,
        specialty: str,
        comment: str,
    ):
        """Roll the dice! If you have a character, you can supply traits ("Strength + Brawl")."""
        await botchcord.roll.roll(ctx, pool, difficulty, specialty, comment)


def setup(bot: BotchBot):
    bot.add_cog(BasicCog(bot))
