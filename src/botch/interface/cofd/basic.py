"""Command interface for basic WoD commands."""

import discord
from discord import option
from discord.commands import slash_command

from botch import botchcord
from botch.bot import AppCtx, BotchBot
from botch.botchcord import options
from botch.config import DOCS_URL
from botch.interface import BotchCog


class BasicCog(BotchCog, name="Basic"):
    """These commands are available to any user, whether you have a character\
    or not."""

    def __init__(self, bot: BotchBot):
        self.bot = bot
        self.docs_url = f"{DOCS_URL}/reference/rolls"

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
        "advanced",
        description="Whether it is a Blessed or Blighted Action",
        choices=["Blessed", "Blighted"],
        required=False,
    )
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
        advanced: str,
        specialty: str,
        autos: int,
        comment: str,
        character: str,
        owner: discord.Member,
    ):
        """Roll the dice! If you have a character, `pool` can be traits (e.g. `Strength + Brawl`)."""
        blessed = False
        blighted = False
        if advanced == "Blessed":
            blessed = True
        elif advanced == "Blighted":
            blighted = True

        await botchcord.roll.roll(
            ctx,
            pool,
            again,
            specialty,
            use_wp,
            rote,
            comment,
            character,
            autos=autos,
            blessed=blessed,
            blighted=blighted,
            owner=owner,
        )

    @slash_command()
    async def chance(self, ctx: AppCtx):
        """Roll a chance die."""
        await botchcord.roll.chance(ctx)


def setup(bot: BotchBot):
    bot.add_cog(BasicCog(bot))
