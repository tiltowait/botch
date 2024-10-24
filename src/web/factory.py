"""Character creation functions."""

from typing import Any

from core.characters import Character, Damage, cofd, wod
from core.characters.base import GameLine
from core.characters.wod import gen_virtues
from utils import max_vtm_bp, max_vtr_vitae
from web.models import CharacterData, WizardSchema

CharacterType = wod.Ghoul | wod.Mortal | wod.Vampire | cofd.Mortal | cofd.Vampire
SPLAT_MAPPING: dict[GameLine, dict[str, type[CharacterType]]] = {
    GameLine.WOD: {
        "Ghoul": wod.Ghoul,
        "Mortal": wod.Mortal,
        "Vampire": wod.Vampire,
    },
    GameLine.COFD: {
        "Mortal": cofd.Mortal,
        "Vampire": cofd.Vampire,
    },
}


def fill_wod(data: CharacterData, splat_args: dict[str, Any]):
    """Fill in the character WoD-specific data."""
    if data.splat == "Vampire":
        gen = splat_args["generation"]
        splat_args["max_bp"] = max_vtm_bp(gen)
        splat_args["blood_pool"] = max_vtm_bp(gen)


def fill_cofd(data: CharacterData, splat_args: dict[str, Any]):
    """Fill in the CofD-specific data."""
    if data.splat == "Vampire":
        bp = splat_args["blood_potency"]
        splat_args["vitae"] = max_vtr_vitae(bp)
        splat_args["max_vitae"] = max_vtr_vitae(bp)


def create_character(wizard: WizardSchema, data: CharacterData) -> Character:
    """Create and return the character from the wizard and data."""
    splat_args: dict[str, Any] = dict(virtues=gen_virtues(data.virtues_dict))
    for special, value in data.special.items():
        splat_args[special.lower()] = value

    if wizard.traits.line == GameLine.WOD:
        fill_wod(data, splat_args)
    else:
        fill_cofd(data, splat_args)

    cls = SPLAT_MAPPING[wizard.traits.line][data.splat]
    print(data.splat)
    print(cls)
    char = cls(
        # Common traits
        name=data.name,
        guild=wizard.guild_id,
        user=wizard.user_id,
        health=Damage.NONE * data.health,
        willpower=Damage.NONE * data.willpower,
        grounding=data.grounding,
        **splat_args,  # Splat traits
    )
    for trait, rating in data.traits.items():
        category = wizard.traits.category(trait)
        subcategory = wizard.traits.subcategory(trait)
        char.add_trait(trait, rating, category, subcategory)

    return char
