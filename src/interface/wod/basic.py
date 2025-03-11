"""Command interface for basic WoD commands."""

import discord
from discord import InteractionContextType, option
from discord.commands import slash_command
from discord.ext.commands import Cog

import botchcord
from bot import AppCtx, BotchBot
from botchcord import options
from core.rolls import Roll


class BasicCog(Cog, name="Basic"):
    """These commands are available to any user, whether you have a character\
    or not."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
    @option("pool", description="The dice pool. May be a number or trait + attribute equation")
    @options.promoted_choice("difficulty", "The roll's difficulty", start=2, end=10, first=6)
    @option(
        "use_wp",
        description="Use WP on the roll. Can also add + WP to your pool",
        default=False,
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
        difficulty: int,
        use_wp: bool,
        specialty: str,
        autos: int,
        comment: str,
        character: str,
        owner: discord.Member,
    ):
        """Roll the dice! If you have a character, `pool` can be traits (e.g. `Strength + Brawl`)."""
        await botchcord.roll.roll(
            ctx,
            pool,
            difficulty,
            specialty,
            use_wp,
            False,
            comment,
            character,
            autos=autos,
            owner=owner,
        )

    @slash_command(contexts={InteractionContextType.guild})
    async def botches(self, ctx: AppCtx):
        """How many botches have you rolled?"""
        rolls = await Roll.find(dict(guild=ctx.guild.id, user=ctx.user.id, botched=True)).to_list()
        count = len(rolls)

        if count == 1:
            await ctx.respond(f"You've got **{count}** botch on this server 😆")
        elif count > 1:
            await ctx.respond(f"You've got **{count}** botches on this server 🤣🤣🤣")
        else:
            await ctx.respond("You haven't botched here yet. Good job, I guess 😔")


def setup(bot: BotchBot):
    bot.add_cog(BasicCog(bot))
