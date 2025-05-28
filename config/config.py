"""
Centralised runtime settings.

Reads environment variables from `.env` at import-time so every module that
`import config` gets the same values.
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# ------------------------------------------------------------------ load .env
env_file = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_file)

# ---------------------------------------------------------------- credentials
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
GAPGPT_API_KEY:     str | None = os.getenv("GAPGPT_API_KEY")

if TELEGRAM_BOT_TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing in environment / .env")
if GAPGPT_API_KEY is None:
    raise RuntimeError("GAPGPT_API_KEY missing in environment / .env")

# ---------------------------------------------------------------- GapGPT base
# single place to swap endpoints if GapGPT changes its URL scheme
GAPGPT_API_BASE: str = "https://api.gapgpt.app/v1"
