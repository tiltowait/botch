"""Botch web app API endpoints."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import core
from config import BOTCH_URL, GAME_LINE, MAX_NAME_LEN
from core.characters import Damage, Grounding
from core.characters.wod import Ghoul, Mortal, Vampire, gen_virtues
from utils import max_vtm_bp, normalize_text
from web.cache import WizardCache
from web.models import CharacterData, NameCheck, WizardSchema

CharacterType = Ghoul | Mortal | Vampire
SPLAT_MAPPING: dict[str, type[CharacterType]] = {
    "Ghoul": Ghoul,
    "Mortal": Mortal,
    "Vampire": Vampire,
}

app = FastAPI()
cache = WizardCache()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

    data.name = normalize_text(data.name)
    if len(data.name) > MAX_NAME_LEN:
        raise HTTPException(
            status_code=422, detail=f"{data.name} is too long. Max name length is {MAX_NAME_LEN}."
        )
    if await core.cache.has_character(wizard.guild_id, wizard.user_id, data.name):
        raise HTTPException(
            status_code=422,
            detail=f"You already have a character named {data.name} on {wizard.guild_name}!",
        )

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


@app.post("/character/valid-name")
async def check_name_validity(check: NameCheck):
    """Check whether the user is allowed to create a character with that name."""
    try:
        schema = cache.get(check.token)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Invalid token. Either it expired, was already used, or never existed.",
        )

    if len(check.name) > MAX_NAME_LEN:
        diff = len(check.name) - MAX_NAME_LEN
        return dict(
            valid=False,
            details=f"{check.name} is too long by {diff}.",
        )

    already_exists = await core.cache.has_character(schema.guild_id, schema.user_id, check.name)
    if already_exists:
        return dict(
            valid=False,
            details=f"You already have a character named {check.name}.",
        )

    return {"valid": True}


def wizard_url(token: str) -> str:
    """Returns the character creation URL."""
    return f"{BOTCH_URL}/wizard/{token}"
