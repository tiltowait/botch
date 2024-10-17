"""Character embed."""

from typing import Any

import discord

import bot
import botchcord
from core.characters import Character


class CEmbed(discord.Embed):
    """A standardized embed for displaying character data."""

    def __init__(
        self,
        bot: bot.BotchBot,
        character: Character,
        show_thumbnail=True,
        *args: Any,
        **kwargs: Any,
    ):
        icon_url = None
        owner = bot.get_user(character.user)
        owner_name = "Unknown User"

        if owner is not None:
            icon_url = botchcord.get_avatar(owner)
            owner_name = owner.display_name

        title = kwargs.get("title")
        if title and title != character.name:
            author_name = character.name
        else:
            kwargs["title"] = character.name
            author_name = owner_name

        super().__init__(*args, **kwargs)

        self.set_author(name=author_name, icon_url=icon_url)
        if show_thumbnail:
            self.set_thumbnail(url=character.profile.main_image)
