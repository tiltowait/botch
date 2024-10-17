"""Image-related command interface."""

from botchcord.character.images.display import display_images as display
from botchcord.character.images.upload import upload_image as upload

__all__ = ("display", "upload")
