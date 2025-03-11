"""Command interface for basic WoD commands."""

import discord
from discord import option
from discord.commands import slash_command
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options


class BasicCog(Cog, name="Basic"):
    """These commands are available to any user, whether you have a character\
    or not."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
    @option("pool", description="The dice pool. May be a number or trait + attribute equation")
    @option(
        "use_wp",
        description="Use WP on the roll. Can also add + WP to your pool",
        default=False,
    )
    @option("again", description="The number at which dice explode", choices=[10, 9, 8], default=10)
    @option("rote", description="Whether to apply the Rote quality", default=False)
    @option(
        "specialty",
        description="A specialty to apply to the roll. You may also use trait.spec syntax in pool.",
        required=False,
    )
    @option("autos", description="Add automatic successes", choices=list(range(11)), default=0)
    @option(
        "comment",
        description="A comment to show alongside the roll",
        required=False,
        max_length=300,
    )
    @options.character("[Optional] The character performing the roll")
    @options.owner()
    async def roll(
        self,
        ctx: AppCtx,
        pool: str,
        use_wp: bool,
        again: int,
        rote: bool,
        specialty: str,
        autos: int,
        comment: str,
        character: str,
        owner: discord.Member,
    ):
        """Roll the dice! If you have a character, `pool` can be traits (e.g. `Strength + Brawl`)."""
        await botchcord.roll.roll(
            ctx, pool, again, specialty, use_wp, rote, comment, character, autos=autos, owner=owner
        )

    @slash_command()
    async def chance(self, ctx: AppCtx):
        """Roll a chance die."""
        await botchcord.roll.chance(ctx)


def setup(bot: BotchBot):
    bot.add_cog(BasicCog(bot))
