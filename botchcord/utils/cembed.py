"""Character embed."""

import discord

import botchcord
from core.characters import Character


class CEmbed(discord.Embed):
    """A standardized embed for displaying character data."""

    def __init__(
        self, bot: discord.Bot, character: Character, show_thumbnail=True, *args, **kwargs
    ):
        icon_url = None
        if (owner := bot.get_user(character.user)) is not None:
            icon_url = botchcord.get_avatar(owner)

        title = kwargs.get("title")
        if title and title != character.name:
            author_name = character.name
        else:
            kwargs["title"] = character.name
            author_name = owner.display_name

        super().__init__(*args, **kwargs)

        self.set_author(name=author_name, icon_url=icon_url)
        if show_thumbnail:
            self.set_thumbnail(url=character.profile.main_image)
