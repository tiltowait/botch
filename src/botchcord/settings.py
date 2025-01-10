"""Various settings handlers."""

import discord
from discord import ButtonStyle
from discord.ui import Button, View

from bot import AppCtx
from models import Guild, User


async def accessibility(ctx: AppCtx) -> bool:
    """Whether to use accessibility mode for the current operation."""
    guild = await ctx.bot.guild_cache.fetch(ctx.guild, create=True)
    if guild.settings.accessibility:
        return True

    user = await ctx.bot.user_store.fetch(ctx.author.id)
    return user.settings.accessibility


async def use_emojis(ctx: AppCtx) -> bool:
    """Whether to use emojis."""
    return not await accessibility(ctx)


class SettingsView(View):
    """A view responsible for presenting settings controls."""

    def __init__(self, ctx: AppCtx):
        super().__init__(disable_on_timeout=True)
        self.ctx = ctx

    @property
    def embed(self) -> discord.Embed:
        """An informational embed."""
        assert self.ctx.bot.user is not None
        name = self.ctx.bot.user.name

        return discord.Embed(
            title="Preferences",
            description=f"Use the controls below to update {name}'s settings.",
        )

    async def respond(self):
        """Populate the buttons and display the settings."""
        await self._populate_buttons()
        await self.ctx.respond(embed=self.embed, view=self, ephemeral=True)

    async def _user(self) -> User:
        """Returns the ctx's user."""
        return await self.ctx.bot.user_store.fetch(self.ctx.author.id)

    async def _guild(self) -> Guild:
        """Returns the ctx's guild."""
        return await self.ctx.bot.guild_cache.fetch(self.ctx.guild, create=True)

    @staticmethod
    def _button_style(enabled: bool) -> ButtonStyle:
        """Get the style for a button, based on the preference's state."""
        return ButtonStyle.primary if enabled else ButtonStyle.secondary

    async def _populate_buttons(self):
        """Populate the view with user and guild settings."""
        self.clear_items()

        # For a11y, we'll use "Use Emojis" instead of "Accessibility", since
        # it's more descriptive.
        user = await self._user()
        user_emojis = not user.settings.accessibility
        label = "Use Emojis (Self)"
        if not user_emojis:
            label = "Don't " + label
        user_a11y = Button(
            label=label,
            style=self._button_style(user_emojis),
            row=0,
        )
        user_a11y.callback = self.toggle_user_a11y
        self.add_item(user_a11y)

        guild = await self._guild()
        guild_emojis = not guild.settings.accessibility
        label = "Use Emojis (Server)"
        if not guild_emojis:
            label = "Don't " + label
        guild_a11y = Button(
            label=label,
            style=self._button_style(guild_emojis),
            row=1,
        )
        if self.ctx.admin_user:
            guild_a11y.callback = self.toggle_guild_a11y
        else:
            guild_a11y.disabled = True
        self.add_item(guild_a11y)

    async def toggle_user_a11y(self, interaction: discord.Interaction):
        """Toggle the user's a11y setting and refresh."""
        user = await self._user()
        user.settings.accessibility = not user.settings.accessibility
        await user.save()

        await self._populate_buttons()
        await interaction.response.edit_message(view=self)

    async def toggle_guild_a11y(self, interaction: discord.Interaction):
        """Toggle the user's a11y setting and refresh."""
        guild = await self._guild()
        guild.settings.accessibility = not guild.settings.accessibility
        await guild.save()

        await self._populate_buttons()
        await interaction.response.edit_message(view=self)
