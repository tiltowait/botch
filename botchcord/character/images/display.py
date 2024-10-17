"""Full-size character image display."""

import logging

import discord
from discord.ui import Button

import api
from bot import AppCtx
from botchcord.haven import haven
from botchcord.utils import CEmbed
from core.characters import Character

logger = logging.getLogger("IMAGES")


def _has_image(character: Character) -> bool:
    """Raises an error if the character doesn't have an image."""
    return len(character.profile.images) > 0


@haven(filter=_has_image)
async def display_images(
    ctx: AppCtx,
    character: Character,
    invoker_controls: bool,
):
    """Display a character's images inside a paginator.

    Args:
        ctx: The command context
        character: The character being displayed
        invoker_controls: Whether only the invoking user can control the buttons"""
    pager = ImagePager(ctx, character, invoker_controls)
    await pager.respond()


class ImagePager(discord.ui.View):
    """
    A display that pages through character images. It features two modes: view
    and manage. In management mode, the character's owner may delete or promote
    images. Management mode is only available if the initiating user is the
    character's owner.
    """

    first_button: Button
    prev_button: Button
    indicator: Button
    next_button: Button
    last_button: Button
    manage_button: Button
    delete_button: Button
    promote_button: Button
    demote_button: Button
    cancel_button: Button

    def __init__(
        self,
        ctx: AppCtx,
        character: Character,
        invoker_controls: bool,
    ):
        self.ctx = ctx
        self.character = character
        self.invoker_controls = invoker_controls
        self.current_page = 0
        self.management_mode = False

        # Standard paging buttons
        self.first_button = Button(
            label="<<",
            style=discord.ButtonStyle.primary,
            disabled=True,
            row=0,
        )
        self.first_button.callback = self.first_page
        self.prev_button = Button(
            label="<",
            style=discord.ButtonStyle.danger,
            row=0,
        )
        self.prev_button.callback = self.previous_page
        self.indicator = Button(
            label=self.indicator_label,
            disabled=True,
            row=0,
        )
        self.next_button = Button(
            label=">",
            style=discord.ButtonStyle.success,
            row=0,
        )
        self.next_button.callback = self.next_page
        self.last_button = Button(
            label=">>",
            style=discord.ButtonStyle.primary,
            row=0,
        )
        self.last_button.callback = self.last_page

        self.manage_button = Button(label="Manage", row=1)
        self.manage_button.callback = self.mode_toggle

        # Management mode buttons
        self.delete_button = Button(
            label="Delete",
            style=discord.ButtonStyle.danger,
            row=0,
        )
        self.delete_button.callback = self._delete_image
        self.promote_button = Button(
            label="Make First",
            style=discord.ButtonStyle.primary,
            disabled=True,
            row=0,
        )
        self.promote_button.callback = self._promote_image
        self.demote_button = Button(
            label="Make Last",
            style=discord.ButtonStyle.primary,
            disabled=self.num_pages == 1,
            row=0,
        )
        self.demote_button.callback = self._demote_image
        self.cancel_button = Button(label="Done", row=1)
        self.cancel_button.callback = self.mode_toggle

        super().__init__(timeout=300)
        self.add_pager_buttons()

    @property
    def num_pages(self) -> int:
        """The number of pages in the view."""
        return len(self.character.profile.images)

    @property
    def indicator_label(self) -> str:
        """The label for the page indicator."""
        return f"{self.current_page + 1}/{self.num_pages}"

    @property
    def current_image(self) -> str:
        """The URL of the current image."""
        return str(self.character.profile.images[self.current_page])

    @property
    def embed(self) -> CEmbed:
        """The embed for the current image."""
        embed = CEmbed(self.ctx.bot, self.character, show_thumbnail=False)
        embed.set_footer(text="Upload images with /character image upload.")
        embed.set_image(url=self.current_image)

        return embed

    def add_pager_buttons(self):
        """Add the pager buttons."""
        if self.num_pages > 1:
            self.add_item(self.first_button)
            self.add_item(self.prev_button)
            self.add_item(self.indicator)
            self.add_item(self.next_button)
            self.add_item(self.last_button)

        if self.character.user == self.ctx.user.id:
            self.add_item(self.manage_button)

    async def respond(self):
        """Display the pager."""
        self.message = await self.ctx.respond(embed=self.embed, view=self)

    async def previous_page(self, interaction: discord.Interaction):
        """Go to the next page."""
        if self.current_page == 0:
            await self.goto_page(self.num_pages - 1, interaction)
        else:
            await self.goto_page(self.current_page - 1, interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Go to the next page."""
        if self.current_page >= self.num_pages - 1:
            await self.goto_page(0, interaction)
        else:
            await self.goto_page(self.current_page + 1, interaction)

    async def first_page(self, interaction: discord.Interaction):
        """Go to the first page."""
        await self.goto_page(0, interaction)

    async def last_page(self, interaction: discord.Interaction):
        """Go to the last page."""
        await self.goto_page(self.num_pages - 1, interaction)

    async def goto_page(self, page_number: int, interaction: discord.Interaction):
        """Go to a specific page number."""
        if not self.num_pages:
            await self._display_no_images(interaction)
            return

        self.current_page = page_number
        self.indicator.label = self.indicator_label

        self.first_button.disabled = self.current_page == 0
        self.last_button.disabled = self.current_page == self.num_pages - 1
        self.promote_button.disabled = self.current_page == 0
        self.demote_button.disabled = self.current_page == self.num_pages - 1

        assert interaction.message is not None
        embed = interaction.message.embeds[0]
        embed.set_image(url=self.current_image)
        await interaction.response.edit_message(embed=embed, view=self)

    async def _display_no_images(self, interaction: discord.Interaction):
        """Inform the character has no images if the last image is deleted."""
        embed = CEmbed(
            self.ctx.bot,
            self.character,
            title="No Images",
            description=f"**{self.character.name}** has no images!",
            show_thumbnail=False,
        )
        embed.set_footer(text="Upload images with /character image upload.")

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    async def mode_toggle(self, interaction: discord.Interaction | None):
        """Toggle between management and normal modes."""
        self.clear_items()

        if self.management_mode:
            self.add_pager_buttons()
        else:
            self.add_item(self.promote_button)
            self.add_item(self.demote_button)
            self.add_item(self.delete_button)
            self.add_item(self.cancel_button)

        self.management_mode = not self.management_mode

        if interaction is not None:
            await interaction.response.edit_message(view=self)

    # Image manipulation

    async def _promote_image(self, interaction: discord.Interaction):
        """Promote the current image to the first position."""
        url = self.character.profile.images.pop(self.current_page)
        self.character.profile.images.insert(0, url)

        await self.mode_toggle(None)  # No point in showing management buttons
        await self.goto_page(0, interaction)
        await self.character.save()

    async def _demote_image(self, interaction: discord.Interaction):
        """Demote the current image to the last position."""
        url = self.character.profile.images.pop(self.current_page)
        self.character.profile.images.append(url)

        await self.mode_toggle(None)  # No point in showing management buttons
        await self.goto_page(self.num_pages - 1, interaction)
        await self.character.save()

    async def _delete_image(self, interaction: discord.Interaction):
        """Delete the current image."""
        image_url = self.character.profile.images.pop(self.current_page)
        logger.info("Removing %s from %s", image_url, self.character.name)

        if self.num_pages == 0:
            logger.debug("Deleted %s's last image", self.character.name)
            await self._display_no_images(interaction)
        else:
            page = min(self.current_page, self.num_pages - 1)
            await self.goto_page(page, interaction)

        if await api.delete_single_faceclaim(str(image_url)):
            await self.character.save()

    async def interaction_check(self, interaction: discord.Interaction):
        """Ensure image management safety."""
        assert interaction.user is not None
        if self.management_mode or self.manage_button.custom_id == interaction.custom_id:
            # Only the character's owner may access management mode.
            if interaction.user.id != self.character.user:
                await interaction.respond(
                    "You may only manage your own characters' images.", ephemeral=True
                )
                return False
        if self.invoker_controls and interaction.user.id != self.ctx.user.id:
            # Prevent others from using buttons if the option was set
            await interaction.respond(
                f"Only {self.ctx.user.mention} can click this button.", ephemeral=True
            )
            return False

        # Default case: Everyone can use pager buttons
        return True

    async def on_timeout(self):
        """Delete the components."""
        if self.children:
            logger.debug("View timed out; deleting components")
            if self.message is not None:
                await self.message.edit(view=None)
        else:
            logger.debug("View timed out, but no components")
