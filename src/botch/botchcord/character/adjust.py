"""Character adjustment menus."""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

import discord
from discord import ButtonStyle
from discord.ui import Button, Select, View

from botch import bot
from botch.botchcord import settings
from botch.botchcord.character.display import DisplayField, build_embed
from botch.botchcord.haven import haven
from botch.core.characters import Character, Damage, GameLine, Tracker, cofd, wod
from botch.utils import normalize_text

__all__ = (
    "Adjuster",
    "GroundingAdjuster",
    "HealthAdjuster",
    "MummyPillarAdjuster",
    "MummySekhemAdjuster",
    "Toggler",
    "WillpowerAdjuster",
    "VampAdjuster",
)

VampireType = wod.Vampire | cofd.Vampire


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
        self.display_msg: discord.WebhookMessage | discord.Interaction | None = None

        self.selector: Select = Select(placeholder="Select a stat to adjust")
        self.selector.callback = self.select_adjuster
        self.add_item(self.selector)

        self.add_adjuster("Adjust: Health", HealthAdjuster)
        self.add_adjuster("Adjust: Willpower", WillpowerAdjuster)
        self.add_adjuster(f"Adjust: {char.grounding.path}", GroundingAdjuster)

        if isinstance(char, VampireType):
            self.add_adjuster("Adjust: Vampirism", VampAdjuster)
        elif isinstance(char, cofd.Mummy):
            self.add_adjuster("Adjust: Sekhem", MummySekhemAdjuster)
            p = cofd.Mummy.Pillars
            self.add_adjuster("Adjust: Ab, Ba", MummyPillarAdjuster, p.AB, p.BA)
            self.add_adjuster("Adjust: Ka, Ren", MummyPillarAdjuster, p.KA, p.REN)
            self.add_adjuster("Adjust: Sheut", MummyPillarAdjuster, p.SHEUT)

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

    def update_grounding_selector_name(self):
        """Updates the name of the Grounding selector."""
        self.selector.options[2].label = f"Adjust: {self.character.grounding.path}"

    def add_adjuster(self, label: str, adjuster_cls: type["Adjuster"], *args: Any, **kwargs: Any):
        """Add a subview behind a select menu option."""
        adjuster = adjuster_cls(self, self.character, *args, **kwargs)
        if not self.adjusters:
            self._populate_menu(adjuster)
            default = True
        else:
            default = False

        self.adjusters.append(adjuster)
        self.selector.add_option(label=label, default=default)

    async def update_display(self):
        """Updates the displayed stats."""
        if self.display_msg is not None:
            use_emojis = await settings.use_emojis(self.ctx)
            await self.display_msg.edit(embed=self._embed(use_emojis))

    async def update(self, interaction: discord.Interaction):
        """Update the character display and the view."""
        await self.update_display()
        await interaction.response.edit_message(view=self)
        await self.character.save()

    async def display(self):
        """Display the character stats adjuster."""
        use_emojis = await settings.use_emojis(self.ctx)

        # If the user used the character selector, then we can't make use of
        # Interaction.edit(), because the message containing the display
        # embed is a WebhookMessage. Luckily, both it and Interaction have
        # an edit(), so we just have to store the response from ctx.respond()
        # and call edit() on it whenever we need to update.
        self.display_msg = await self.ctx.respond(embed=self._embed(use_emojis))
        await self.ctx.respond(view=self, ephemeral=True)

    def _embed(self, use_emojis: bool) -> discord.Embed:
        """The character display embed."""
        fields = [
            DisplayField.HEALTH,
            DisplayField.WILLPOWER,
            DisplayField.GROUNDING,
        ]
        if isinstance(self.character, wod.Vampire):
            fields.append(DisplayField.BLOOD_POOL)
            fields.append(DisplayField.GENERATION)
        elif isinstance(self.character, cofd.Vampire):
            fields.append(DisplayField.VITAE)
            fields.append(DisplayField.BLOOD_POTENCY)
        return build_embed(self.ctx.bot, self.character, use_emojis, fields=tuple(fields))

    async def on_timeout(self):
        """Remove the controls and prompt user to run the command again."""
        cmd = self.ctx.bot.cmd_mention("character adjust")
        if self.message is not None:
            try:
                await self.message.edit(
                    content=f"Adjustments timed out. Please run {cmd} again.",
                    view=None,
                )
            except (discord.Forbidden, discord.NotFound):
                # The message was deleted
                pass


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

    def add_stepper(
        self,
        row: int,
        label: str,
        dec_color=ButtonStyle.success,
        inc_color=ButtonStyle.danger,
    ):
        """Adds an adjuster row."""
        btn: Button = Button(emoji="➖", style=dec_color, row=row)
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

    @abstractmethod
    def _update_buttons(self):
        """Update button states."""

    @abstractmethod
    async def callback(self, interaction: discord.Interaction):
        """Perform the adjustment and inform the container."""
        self._update_buttons()
        await self.container.update(interaction)


