from discord.commands import slash_command
from discord.ext.commands import Cog

from bot import AppCtx, BotchBot
from core.rolls import Roll


class MiscCog(Cog, name="Miscellaneous commands"):
    """A motley collection of shared commands that don't belong anywhere else."""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command()
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
    """Add the cog to the bot."""
    bot.add_cog(MiscCog(bot))
