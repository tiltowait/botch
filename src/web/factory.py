"""Character creation functions."""

from typing import Any

from core.characters import Character, Damage
from core.characters.base import GameLine
from core.characters.wod import Ghoul, Mortal, Vampire, gen_virtues
from utils import max_vtm_bp
from web.models import CharacterData, WizardSchema

CharacterType = Ghoul | Mortal | Vampire
SPLAT_MAPPING: dict[str, type[CharacterType]] = {
    "Ghoul": Ghoul,
    "Mortal": Mortal,
    "Vampire": Vampire,
}


def fill_wod(data: CharacterData, splat_args: dict[str, Any]):
    """Start the character args with WoD data."""
    if data.splat == "Vampire":
        gen = splat_args["generation"]
        splat_args["max_bp"] = max_vtm_bp(gen)
        splat_args["blood_pool"] = max_vtm_bp(gen)


async def create_character(wizard: WizardSchema, data: CharacterData) -> Character:
    """Create and return the character from the wizard and data."""
    splat_args: dict[str, Any] = dict(virtues=gen_virtues(data.virtues_dict))
    for special, value in data.special.items():
        splat_args[special.lower()] = value

    if wizard.traits.line == GameLine.WOD:
        fill_wod(data, splat_args)
    else:
        raise NotImplementedError("CofD isn't implemented yet!")

    cls = SPLAT_MAPPING[data.splat]
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
