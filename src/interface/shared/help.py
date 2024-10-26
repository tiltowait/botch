"""Help interface."""

import discord
from discord import slash_command
from discord.commands.core import SlashCommand
from discord.ext.commands import Cog

from bot import AppCtx, BotchBot


class HelpCog(Cog, name="Help"):
    """These help menus are generated dynamically, and I thought it was funny\
    not to filter out this section, so here it is. There's nothing helpful on\
    this page. Move along!"""

    def __init__(self, bot: BotchBot):
        self.bot = bot

    @slash_command(name="help")
    async def help_command(self, ctx: AppCtx):
        """View command help. It's ... what you're looking at right now."""
        cog = self.bot.get_cog("Macros")
        assert cog is not None
        commands = [cmd for cmd in cog.walk_commands() if isinstance(cmd, SlashCommand)]
        commands.sort(key=lambda c: c.qualified_name)

        entries = map(self._generate_command_entry, commands)
        embed = discord.Embed(title=cog.qualified_name, description=cog.description)
        embed.add_field(name="Commands", value="\n".join(entries))

        await ctx.respond(embed=embed, ephemeral=True)

    def _generate_command_entry(self, command: SlashCommand) -> str:
        """Generates a help entry for a command."""
        cmd = self.bot.cmd_mention(command.qualified_name)
        return f"* {cmd}: {command.description}"


def setup(bot: BotchBot):
    bot.add_cog(HelpCog(bot))
