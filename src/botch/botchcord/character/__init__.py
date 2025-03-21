"""Character commands interface."""

from botch.botchcord.character import images, specialties, traits, web
from botch.botchcord.character.adjust import adjust
from botch.botchcord.character.delete import delete
from botch.botchcord.character.display import display

__all__ = ("adjust", "delete", "display", "images", "specialties", "traits", "web")
