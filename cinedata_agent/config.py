import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODELS = [
    "openrouter/free",
    "nvidia/nemotron-3.5-lightning:free",
    "z-ai/glm-5.2:free",
    "google/gemma-4-26b-a4b-it:free",
]

DB_PATH = Path(os.getenv("CINEROCKET_DB", "cinerocket.db"))
MAX_ROWS = 100          # linhas devolvidas ao modelo por consulta
QUERY_TIMEOUT_S = 90    # tempo máximo de uma consulta


def api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Defina OPENROUTER_API_KEY no .env (veja .env.example).")
    return key


def models() -> list[str]:
    raw = os.getenv("OPENROUTER_MODELS")
    return [m.strip() for m in raw.split(",") if m.strip()] if raw else DEFAULT_MODELS