class HealthAdjuster(Adjuster):
    """Adjust character health."""

    def _populate(self):
        for i, label in enumerate(["Bashing", "Lethal", "Aggravated"]):
            self.add_stepper(i + 1, label)

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
        self.add_stepper(1, "Temporary")
        self.add_stepper(
            2, "Permanent", dec_color=ButtonStyle.danger, inc_color=ButtonStyle.success
        )

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
                if len(self.character.willpower) > 1:
                    self.character.willpower = self.character.willpower[1:]
            case 5:
                if len(self.character.willpower) < 10:
                    self.character.willpower = Damage.NONE + self.character.willpower

        await super().callback(interaction)


class GroundingAdjuster(Adjuster):
    """Adjust character grounding (path/humanity)."""

    def __init__(self, container: Toggler, char: Character):
        self.allow_path_change = char.line == GameLine.WOD
        super().__init__(container, char)

    def _populate(self):
        self.add_stepper(
            1,
            self.character.grounding.path,
            dec_color=ButtonStyle.danger,
            inc_color=ButtonStyle.success,
        )
        for btn in self.buttons:
            btn.callback = self.callback

        if self.allow_path_change:
            button = Button(label="Change Path", style=ButtonStyle.primary, row=2)
            button.callback = self.change_path
            self.add_item(button)

    def _update_buttons(self):
        self.buttons[0].disabled = self.character.grounding.rating == 0
        self.buttons[2].disabled = self.character.grounding.rating == 10
        self.buttons[1].label = self.character.grounding.path

    async def change_path(self, interaction: discord.Interaction):
        """Present a modal to change the character's Path."""
        modal = PathModal(self.character.name, self.character.grounding.path)
        await interaction.response.send_modal(modal)
        await modal.wait()

        if modal.new_path:
            self.character.grounding.path = modal.new_path
            if modal.interaction:
                self.container.update_grounding_selector_name()
                await super().callback(modal.interaction)

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)
        if i == 0:
            self.character.grounding.decrement()
        else:
            self.character.grounding.increment()

        await super().callback(interaction)


