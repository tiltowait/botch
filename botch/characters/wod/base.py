"""Base WoD character attributes."""

from botch.characters.base import Character


class WoD(Character):
    """Abstract class for WoD characters. Used primarily for inheritance tree
    to let Beanie know what class to instantiate."""
