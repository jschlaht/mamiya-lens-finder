"""Klassifiziert Anzeigentexte per `claude`-CLI (Option A: Claude Pro/Max-Abo
statt separatem Anthropic-API-Key).

Ruft `claude -p ... --output-format json --json-schema ...` als Subprocess
auf. Authentifizierung läuft über die bereits eingeloggte claude-CLI bzw.
über CLAUDE_CODE_OAUTH_TOKEN (siehe `claude setup-token`) - keine separate
API-Abrechnung.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass

from config import CLAUDE_BINARY, CLAUDE_MODEL, MAX_FOCAL_LENGTH_MM, MIN_FOCAL_LENGTH_MM

_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_lens": {
            "type": "boolean",
            "description": "True, wenn die Anzeige (primär) ein einzelnes Objektiv verkauft "
            "(nicht ein Kamera-Body, Set mit Body, Zubehör, Adapter oder Gesuch).",
        },
        "is_mamiya_645_mount": {
            "type": "boolean",
            "description": "True, wenn das Objektiv für das Mamiya-645-Bajonett (645 / M645 / "
            "645 Super/Pro/AF) passt.",
        },
        "is_prime_lens": {
            "type": "boolean",
            "description": "True, wenn es sich um eine Festbrennweite handelt (kein Zoom).",
        },
        "focal_length_mm": {
            "type": ["number", "null"],
            "description": "Erkannte Brennweite in mm, oder null falls nicht eindeutig erkennbar.",
        },
        "reason": {
            "type": "string",
            "description": "Kurze Begründung auf Deutsch (1-2 Sätze).",
        },
    },
    "required": ["is_lens", "is_mamiya_645_mount", "is_prime_lens", "focal_length_mm", "reason"],
    "additionalProperties": False,
}


class ClassificationError(RuntimeError):
    pass


@dataclass
class Classification:
    is_lens: bool
    is_mamiya_645_mount: bool
    is_prime_lens: bool
    focal_length_mm: float | None
    reason: str

    @property
    def matches(self) -> bool:
        if not (self.is_lens and self.is_mamiya_645_mount and self.is_prime_lens):
            return False
        if self.focal_length_mm is None:
            return False
        return MIN_FOCAL_LENGTH_MM <= self.focal_length_mm <= MAX_FOCAL_LENGTH_MM


def classify(title: str, description: str, price_text: str) -> Classification:
    prompt = (
        "Analysiere die folgende kleinanzeigen.de-Anzeige und bestimme, ob es sich um ein "
        "einzelnes Festbrennweiten-Objektiv (keine Zoomobjektiv, kein Body, kein Set, kein "
        "Gesuch) für das Mamiya-645-System handelt. Antworte ausschließlich mit dem "
        "strukturierten JSON gemäß Schema, ohne weiteren Text.\n\n"
        f"Titel: {title}\n"
        f"Preis: {price_text}\n"
        f"Beschreibung:\n{description}\n"
    )

    cmd = [
        CLAUDE_BINARY,
        "-p",
        prompt,
        "--model",
        CLAUDE_MODEL,
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(_JSON_SCHEMA),
        "--tools",
        "",
        "--no-session-persistence",
        "--setting-sources",
        "",
    ]

    # Windows: npm installiert die claude-CLI als .cmd-Shim. subprocess kann
    # solche Batch-Dateien mit shell=False nicht direkt ausführen (auch nicht
    # über den vollen Pfad) - dort über die Shell (cmd.exe) aufrufen, die
    # PATH/PATHEXT wie gewohnt auflöst. Auf macOS/Linux bleibt shell=False,
    # da dort args als Liste erwartet und sicher ohne Shell-Interpretation
    # ausgeführt wird.
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, shell=(sys.platform == "win32")
        )
    except FileNotFoundError as e:
        raise ClassificationError(
            f"claude-CLI nicht gefunden unter '{CLAUDE_BINARY}'. Ist sie installiert "
            "(npm install -g @anthropic-ai/claude-code) und CLAUDE_BINARY korrekt gesetzt?"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ClassificationError("claude-CLI hat nicht innerhalb von 120s geantwortet.") from e

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise ClassificationError(
            f"Konnte claude-CLI-Ausgabe nicht parsen (exit={proc.returncode}): "
            f"stdout={proc.stdout[:500]!r} stderr={proc.stderr[:500]!r}"
        ) from e

    if envelope.get("is_error") or proc.returncode != 0:
        raise ClassificationError(f"claude-CLI meldete einen Fehler: {envelope.get('result')}")

    result = envelope.get("result")
    data = json.loads(result) if isinstance(result, str) else result
    if not isinstance(data, dict):
        raise ClassificationError(f"Unerwartetes Ergebnisformat von claude-CLI: {envelope}")

    return Classification(
        is_lens=data["is_lens"],
        is_mamiya_645_mount=data["is_mamiya_645_mount"],
        is_prime_lens=data["is_prime_lens"],
        focal_length_mm=data["focal_length_mm"],
        reason=data["reason"],
    )
