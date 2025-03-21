import discord
from discord.ext import commands

from botch.config import DOCS_URL


class BotchCog(commands.Cog):
    docs_url = DOCS_URL

    @property
    def documentation_view(self):
        """Return a view with a documentation link button."""
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link, label="Documentation", url=self.docs_url
            )
        )
        return view
