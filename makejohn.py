# mypy: ignore-errors
"""Simple program to insert John or some random characters into the database
for testing purposes, because mucking about with the wizard over and over again
gets tedious pretty quickly."""

import asyncio
from argparse import ArgumentParser
from random import randint

import requests
from dotenv import load_dotenv

import db
import utils
from core.characters import Character, Damage, GameLine, Grounding, Splat
from core.characters.factory import Factory
from core.characters.wod import Vampire, gen_virtues

load_dotenv()  # You *MUST* have MONGO_URL and MONGO_DB defined!


def make_john(guild: int, user: int) -> Character:
    """John Wilcox is an Nosferatu this author used to play. He died well, so
    let's enshrine him here with his final stats."""
    core = {
        "name": "John Wilcox",
        "guild": guild,
        "user": user,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * 6,
        "grounding": Grounding(path="Humanity", rating=8),
        "generation": 13,
        "max_bp": 10,
        "blood_pool": 10,
        "virtues": gen_virtues(
            {
                "Conscience": 4,
                "SelfControl": 4,
                "Courage": 2,
            }
        ),
    }

    dots = [
        4,
        3,
        3,
        2,
        3,
        0,
        2,
        3,
        3,
        2,
        3,
        0,
        2,
        1,
        0,
        0,
        0,
        2,
        4,
        0,
        0,
        1,
        0,
        0,
        2,
        2,
        3,
        4,
        1,
        1,
        0,
        1,
        0,
        0,
        2,
        2,
        0,
        3,
        0,
    ]

    fac = Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, core)
    for dot in dots:
        fac.assign_next(dot)

    return fac.create()


def create_char(guild: int, user: int) -> Character:
    """Create a random character."""
    name = random_name()
    generation = randint(4, 13)
    max_bp = utils.max_vtm_bp(generation)
    max_trait = utils.max_vtm_trait(generation)

    core = {
        "name": name,
        "guild": guild,
        "user": user,
        "health": Damage.NONE * 7,
        "willpower": Damage.NONE * randint(1, 10),
        "grounding": Grounding(path="Humanity", rating=randint(1, 10)),
        "generation": randint(4, 13),
        "max_bp": max_bp,
        "blood_pool": randint(0, max_bp),
        "max_trait": max_trait,
        "virtues": gen_virtues(
            {
                "Conscience": randint(1, 5),
                "SelfControl": randint(1, 5),
                "Courage": randint(1, 5),
            }
        ),
    }
    fac = Factory(GameLine.WOD, Splat.VAMPIRE, Vampire, core)
    while fac.next_trait() is not None:
        fac.assign_next(randint(0, max_trait))

    return fac.create()


def random_name() -> str:
    """Fetch a random name."""
    r = requests.get("https://api.namefake.com/english-united-states")
    person = r.json()
    return person["name"]


async def main():
    await db.init()

    parser = ArgumentParser(description="Make John or a number of random characters.")
    parser.add_argument("--john", action="store_true", help="Just make John")
    parser.add_argument(
        "--guild",
        type=int,
        default=826628660450689074,
        help="The server the character(s) should belong to",
    )
    parser.add_argument(
        "--user",
        type=int,
        default=229736753676681230,
        help="The user the character(s) should belong to",
    )
    parser.add_argument(
        "--num-chars",
        "-n",
        type=int,
        default=1,
        help="The number of random characters to insert",
    )
    args = parser.parse_args()

    guild = args.guild
    user = args.user

    print("Guild:", guild)
    print("User: ", user)
    print("=========================")
    print()

    # Make some characters
    if args.john:
        print("Making John ... ", end="", flush=True)
        john = make_john(guild, user)
        await john.insert()
        print("done!")
    else:
        print(f"Inserting {args.num_chars} random characters ...")
        for _ in range(args.num_chars):
            char = create_char(guild, user)
            await char.insert()
            print(" ", char.name)
        print("... done!")


if __name__ == "__main__":
    asyncio.run(main())
