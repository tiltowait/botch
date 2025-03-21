"""interface/loggingcog.py - Log command events."""

import logging

import discord
from discord.ext import commands

from bot import BotchBot
from interface.models import CommandRecord
from interface import BotchCog


class LoggingCog(BotchCog):
    """A simple cog for logging command events."""

    logger = logging.getLogger("COMMAND")

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        """Log command usage."""
        location = "DMs"
        if ctx.guild is not None:
            location = ctx.guild.name

        if selected_options := ctx.selected_options:
            options = []
            for option in selected_options:
                name = option["name"]
                value = option["value"]
                if isinstance(value, str):
                    options.append(f'{name}="{value}"')
                else:
                    options.append(f"{name}={value}")
        else:
            options = ["None"]

        self.logger.info(
            "`/%s` invoked by @%s (%s) in %s (%s). Options: %s",
            ctx.command.qualified_name,
            ctx.user.name,
            ctx.user.id,
            location,
            ctx.guild_id,
            ", ".join(options),
        )

        record = CommandRecord.from_context(ctx)
        await record.save()


def setup(bot: BotchBot):
    """Add the cog to the bot."""
    bot.add_cog(LoggingCog(bot))
