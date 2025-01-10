"""A tool for launching the bots via a poetry script."""

from typing import Literal

from dotenv import load_dotenv


def run_bot(bot_type: Literal["botch", "beat"]) -> None:
    load_dotenv(".env")
    load_dotenv(f".env.{bot_type}")

    import main

    main.main()
