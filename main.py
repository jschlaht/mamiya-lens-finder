"""Mamiya-645-Objektiv-Finder für kleinanzeigen.de.

Sucht regelmäßig (z.B. per Cron) nach neuen Anzeigen, lässt neue Treffer
per Claude auf "Festbrennweite im gewünschten Brennweitenbereich" prüfen
und meldet Treffer per Telegram.
"""

import logging
import sys

import classifier
import kleinanzeigen
import notifier
import state
from config import MAX_FOCAL_LENGTH_MM, MIN_FOCAL_LENGTH_MM, SEARCH_QUERIES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("mamiya-lens-finder")


def run() -> None:
    seen_ids = state.load_seen_ids()
    is_first_run = len(seen_ids) == 0

    all_listings = {}
    for query in SEARCH_QUERIES:
        log.info("Suche: %s", query)
        for listing in kleinanzeigen.search(query):
            all_listings[listing.ad_id] = listing

    new_listings = [l for ad_id, l in all_listings.items() if ad_id not in seen_ids]
    log.info("%d Anzeigen gefunden, %d davon neu.", len(all_listings), len(new_listings))

    if is_first_run:
        log.info(
            "Erster Lauf: markiere alle %d aktuell gefundenen Anzeigen als bekannt, "
            "ohne zu benachrichtigen (Baseline).",
            len(new_listings),
        )
        state.save_seen_ids(set(all_listings.keys()))
        return

    matches = 0
    for listing in new_listings:
        try:
            try:
                full_description = kleinanzeigen.fetch_full_description(listing.url)
                description = full_description or listing.short_description
            except Exception:
                log.warning(
                    "Volltext für %s (%s) nicht abrufbar, nutze Kurzbeschreibung von der "
                    "Suchseite als Fallback.",
                    listing.ad_id,
                    listing.url,
                    exc_info=True,
                )
                description = listing.short_description

            result = classifier.classify(listing.title, description, listing.price_text)
            log.info(
                "%s -> lens=%s mount=%s prime=%s focal=%s (%s)",
                listing.title,
                result.is_lens,
                result.is_mamiya_645_mount,
                result.is_prime_lens,
                result.focal_length_mm,
                result.reason,
            )

            if result.matches:
                matches += 1
                notifier.send_message(
                    f"📷 *Mamiya 645 Festbrennweite gefunden*\n\n"
                    f"*{listing.title}*\n"
                    f"Brennweite: {result.focal_length_mm:.0f} mm\n"
                    f"Preis: {listing.price_text or 'k.A.'}\n"
                    f"Ort: {listing.location_date}\n\n"
                    f"{listing.url}"
                )
        except Exception:
            log.exception("Fehler bei Anzeige %s (%s)", listing.ad_id, listing.url)
        finally:
            seen_ids.add(listing.ad_id)

    state.save_seen_ids(seen_ids)
    log.info(
        "Fertig. %d neue Treffer im Bereich %d-%d mm gemeldet.",
        matches,
        MIN_FOCAL_LENGTH_MM,
        MAX_FOCAL_LENGTH_MM,
    )


if __name__ == "__main__":
    run()
