"""Character adjustment menus."""

from abc import ABC, abstractmethod
from collections import Counter

import discord
from discord import ButtonStyle
from discord.ui import Button, Select, View

import bot
import botchcord.settings
from botchcord.character.display import DisplayField, build_embed
from botchcord.haven import haven
from core.characters import Character, Damage, Tracker
from core.characters.wod import Vampire

__all__ = (
    "Adjuster",
    "BloodAdjuster",
    "GroundingAdjuster",
    "HealthAdjuster",
    "Toggler",
    "WillpowerAdjuster",
)


@haven()
async def adjust(ctx: bot.AppCtx, character: Character):
    """Present the adjuster views."""
    toggler = Toggler(ctx, character)
    await toggler.display()


class Toggler(View):
    """A view that toggles between subviews."""

    def __init__(self, ctx: bot.AppCtx, char: Character):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.character = char
        self.adjusters: list["Adjuster"] = []

        self.selector = Select(placeholder="Select a stat to adjust")
        self.selector.callback = self.select_adjuster
        self.add_item(self.selector)

        self.add_adjuster("Adjust: Health", HealthAdjuster)
        self.add_adjuster("Adjust: Willpower", WillpowerAdjuster)
        self.add_adjuster(f"Adjust: {char.grounding.path}", GroundingAdjuster)

        if self.character.has_blood_pool:
            self.add_adjuster("Adjust: Blood Pool", BloodAdjuster)

    def _populate_menu(self, adjuster: "Adjuster"):
        """Populate the menu."""
        for btn in self.children[1:]:
            self.remove_item(btn)
        for btn in adjuster.buttons:
            self.add_item(btn)

    async def select_adjuster(self, interaction: discord.Interaction):
        """Select the indicated subview."""
        selected = self.selector.values[0]
        idx = next(i for i, o in enumerate(self.selector.options) if o.label == selected)
        new_adjuster = self.adjusters[idx]
        self._populate_menu(new_adjuster)

        # Mark the correct one as selected
        for opt in self.selector.options:
            opt.default = opt.label == selected

        await interaction.response.edit_message(view=self)

    def add_adjuster(self, label: str, adjuster_cls: type["Adjuster"]):
        """Add a subview behind a select menu option."""
        adjuster = adjuster_cls(self, self.character)
        if not self.adjusters:
            self._populate_menu(adjuster)
            default = True
        else:
            default = False

        self.adjusters.append(adjuster)
        self.selector.add_option(label=label, default=default)

    async def update(self, interaction: discord.Interaction):
        """Update the character display and the view."""
        use_emojis = await botchcord.settings.use_emojis(self.ctx)
        await self.ctx.edit(embed=self._embed(use_emojis))
        await interaction.response.edit_message(view=self)
        await self.character.save()

    async def display(self):
        """Display the character stats adjuster."""
        use_emojis = await botchcord.settings.use_emojis(self.ctx)
        await self.ctx.respond(embed=self._embed(use_emojis))
        await self.ctx.respond(view=self, ephemeral=True)

    def _embed(self, use_emojis: bool) -> discord.Embed:
        """The character display embed."""
        fields = [
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
        ]
        if self.character.has_blood_pool:
            fields.append(DisplayField.BLOOD_POOL)
        return build_embed(self.ctx.bot, self.character, use_emojis, fields=tuple(fields))

    async def on_timeout(self):
        """Remove the controls and prompt user to run the command again."""
        cmd = self.ctx.bot.cmd_mention("character adjust")
        if self.message is not None:
            await self.message.edit(
                content=f"Adjustments timed out. Please run {cmd} again.",
                view=None,
            )


class Adjuster(ABC):
    """Base class for adjuster "subviews"."""

    def __init__(self, container: Toggler, char: Character):
        self.container = container
        self.character = char
        self.buttons: list[Button] = []
        self._populate()
        self._update_buttons()

    @abstractmethod
    def _populate(self):
        """Override to populate the view."""

    def add_item(self, btn: Button):
        """Add a button."""
        self.buttons.append(btn)

    def add_row(
        self,
        row: int,
        label: str,
        dec_color=ButtonStyle.success,
        inc_color=ButtonStyle.danger,
    ):
        """Adds an adjuster row."""
        btn = Button(emoji="➖", style=dec_color, row=row)
        btn.callback = self.callback
        self.add_item(btn)
        btn = Button(label=label, style=ButtonStyle.secondary, row=row, disabled=True)
        btn.callback = self.callback
        self.add_item(btn)
        btn = Button(emoji="➕", style=inc_color, row=row)
        btn.callback = self.callback
        self.add_item(btn)

    def get_button(self, custom_id: str | None) -> tuple[int, Button]:
        """Get a button by ID."""
        for i, btn in enumerate(self.buttons):
            if btn.custom_id == custom_id:
                return i, btn
        raise ValueError(f"No button with ID {custom_id}")

    def _update_buttons(self):
        pass

    @abstractmethod
    async def callback(self, interaction: discord.Interaction):
        """Perform the adjustment and inform the container."""
        self._update_buttons()
        await self.container.update(interaction)


