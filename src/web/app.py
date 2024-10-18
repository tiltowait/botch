"""Botch web app API endpoints."""

from fastapi import FastAPI, HTTPException

from config import BOTCH_URL
from web.cache import WizardCache
from web.models import WizardSchema

app = FastAPI()
cache = WizardCache()


@app.get("/character/create/{token}", response_model=WizardSchema)
async def get_wizard_schema(token: str):
    """Returns the character creation wizard data."""
    if token not in cache:
        raise HTTPException(
            status_code=404,
            detail="Unknown token. Either it expired, was already used, or never existed.",
        )
    return cache.get(token)


def wizard_url(token: str) -> str:
    """Returns the character creation URL."""
    return f"{BOTCH_URL}/wizard/{token}"
