"""Character creation functions."""

from core.characters import Character, Damage, Grounding
from core.characters.wod import Ghoul, Mortal, Vampire, gen_virtues
from utils import max_vtm_bp
from web.models import CharacterData, WizardSchema

CharacterType = Ghoul | Mortal | Vampire
SPLAT_MAPPING: dict[str, type[CharacterType]] = {
    "Ghoul": Ghoul,
    "Mortal": Mortal,
    "Vampire": Vampire,
}


async def create_character(wizard: WizardSchema, data: CharacterData) -> Character:
    # First, determine the splat. TODO: Make system-agnostic

    cls = SPLAT_MAPPING[data.splat]
    grounding = Grounding(**data.grounding.model_dump())

    if data.splat == "Ghoul":
        extra_args = dict(bond_strength=3)
    elif data.splat == "Vampire":
        gen = data.generation or 13
        extra_args = dict(
            generation=gen,
            max_bp=max_vtm_bp(gen),
            blood_pool=max_vtm_bp(gen),
        )
    else:
        extra_args = dict()

    char = cls(
        name=data.name,
        guild=wizard.guild_id,
        user=wizard.user_id,
        health=Damage.NONE * data.health,
        willpower=Damage.NONE * data.willpower,
        grounding=grounding,
        virtues=gen_virtues(data.virtue_dict),
        **extra_args,  # type: ignore
    )
    for trait, rating in data.traits.items():
        category = wizard.traits.category(trait)
        subcategory = wizard.traits.subcategory(trait)
        char.add_trait(trait, rating, category, subcategory)

    return char
