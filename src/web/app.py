"""Botch web app API endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import core
from config import BOTCH_URL, GAME_LINE
from core.characters import Damage, Grounding
from core.characters.wod import Ghoul, Mortal, Vampire, gen_virtues
from utils import max_vtm_bp
from web.cache import WizardCache
from web.models import CharacterData, WizardSchema

CharacterType = Ghoul | Mortal | Vampire
SPLAT_MAPPING: dict[str, type[CharacterType]] = {
    "Ghoul": Ghoul,
    "Mortal": Mortal,
    "Vampire": Vampire,
}

app = FastAPI()
cache = WizardCache()

origins = ["http://localhost:8000", BOTCH_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/character/create/{token}", response_model=WizardSchema)
async def get_wizard_schema(token: str):
    """Returns the character creation wizard data."""
    if token not in cache:
        raise HTTPException(
            status_code=404,
            detail="Invalid token. Either it expired, was already used, or never existed.",
        )
    return cache.get(token)


@app.post("/character/create")
async def create_character(data: CharacterData):
    """Create a character from provided data."""
    # First, determine the splat. TODO: Make system-agnostic
    wizard = cache.get(data.token)
    assert wizard.traits.line == GAME_LINE

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

    await core.cache.register(char)
    cache.remove(data.token)

    return {"message": f"Successfully created {char.name} on {wizard.guild_name}!"}


def wizard_url(token: str) -> str:
    """Returns the character creation URL."""
    return f"{BOTCH_URL}/wizard/{token}"
