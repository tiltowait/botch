"""A tool that exports character data for web testing."""

import json
import os
import sys
from argparse import ArgumentParser
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URL"))
db = client.dev


def get_outfile() -> str:
    """Get the output file from arguments."""
    parser = ArgumentParser()
    parser.add_argument("outfile")
    args = parser.parse_args()

    return os.path.realpath(args.outfile)


def main():
    outfile = get_outfile()
    if os.path.exists(outfile):
        while True:
            confirmation = input("File already exists. Overwrite? [y/n] ").lower()
            if confirmation == "n":
                sys.exit()
            if confirmation == "y":
                break

    characters: list[dict[str, Any]] = list(db.characters.find())

    guild_ids: set[int] = {c["guild"] for c in characters}
    guild_data: list[dict[str, Any]] = list(db.guilds.find({"guild": {"$in": list(guild_ids)}}))
    guilds: list[dict[str, int | str]] = [
        {"id": g["guild"], "name": g["name"], "icon": ""} for g in guild_data
    ]

    data = {"guilds": guilds, "characters": characters}
    with open(outfile, "w") as f:
        json.dump(data, f, default=str, indent=2)


if __name__ == "__main__":
    main()