class PathModal(discord.ui.Modal):
    """A modal for changing a character's Path."""

    def __init__(self, char_name: str, current_path: str, *args, **kwargs):
        super().__init__(title=f"Change {char_name}'s Path", *args, **kwargs)
        self.current_path = current_path
        self.interaction: discord.Interaction | None = None
        self.new_path = current_path

        self.add_item(
            discord.ui.InputText(
                label="New Path",
                placeholder=current_path,
                min_length=1,
                max_length=30,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        self.interaction = interaction
        if user_input := self.children[0].value:
            normalized = normalize_text(user_input)
            if normalized:
                self.new_path = normalized


class VampAdjuster(Adjuster):
    """Adjust character blood pool. This might be expandable to adjusting
    special attributes--BP, Rage, Pillars, etc."""

    character: VampireType

    @property
    def is_cofd(self) -> bool:
        return self.character.line == GameLine.COFD

    def _populate(self):
        colors = dict(dec_color=ButtonStyle.danger, inc_color=ButtonStyle.success)
        if self.is_cofd:
            current_blood = "Vitae"
            max_blood = "Max Vitae"
            potency = "Blood Potency"
        else:
            current_blood = "Blood Pool"
            max_blood = "Max Blood Pool"
            potency = "Generation"

        self.add_stepper(1, current_blood, **colors)
        self.add_stepper(2, max_blood, **colors)
        self.add_stepper(3, potency)

    def _update_buttons(self):
        if self.is_cofd:
            self._update_buttons_cofd()
        else:
            self._update_buttons_wod()

    def _update_buttons_cofd(self):
        self.buttons[0].disabled = self.character.vitae == 0
        self.buttons[2].disabled = self.character.vitae == self.character.max_vitae
        self.buttons[3].disabled = self.character.max_vitae == 1
        self.buttons[5].disabled = self.character.max_vitae == 75
        self.buttons[6].disabled = self.character.blood_potency == 0
        self.buttons[8].disabled = self.character.blood_potency == 10

    def _update_buttons_wod(self):
        self.buttons[0].disabled = self.character.blood_pool == 0
        self.buttons[2].disabled = self.character.blood_pool == self.character.max_bp
        self.buttons[3].disabled = self.character.max_bp == 1
        self.buttons[5].disabled = self.character.max_bp == 50
        self.buttons[6].disabled = self.character.generation == 3
        self.buttons[8].disabled = self.character.generation == 15

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)

        match i:
            # BP
            case 0:
                self.character.reduce_blood(1)
            case 2:
                self.character.add_blood(1)
            # Max BP
            case 3:
                self.character.decrement_max_blood()
            case 5:
                self.character.increment_max_blood()
            # Generation
            case 6:
                self.character.lower_potency()
            case 8:
                self.character.raise_potency()

        await super().callback(interaction)


class MummySekhemAdjuster(Adjuster):
    """Adjust Mummy-exclusive traits (Sekhem)."""

    character: cofd.Mummy

    def _populate(self):
        self.add_stepper(1, "Sekhem", dec_color=ButtonStyle.danger, inc_color=ButtonStyle.success)

    def _update_buttons(self):
        self.buttons[0].disabled = self.character.sekhem == 0
        self.buttons[2].disabled = self.character.sekhem == 10

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)

        match i:
            case 0:
                self.character.sekhem = max(0, self.character.sekhem - 1)
            case 2:
                self.character.sekhem = min(10, self.character.sekhem + 1)

        await super().callback(interaction)


class MummyPillarAdjuster(Adjuster):
    """Adjust Mummy pillar ratings."""

    character: cofd.Mummy

    def __init__(self, container: Toggler, char: cofd.Mummy, *pillars: cofd.Mummy.Pillars):
        assert 0 < len(pillars) <= 2
        self.pillars = pillars
        super().__init__(container, char)

    def _populate(self):
        bad = ButtonStyle.danger
        good = ButtonStyle.success

        row_offset = 0
        for pillar in self.pillars:
            self.add_stepper(
                row_offset + 1, f"{pillar.value} (Permanent)", dec_color=bad, inc_color=good
            )
            self.add_stepper(
                row_offset + 2, f"{pillar.value} (Current)", dec_color=bad, inc_color=good
            )
            row_offset += 2

    def _update_buttons(self):
        pillar = self.character.get_pillar(self.pillars[0])
        self.buttons[0].disabled = pillar.rating == 0
        self.buttons[3].disabled = pillar.temporary == 0
        self.buttons[2].disabled = pillar.rating == 5
        self.buttons[5].disabled = pillar.temporary >= pillar.rating

        if len(self.pillars) == 2:
            pillar = self.character.get_pillar(self.pillars[1])
            self.buttons[6].disabled = pillar.rating == 0
            self.buttons[9].disabled = pillar.temporary == 0
            self.buttons[8].disabled = pillar.rating == 5
            self.buttons[11].disabled = pillar.temporary >= pillar.rating

    async def callback(self, interaction: discord.Interaction):
        i, _ = self.get_button(interaction.custom_id)
        pillar = self.character.get_pillar(self.pillars[0 if i < 6 else 1])

        match i:
            # Permanent
            case 0 | 6:  # Decrement
                pillar.pdec()
                pillar.temporary = min(pillar.temporary, pillar.rating)
            case 2 | 8:  # Increment
                pillar.pinc()
            # Temporary
            case 3 | 9:
                pillar.tdec()
            case 5 | 11:
                pillar.tinc()

        await super().callback(interaction)
