"""WoD (X20) character creation."""

from functools import partial

import discord

import utils
from botchcord.wizard import Wizard
from core.characters import Damage, GameLine, Grounding, Splat, Trait
from core.characters.wod import Ghoul, Mortal, Vampire


async def create(
    ctx: discord.ApplicationContext,
    splat: Splat,
    name: str,
    health: int,
    willpower: int,
    path: str,
    path_rating: int,
    integrity: str,
    integrity_rating: str,
    control: str,
    control_rating: str,
    courage: int,
    max_trait: int,
    *,
    generation: int | None = None,
    max_bp: int | None = None,
    bond_strength: int | None = None
):
    """Start a WoD character creation wizard."""
    # Because they have unique names, virtues are separate from regular traits
    tv = partial(Trait, category=Trait.Category.VIRTUE, subcategory=Trait.Subcategory.BLANK)
    virtues = [
        tv(name=integrity, rating=integrity_rating),
        tv(name=control, rating=control_rating),
        tv(name="Courage", rating=courage),
    ]

    if splat == Splat.VAMPIRE and generation is not None:
        if max_trait is None:
            max_trait = utils.max_vtm_trait(generation)
        if max_bp is None:
            max_bp = utils.max_vtm_bp(generation)
    elif max_trait is None:
        max_trait = 5

    wizard = Wizard(
        GameLine.WOD,
        splat,
        creation_class(splat),
        generation=generation,
        max_rating=max_trait,
        name=name,
        guild=ctx.guild.id,
        user=ctx.user.id,
        health=Damage.NONE * health,
        willpower=Damage.NONE * willpower,
        grounding=Grounding(path=utils.normalize_text(path), rating=path_rating),
        max_bp=max_bp,
        blood_pool=max_bp,
        virtues=virtues,
        bond_strength=bond_strength,
    )
    await wizard.start(ctx.interaction)


def creation_class(splat: Splat):
    """Gets the character creation class for the given line and splat."""
    splats = {
        Splat.MORTAL: Mortal,
        Splat.GHOUL: Ghoul,
        Splat.VAMPIRE: Vampire,
    }
    return splats[splat]
