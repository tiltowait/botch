"""Help interface."""

import discord
from discord import slash_command
from discord.cog import Cog
from discord.commands.core import SlashCommand
from discord.ext.pages import Page, PageGroup, Paginator

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
        page_groups = []
        for cog_name, cog in sorted(self.bot.cogs.items()):
            embeds = self._generate_cog_embeds(cog)
            if embeds is None:
                continue
            page = Page(embeds=embeds)  # type: ignore
            page_groups.append(PageGroup(pages=[page], label=cog_name))

        paginator = Paginator(
            pages=page_groups,
            disable_on_timeout=True,
            show_menu=True,
            use_default_buttons=False,
        )
        await paginator.respond(ctx.interaction, ephemeral=True)

    def _generate_cog_embeds(self, cog: Cog) -> list[discord.Embed] | None:
        """Generate the embed for a cog's PageGroup. It's returned as a list of
        embeds because Page expects a list."""
        commands = [cmd for cmd in cog.walk_commands() if isinstance(cmd, SlashCommand)]
        if not commands:
            return None

        commands.sort(key=lambda c: c.qualified_name)

        entries = map(self._generate_command_entry, commands)
        embed = discord.Embed(title=cog.qualified_name, description=cog.description)
        embed.add_field(name="Commands", value="\n".join(entries))

        return [embed]

    def _generate_command_entry(self, command: SlashCommand) -> str:
        """Generates a help entry for a command."""
        cmd = self.bot.cmd_mention(command.qualified_name)
        return f"* {cmd}: {command.description}"


def setup(bot: BotchBot):
    bot.add_cog(HelpCog(bot))
