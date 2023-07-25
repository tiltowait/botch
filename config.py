"""Shared configuration variables."""

import os

from dotenv import load_dotenv

load_dotenv()

# Bucket for storing character images
FC_BUCKET = "pcs-dev.botch.lol" if "TESTING" in os.environ else "pcs.botch.lol"
