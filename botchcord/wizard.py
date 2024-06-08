"""Character creation wizard."""

import discord

from core.cache import cache
from core.characters import GameLine, Splat
from core.characters.factory import Factory


class Wizard(discord.ui.View):
    """The character wizard presents a self-editing message and view for
    selecting character traits. Once finished, it creates and inserts the new
    character."""

    def __init__(self, line: GameLine, splat: Splat, constructor, *, max_rating: int, **char_args):
        super().__init__(timeout=300)
        self.char_name = char_args["name"]
        self.factory = Factory(line, splat, constructor, char_args)
        self.last_trait = None
        self.bot_avatar = None

        if max_rating > 5:
            self._add_select(max_rating)
        else:
            self._add_buttons()

    def _add_select(self, max_rating: int):
        """Add the select menu from 0-max_rating."""
        select = discord.ui.Select(
            placeholder="Select the rating",
            options=[discord.SelectOption(label=str(n)) for n in range(0, max_rating + 1)],
            max_values=1,
        )
        select.callback = self.rating_selected
        self.add_item(select)

    def _add_buttons(self):
        """Add buttons 0-5."""
        for rating in range(1, 6):
            button = discord.ui.Button(label=str(rating), style=discord.ButtonStyle.primary, row=0)
            button.callback = self.rating_selected
            self.add_item(button)

        # Discord only allows 5 buttons on a row, so 0 has to be on its own
        zero_button = discord.ui.Button(label="0", row=1)
        zero_button.callback = self.rating_selected
        self.add_item(zero_button)

    async def on_timeout(self):
        """Cancel the wizard and inform the user."""
        embed = discord.Embed(
            title="Timed out",
            description="Due to inactivity, the character entry wizard has been canceled.",
        )
        await self.message.edit(embed=embed, view=None)

    def embed(self) -> discord.Embed:
        """Generate the embed for the current trait being looked at."""
        next_trait = self.factory.next_trait()
        if last_trait := self.factory.peek_last():
            description = f"Just assigned: {last_trait[0]} = {last_trait[1]}"
        else:
            description = "This wizard will guide you through the character entry process."

        embed = discord.Embed(
            title=f"Select rating: {next_trait}",
            description=description,
        )
        embed.set_author(name=f"Creating {self.char_name}", icon_url=self.bot_avatar)
        embed.set_footer(
            text=(
                "Your character will not be saved until you finish selecting traits.\n"
                f"{self.factory.remaining} remaining."
            )
        )

        return embed

    async def rating_selected(self, interaction: discord.Interaction):
        """Apply the rating to the current trait, then prompt for the next one."""
        if values := interaction.data.get("values"):
            rating = int(values[0])
        else:
            for child in self.children:
                if child.custom_id == interaction.custom_id:
                    rating = int(child.label)
                    break

        # Got the rating
        self.factory.assign_next(rating)
        if self.factory.next_trait():
            await interaction.response.edit_message(embed=self.embed())
        else:
            await self.finalize(interaction)

    async def finalize(self, interaction: discord.Interaction):
        """Create the character and display next steps."""
        character = self.factory.create()
        embed = discord.Embed(
            title="Finished!",
            description=f"Character entry is finished. You may now use {character.name} in rolls.",
        )
        embed.set_author(name=f"Creating {character.name}", icon_url=self.bot_avatar)

        await interaction.response.edit_message(embed=embed, view=None)
        await cache.register(character)

    async def start(self, interaction: discord.Interaction):
        """Start the wizard."""
        self.bot_avatar = interaction.client.user.display_avatar
        await interaction.response.send_message(embed=self.embed(), view=self, ephemeral=True)
