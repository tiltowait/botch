"""Character deletion command."""

import discord

from botch import bot, core
from botch.botchcord.haven import haven
from botch.core.characters import Character


@haven()
async def delete(ctx: bot.AppCtx, character: Character):
    """Present a modal for character deletion."""
    modal = DeletionModal(character.name)
    await ctx.send_modal(modal)
    await modal.wait()

    if modal.should_delete:
        await core.cache.remove(character)
        await modal.interaction.respond(f"**{character.name}** deleted!")  # type: ignore
    else:
        await ctx.send_error(
            "Error",
            "You must type your character's name exactly to delete.",
            interaction=modal.interaction,
        )


class DeletionModal(discord.ui.Modal):
    """A modal that requires the user to type their character's name."""

    def __init__(self, char_name: str, *args, **kwargs):
        super().__init__(title=f"Delete {char_name}?", *args, **kwargs)
        self.should_delete = False
        self.expected = char_name.casefold()
        self.interaction: discord.Interaction | None = None

        self.add_item(
            discord.ui.InputText(
                label="Enter character name to delete",
                placeholder=char_name,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.should_delete = self.children[0].value.casefold() == self.expected  # type: ignore
