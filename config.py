import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SEARCH_QUERIES = [
    q.strip() for q in os.environ.get("SEARCH_QUERIES", "mamiya 645").split(",") if q.strip()
]

MIN_FOCAL_LENGTH_MM = int(os.environ.get("MIN_FOCAL_LENGTH_MM", 35))
MAX_FOCAL_LENGTH_MM = int(os.environ.get("MAX_FOCAL_LENGTH_MM", 150))

# Option A: Klassifikation läuft über die `claude`-CLI (Claude Pro/Max-Abo),
# nicht über einen separaten Anthropic-API-Key. CLAUDE_CODE_OAUTH_TOKEN
# (per `claude setup-token` erzeugt) landet via dotenv automatisch in
# os.environ und wird vom claude-Subprocess in kleinanzeigen.py/classifier.py
# aufgegriffen - hier ist kein extra Code nötig.
CLAUDE_BINARY = os.environ.get("CLAUDE_BINARY", "claude")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "sonnet")

REQUEST_DELAY_SECONDS = float(os.environ.get("REQUEST_DELAY_SECONDS", 1.5))

STATE_FILE = BASE_DIR / "state" / "seen_ads.json"

BASE_URL = "https://www.kleinanzeigen.de"
USER_AGENT = (
    "Mozilla/5.0 (compatible; MamiyaLensFinder/1.0; privater Suchagent; "
    "+https://github.com/) "
)
