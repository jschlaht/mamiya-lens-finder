import json

from config import STATE_FILE


def load_seen_ids() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    with STATE_FILE.open("r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen_ids(seen_ids: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(sorted(seen_ids), f, ensure_ascii=False, indent=2)