class HealthAdjuster(Adjuster):
    """Adjust character health."""

    def _populate(self):
        for i, label in enumerate(["Bashing", "Lethal", "Aggravated"]):
            self.add_row(i + 1, label)

    def _update_buttons(self):
        c = Counter(list(self.character.health))

        # Bashing: 0, 2
        self.buttons[0].disabled = c[Damage.BASHING] == 0
        self.buttons[2].disabled = c[Damage.NONE] == 0

        # Lethal: 3, 5
        self.buttons[3].disabled = c[Damage.LETHAL] == 0
        self.buttons[5].disabled = (c[Damage.NONE] + c[Damage.BASHING]) == 0

        # Aggravated: 6, 8
        self.buttons[6].disabled = c[Damage.AGGRAVATED] == 0
        self.buttons[8].disabled = (c[Damage.NONE] + c[Damage.BASHING] + c[Damage.LETHAL]) == 0

    async def callback(self, interaction: discord.Interaction):
        i, btn = self.get_button(interaction.custom_id)
        match btn.row:
            case 1:
                severity = Damage.BASHING
            case 2:
                severity = Damage.LETHAL
            case 3:
                severity = Damage.AGGRAVATED
            case _:
                raise ValueError("Health adjuster: Unexpected row")

        # Buttons are in a grid, with the left column being decrement
        # and the right being increment
        if i in (0, 3, 6):
            self.character.decrement_damage(Tracker.HEALTH, severity)
        else:
            self.character.increment_damage(Tracker.HEALTH, severity)

        await super().callback(interaction)


class WillpowerAdjuster(Adjuster):
    """Adjust character willpower."""

    def _populate(self):
        self.add_row(1, "Temporary")
        self.add_row(2, "Permanent")

    def _update_buttons(self):
        c = Counter(list(self.character.willpower))

        self.buttons[0].disabled = c[Damage.BASHING] == 0
        self.buttons[2].disabled = c[Damage.NONE] == 0
        self.buttons[3].disabled = len(self.character.willpower) <= 1
        self.buttons[5].disabled = len(self.character.willpower) >= 10

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)
        match i:
            # Temporary willpower
            case 0:
                self.character.decrement_damage(Tracker.WILLPOWER, Damage.BASHING)
            case 2:
                self.character.increment_damage(Tracker.WILLPOWER, Damage.BASHING)
            # Permanent willpower
            case 3:
                self.character.willpower = self.character.willpower[1:]
            case 5:
                self.character.willpower = Damage.NONE + self.character.willpower

        await super().callback(interaction)


class GroundingAdjuster(Adjuster):
    """Adjust character grounding (path/humanity)."""

    def _populate(self):
        self.add_row(1, self.character.grounding.path)
        for btn in self.buttons:
            btn.callback = self.callback

    def _update_buttons(self):
        self.buttons[0].disabled = self.character.grounding.rating == 0
        self.buttons[2].disabled = self.character.grounding.rating == 10

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)
        if i == 0:
            self.character.grounding.decrement()
        else:
            self.character.grounding.increment()

        await super().callback(interaction)


class BloodAdjuster(Adjuster):
    """Adjust character blood pool. This might be expandable to adjusting
    special attributes--BP, Rage, Pillars, etc."""

    character: Vampire

    def _populate(self):
        self.add_row(1, "Blood Pool", dec_color=ButtonStyle.danger, inc_color=ButtonStyle.success)

    def _update_buttons(self):
        self.buttons[0].disabled = self.character.blood_pool == 0
        self.buttons[2].disabled = self.character.blood_pool == self.character.max_bp

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)

        if i == 0:
            self.character.reduce_blood(1)
        else:
            self.character.add_blood(1)

        await super().callback(interaction)
