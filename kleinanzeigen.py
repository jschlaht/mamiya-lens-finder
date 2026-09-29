"""Schlanker, höflicher Scraper für kleinanzeigen.de Suchergebnisse.

Nutzt normale HTTP-Requests gegen serverseitig gerenderte Seiten
(kein Login, keine Umgehung von Bot-Schutz/CAPTCHAs). Die genutzten
URL-Pfade (/s-*.html Suchergebnisse, /s-anzeige/... Detailseiten) sind
laut robots.txt von kleinanzeigen.de nicht gesperrt.

Jede Anzeige trägt ein eingebettetes JSON-LD <script> mit title/description -
das ist der stabilste Weg an die Kerndaten zu kommen, da CSS-Klassen auf
kleinanzeigen.de generierte Tailwind-Utility-Klassen sind und sich häufiger
ändern können als die schema.org-Auszeichnung.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from config import BASE_URL, REQUEST_DELAY_SECONDS, USER_AGENT

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"})


@dataclass
class Listing:
    ad_id: str
    url: str
    title: str
    short_description: str
    price_text: str
    location_date: str


def _slugify(query: str) -> str:
    slug = query.lower().strip()
    slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return quote(slug)


def search(query: str) -> list[Listing]:
    """Holt Seite 1 der Suchergebnisse für einen Suchbegriff."""
    url = f"{BASE_URL}/s-{_slugify(query)}/k0"
    resp = session.get(url, timeout=20)
    resp.raise_for_status()
    # resp.content (Bytes) statt resp.text: requests errät die Encoding sonst
    # teils falsch (ISO-8859-1), lxml erkennt UTF-8 zuverlässig selbst.
    soup = BeautifulSoup(resp.content, "lxml")

    listings: list[Listing] = []
    for article in soup.select("article[data-adid]"):
        ad_id = article.get("data-adid")
        href = article.get("data-href")
        if not ad_id or not href:
            continue

        title, short_description = _title_and_description(article)
        price_text = _clean_text(article.select_one(".text-title3.font-strong.text-secondary"))
        location_date = _clean_text(article.select_one("div.flex.items-start.justify-between"))

        listings.append(
            Listing(
                ad_id=ad_id,
                url=BASE_URL + href,
                title=title,
                short_description=short_description,
                price_text=price_text,
                location_date=location_date,
            )
        )
    return listings


def _clean_text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _title_and_description(article) -> tuple[str, str]:
    ld_script = article.select_one('script[type="application/ld+json"]')
    if ld_script:
        try:
            data = json.loads(ld_script.get_text())
            title = data.get("title", "")
            description = data.get("description", "")
            if title:
                return title, description
        except json.JSONDecodeError:
            pass
    return "(kein Titel gefunden)", ""


def fetch_full_description(url: str, retries: int = 2) -> str:
    """Holt die vollständige Beschreibung von der Anzeigen-Detailseite.

    kleinanzeigen.de antwortet gelegentlich langsam/gar nicht (transiente
    Timeouts) - das ist kein Parsing-Problem, wird aber mit ein paar
    Wiederholungen abgefedert, damit einzelne Anzeigen nicht dauerhaft
    unklassifiziert bleiben.
    """
    last_error: Exception | None = None
    for attempt in range(1 + retries):
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "lxml")
            desc_el = soup.select_one("#viewad-description-text")
            return desc_el.get_text("\n", strip=True) if desc_el else ""
        except requests.exceptions.RequestException as e:
            last_error = e
    raise last_error
