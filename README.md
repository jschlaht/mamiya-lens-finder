# Mamiya 645 Objektiv-Finder

Ein kleiner KI-Agent, der rund um die Uhr kleinanzeigen.de nach
Festbrennweiten-Objektiven für die analoge Mittelformatkamera Mamiya 645
durchsucht (Brennweite konfigurierbar, Standard: 35–150 mm) und bei einem
Treffer eine Nachricht per Telegram schickt.

Dieses Projekt eignet sich gut, um sich in kleinen, überschaubaren Schritten
mit KI-Agenten vertraut zu machen: Es kombiniert Web-Scraping, eine LLM-
Klassifikation und eine simple Benachrichtigung zu einem funktionierenden
Werkzeug – kein Rahmenwerk, keine Magie, jede Zeile Code ist lesbar.

**Funktioniert auf macOS, Linux und Windows.** Überall wo sich die Schritte
unterscheiden, ist das unten explizit markiert (🍎 macOS/Linux vs. 🪟
Windows).

---

## Inhaltsverzeichnis

1. [Was macht dieser Agent eigentlich?](#was-macht-dieser-agent-eigentlich)
2. [Wie funktioniert das im Detail?](#wie-funktioniert-das-im-detail)
3. [Voraussetzungen](#voraussetzungen)
4. [Schritt-für-Schritt-Setup](#schritt-für-schritt-setup)
5. [Ersten Lauf ausführen](#ersten-lauf-ausführen)
6. [Automatisch im Hintergrund laufen lassen](#automatisch-im-hintergrund-laufen-lassen)
7. [Projektstruktur – welche Datei macht was?](#projektstruktur--welche-datei-macht-was)
8. [Konfiguration (.env)](#konfiguration-env)
9. [Häufige Probleme (Troubleshooting)](#häufige-probleme-troubleshooting)
10. [Einstiegstipps für Programmier-/KI-Agenten-Neulinge](#einstiegstipps-für-programmier-ki-agenten-neulinge)
11. [Fairness & Spielregeln beim Scrapen](#fairness--spielregeln-beim-scrapen)

---

## Was macht dieser Agent eigentlich?

Stell dir vor, du suchst ein ganz bestimmtes Objektiv auf einem
Gebrauchtwaren-Marktplatz. Das Problem: Es werden ständig neue Anzeigen
eingestellt, und die Suchfunktion der Website kann nicht filtern, ob ein
Objektiv eine "Festbrennweite" ist oder ob die Brennweite in deinem
Wunschbereich liegt – diese Info steht meistens nur im Fließtext der
Anzeige, nicht in einem durchsuchbaren Feld.

Genau hier kommt die KI ins Spiel: Der Agent liest jede neue Anzeige wie ein
Mensch und beantwortet drei Fragen dazu:

1. Ist das überhaupt ein *einzelnes Objektiv* (und kein Kamera-Body, kein
   Set, kein Zubehör)?
2. Passt es an das Mamiya-645-Bajonett?
3. Ist es eine *Festbrennweite* (kein Zoom) mit einer Brennweite in deinem
   gewünschten Bereich?

Nur wenn alle drei Fragen mit "Ja" beantwortet werden, bekommst du eine
Telegram-Nachricht. Alles andere wird stillschweigend ignoriert.

## Wie funktioniert das im Detail?

Der Agent läuft in Zyklen ab (z.B. alle 20 Minuten automatisiert, siehe
unten). Jeder Zyklus macht Folgendes:

```
1. Suchen        →  kleinanzeigen.de nach "mamiya 645" & "mamiya sekor" durchsuchen
2. Vergleichen    →  Welche Anzeigen-IDs kennen wir schon aus früheren Läufen?
3. Nachladen      →  Für jede NEUE Anzeige: vollständige Beschreibung laden
4. Klassifizieren →  Claude liest Titel + Beschreibung + Preis und beantwortet
                      die drei Fragen von oben als strukturiertes Ergebnis
5. Benachrichtigen→  Bei einem Treffer: Telegram-Nachricht mit Link versenden
6. Merken         →  Anzeigen-ID speichern, damit sie nie doppelt gemeldet wird
```

Beim allerersten Lauf gibt es einen Sonderfall: Es gibt ja schon ~150+
existierende Anzeigen auf kleinanzeigen.de. Damit du nicht mit 150
Nachrichten auf einmal bombardiert wirst, merkt sich der Agent beim ersten
Lauf einfach alle aktuell vorhandenen Anzeigen als "schon gesehen", ohne
etwas zu melden (die sogenannte *Baseline*). Erst ab dem zweiten Lauf werden
wirklich neue Anzeigen erkannt und gemeldet.

## Voraussetzungen

Folgende Dinge sollten auf dem Rechner vorhanden bzw. installierbar sein:

- **Ein Terminal.**
  - 🍎 macOS: Spotlight öffnen (`Cmd + Leertaste`), "Terminal" eintippen,
    Enter drücken.
  - 🪟 Windows: Start-Menü öffnen, "PowerShell" eintippen, Enter drücken
    (Windows PowerShell oder das modernere "Terminal" – beide funktionieren
    für dieses Projekt gleich gut).
- **Python 3** (Version 3.9 oder neuer).
  - 🍎 macOS: meist schon vorinstalliert, prüfen mit `python3 --version`.
  - 🪟 Windows: falls nicht vorhanden, von
    [python.org/downloads](https://www.python.org/downloads/) installieren.
    **Wichtig:** Beim Installer unbedingt das Häkchen bei **"Add python.exe
    to PATH"** setzen – sonst findet das Terminal den Befehl später nicht.
    Danach prüfen mit `python --version` (unter Windows heißt der Befehl
    `python`, nicht `python3`).
- **Node.js / npm** (wird für die `claude`-CLI gebraucht).
  - Beide Systeme: von [nodejs.org](https://nodejs.org/) die
    "LTS"-Version installieren (Installer einfach durchklicken, Standard-
    einstellungen reichen). Prüfen mit `npm --version` – dieser Befehl heißt
    auf beiden Systemen gleich.
- **Ein Claude-Account mit Pro- oder Max-Abo** (für die KI-Klassifikation).
- **Ein Telegram-Account** (für die Benachrichtigungen) – App oder
  [web.telegram.org](https://web.telegram.org/).

Kein Vorwissen in Python oder Web-Scraping nötig – die folgenden Schritte
sind bewusst sehr kleinteilig beschrieben.

## Schritt-für-Schritt-Setup

### 1. Terminal öffnen und ins Projektverzeichnis wechseln

🍎 macOS/Linux:
```bash
cd ~/Projects/mamiya-lens-finder
```

🪟 Windows (PowerShell) – Pfad an den tatsächlichen Speicherort anpassen,
z.B. wenn der Ordner auf dem Desktop liegt:
```powershell
cd $HOME\Desktop\mamiya-lens-finder
```

`cd` steht für "change directory" – damit sagst du dem Terminal, in welchem
Ordner die nächsten Befehle ausgeführt werden sollen.

### 2. Virtuelle Umgebung anlegen

🍎 macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

🪟 Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> **Windows-Stolperstein:** PowerShell blockiert das Ausführen von Skripten
> standardmäßig aus Sicherheitsgründen. Kommt die Fehlermeldung *"...cannot
> be loaded because running scripts is disabled on this system"*, einmalig
> ausführen (gilt nur für das aktuelle Fenster, keine dauerhafte
> Systemänderung):
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
> Danach `.venv\Scripts\Activate.ps1` erneut versuchen. Alternativ im
> normalen `cmd.exe`-Fenster (statt PowerShell) mit `.venv\Scripts\activate.bat`
> aktivieren – dort gibt es diese Einschränkung nicht.

Eine **virtuelle Umgebung** ("venv") ist ein isolierter Bereich nur für
dieses Projekt, in dem Python-Pakete installiert werden, ohne das restliche
System zu beeinflussen. Nach dem Aktivieren steht vor deiner Terminal-Zeile
ein `(.venv)` – das zeigt: Die Umgebung ist aktiv. Das musst du in **jedem
neuen Terminal-Fenster** wiederholen, bevor du `python main.py` ausführst.

### 3. Python-Abhängigkeiten installieren

Beide Systeme (im aktivierten `.venv`):
```bash
pip install -r requirements.txt
```

`pip` ist der Paketmanager von Python. Die Datei `requirements.txt` listet
auf, welche fertigen Bausteine (Bibliotheken) das Projekt braucht, z.B.
`requests` zum Abrufen von Webseiten oder `beautifulsoup4` zum Auslesen von
HTML. Kein Rad wird neu erfunden.

### 4. Die claude-CLI installieren

Beide Systeme:
```bash
npm install -g @anthropic-ai/claude-code
```

🪟 Windows: Falls die Installation mit einem Berechtigungsfehler
abbricht, das Terminal einmal **"Als Administrator ausführen"** (Rechtsklick
auf PowerShell/Terminal im Startmenü) und den Befehl dort wiederholen.

Das ist Anthropics eigenes Kommandozeilen-Werkzeug für Claude. Der Agent
nutzt es, um Anzeigentexte klassifizieren zu lassen – über dein bestehendes
Claude Pro/Max-Abo, **ohne** dass du dich extra bei der (separat
abgerechneten) Anthropic-API registrieren musst.

### 5. Bei Claude einloggen und einen Cron-Token erzeugen

Beide Systeme:
```bash
claude setup-token
```

Das öffnet einen Browser zum Login mit deinem Claude-Account und gibt
danach einen langlebigen Token aus (beginnt etwa mit `sk-ant-oat...`).
**Diesen Token kopieren** – er wird gleich in Schritt 8 gebraucht. Er wird
gebraucht, damit der Agent sich auch dann anmelden kann, wenn später
niemand am Rechner sitzt (automatischer Hintergrund-Lauf, siehe unten).

### 6. Telegram-Bot anlegen

1. In Telegram nach **@BotFather** suchen und ein Gespräch öffnen.
2. `/newbot` eingeben und den Anweisungen folgen (Name + Nutzername
   vergeben, z.B. `MamiyaLensFinderBot`).
3. BotFather gibt dir einen **Token** aus (Format etwa
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`). Kopieren.

### 7. Deine Telegram-Chat-ID herausfinden

1. Dem neu erstellten Bot **einmal irgendeine Nachricht schreiben** (z.B.
   "Hallo") – sonst kann der Bot dir später nicht antworten.
2. Im Browser diese Adresse öffnen (Token aus Schritt 6 einsetzen):
   ```
   https://api.telegram.org/bot<DEIN-TOKEN>/getUpdates
   ```
3. In der Antwort nach `"chat":{"id":` suchen – die Zahl dahinter ist deine
   Chat-ID.

### 8. `.env`-Datei anlegen

🍎 macOS/Linux:
```bash
cp .env.example .env
open -e .env
```

🪟 Windows (PowerShell):
```powershell
Copy-Item .env.example .env
notepad .env
```

Die `.env`-Datei enthält alle persönlichen Zugangsdaten und Einstellungen
– sie wird **nicht** mit ins Git-Repository übernommen (siehe
`.gitignore`), damit niemand versehentlich seine Zugangsdaten veröffentlicht.
(Tipp: Falls schon installiert, ist [VS Code](https://code.visualstudio.com/)
angenehmer zum Bearbeiten als Notepad – dann stattdessen `code .env`.)

In der geöffneten Datei eintragen:

- `TELEGRAM_BOT_TOKEN` → aus Schritt 6
- `TELEGRAM_CHAT_ID` → aus Schritt 7
- `CLAUDE_CODE_OAUTH_TOKEN` → aus Schritt 5
- `CLAUDE_BINARY` → Pfad zur claude-Installation, siehe direkt darunter

**`CLAUDE_BINARY` herausfinden:**

🍎 macOS/Linux:
```bash
which claude
```

🪟 Windows (PowerShell):
```powershell
Get-Command claude | Select-Object -ExpandProperty Source
```
(Ergebnis sieht etwa so aus:
`C:\Users\<DeinName>\AppData\Roaming\npm\claude.cmd` – diesen kompletten
Pfad 1:1 in `CLAUDE_BINARY` eintragen, inklusive `.cmd`-Endung.)

Das ist wichtig, weil ein später eingerichteter automatischer
Hintergrund-Lauf (Cron/Aufgabenplanung) ein sehr minimales `PATH` hat und
`claude` dort sonst nicht findet.

Die restlichen Variablen (Suchbegriffe, Brennweitenbereich, …) haben schon
sinnvolle Standardwerte, können aber gerne angepasst werden – siehe
[Konfiguration](#konfiguration-env).

## Ersten Lauf ausführen

Beide Systeme (venv muss aktiv sein, siehe Schritt 2):
```bash
python main.py
```
(🪟 Windows: falls `python main.py` einen Fehler wirft, `py main.py`
probieren – manche Windows-Installationen registrieren nur den
`py`-Befehl.)

Wie oben erklärt: Der erste Lauf legt nur die Baseline an und meldet noch
nichts. Das erkennst du an einer Log-Zeile wie:

```
[INFO] Erster Lauf: markiere alle 42 aktuell gefundenen Anzeigen als bekannt, ohne zu benachrichtigen (Baseline).
```

Führe `python main.py` ein zweites Mal aus (z.B. am nächsten Tag oder nach
ein paar Stunden) – jetzt werden wirklich neue Anzeigen erkannt,
klassifiziert und bei Treffer per Telegram gemeldet.

## Automatisch im Hintergrund laufen lassen

Damit du nicht jedes Mal manuell `python main.py` starten musst, lässt man
das Skript regelmäßig automatisch laufen. Wie das eingerichtet wird,
unterscheidet sich zwischen den Betriebssystemen.

**Tipp:** Erstmal ein paar Tage manuell laufen lassen und beobachten, bevor
du es automatisierst – so lernst du das Verhalten kennen und siehst
eventuelle Fehlermeldungen direkt im Terminal statt versteckt im Log.

### 🍎 macOS/Linux: Cron

**Cron** ist ein seit Jahrzehnten bewährter, im Betriebssystem eingebauter
Zeitplaner.

```bash
crontab -e
```

Öffnet einen Editor für deine persönliche Cron-Tabelle. Folgende Zeile
hinzufügen (alle 20 Minuten ausführen, Pfad anpassen):

```
*/20 * * * * /Users/<DeinName>/Projects/mamiya-lens-finder/run.sh >> /Users/<DeinName>/Projects/mamiya-lens-finder/cron.log 2>&1
```

Speichern und den Editor schließen (bei `vim`, dem Standardeditor: `Esc`,
dann `:wq` und Enter). Ab jetzt läuft der Agent von selbst im Hintergrund;
im `cron.log` kannst du jederzeit nachschauen, was er gerade tut.

### 🪟 Windows: Aufgabenplanung (Task Scheduler)

Windows hat kein Cron, sondern die grafische **Aufgabenplanung**
("Task Scheduler"). Das Projekt bringt dafür ein `run.bat`-Skript mit, das
die virtuelle Umgebung aktiviert und `main.py` ausführt.

**Variante A – per Kommandozeile (schnell):** PowerShell **als
Administrator** öffnen und (Pfad anpassen):
```powershell
schtasks /create /tn "MamiyaLensFinder" /tr "C:\Pfad\zu\mamiya-lens-finder\run.bat" /sc minute /mo 20
```
Das legt eine Aufgabe namens "MamiyaLensFinder" an, die `run.bat` alle 20
Minuten ausführt.

**Variante B – per grafischer Oberfläche:**
1. Start-Menü öffnen, "Aufgabenplanung" eintippen und öffnen.
2. Rechts auf **"Aufgabe erstellen…"** klicken (nicht "Einfache Aufgabe").
3. Reiter **Allgemein**: Namen vergeben, z.B. `MamiyaLensFinder`.
4. Reiter **Trigger** → **Neu…** → "Täglich" wählen, dann unten bei
   "Wiederholung der Aufgabe alle" `20 Minuten` einstellen, Dauer "Unbegrenzt".
5. Reiter **Aktionen** → **Neu…** → als Programm/Skript den vollständigen
   Pfad zu `run.bat` eintragen (z.B.
   `C:\Users\<DeinName>\Desktop\mamiya-lens-finder\run.bat`).
6. Mit OK bestätigen.

Zum Überprüfen: In der Aufgabenplanung die Aufgabe markieren und rechts auf
**"Ausführen"** klicken – dann kurz in Telegram/im Projektordner schauen,
ob sich etwas tut.

## Projektstruktur – welche Datei macht was?

| Datei | Rolle |
|---|---|
| [`main.py`](main.py) | Der "Dirigent": ruft alle anderen Module in der richtigen Reihenfolge auf (suchen → filtern → klassifizieren → benachrichtigen → merken). Guter Einstiegspunkt zum Lesen. |
| [`kleinanzeigen.py`](kleinanzeigen.py) | Holt die Suchergebnis- und Detailseiten von kleinanzeigen.de per HTTP und liest Titel, Preis, Ort und Beschreibung aus dem HTML heraus ("Scraping"). |
| [`classifier.py`](classifier.py) | Schickt Titel/Beschreibung/Preis an die `claude`-CLI und bekommt ein strukturiertes JSON-Ergebnis zurück (ist es ein Objektiv? Festbrennweite? welche Brennweite?). |
| [`notifier.py`](notifier.py) | Verschickt die Telegram-Nachricht bei einem Treffer. |
| [`state.py`](state.py) | Speichert, welche Anzeigen-IDs schon verarbeitet wurden, in `state/seen_ads.json`, damit nichts doppelt gemeldet wird. |
| [`config.py`](config.py) | Liest die `.env`-Datei ein und stellt alle Einstellungen zentral als Python-Variablen bereit. |
| [`run.sh`](run.sh) | 🍎 Wrapper-Skript für Cron: aktiviert die virtuelle Umgebung und startet `main.py`. |
| [`run.bat`](run.bat) | 🪟 Dasselbe für die Windows-Aufgabenplanung. |

Die Dateien sind bewusst klein und einzeln lesbar gehalten – jede macht
genau eine Sache. Das nennt man "Separation of Concerns" und macht es
leichter, das Projekt zu verstehen oder zu erweitern.

## Konfiguration (.env)

| Variable | Bedeutung |
|---|---|
| `SEARCH_QUERIES` | Kommagetrennte Suchbegriffe (Standard: `mamiya 645,mamiya sekor`) |
| `MIN_FOCAL_LENGTH_MM` / `MAX_FOCAL_LENGTH_MM` | Gesuchter Brennweitenbereich in mm |
| `CLAUDE_MODEL` | Modell-Alias für die Klassifikation, Standard `sonnet`; für geringere Nutzungslast z.B. `haiku` |
| `CLAUDE_CODE_OAUTH_TOKEN` | Von `claude setup-token` – ermöglicht Login ohne Browser für den automatisierten Hintergrund-Betrieb |
| `CLAUDE_BINARY` | Absoluter Pfad zur claude-CLI (`which claude` / `Get-Command claude`) – Cron/Aufgabenplanung haben ein sehr minimales `PATH` und finden `claude` sonst nicht |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Zugangsdaten für die Benachrichtigung |
| `REQUEST_DELAY_SECONDS` | Pause zwischen Requests an kleinanzeigen.de (Höflichkeit gegenüber dem Server) |

## Häufige Probleme (Troubleshooting)

- **`KeyError: 'TELEGRAM_BOT_TOKEN'`** — Die `.env`-Datei fehlt oder ein Feld
  ist leer. Prüfen, ob `.env` (nicht nur `.env.example`!) existiert und
  alle Pflichtfelder ausgefüllt sind.
- **`Not logged in · Please run /login`** — Der `CLAUDE_CODE_OAUTH_TOKEN`
  fehlt, ist abgelaufen, oder der Hintergrund-Prozess hat keinen Zugriff auf
  deine gespeicherte Anmeldung. Schritt 5 (`claude setup-token`) wiederholen.
- **`requests.exceptions.ReadTimeout`** — kleinanzeigen.de hat auf eine
  einzelne Anfrage nicht rechtzeitig geantwortet (transientes
  Netzwerk-Problem, kein Bug). Wird automatisch mit ein paar Wiederholungen
  abgefangen; bei Bedarf kann `REQUEST_DELAY_SECONDS` erhöht werden.
- **Telegram-Nachricht kommt nicht an** — meistens eine falsche/vertauschte
  `TELEGRAM_CHAT_ID`. Prüfen, ob dem Bot vorher wirklich eine Nachricht
  geschrieben wurde (Schritt 7), sonst liefert `getUpdates` nichts.
- **`claude: command not found` / `'claude' is not recognized`** im
  Cron-/Aufgabenplanungs-Lauf, obwohl es im Terminal funktioniert —
  klassisches PATH-Problem, siehe `CLAUDE_BINARY` oben.
- 🪟 **`... cannot be loaded because running scripts is disabled on this
  system`** beim Aktivieren des venv — siehe PowerShell-Hinweis in Schritt 2.
- 🪟 **`'python' is not recognized as an internal or external command`** —
  Python wurde ohne "Add python.exe to PATH" installiert. Python-Installer
  erneut ausführen, "Modify" wählen und das Häkchen nachträglich setzen,
  oder Python komplett neu installieren.

## Einstiegstipps für Programmier-/KI-Agenten-Neulinge

Falls du neu im Thema bist: Dieses Projekt ist bewusst
klein genug, um es komplett zu verstehen, aber realistisch genug, um
typische Bausteine eines KI-Agenten in freier Wildbahn zu zeigen. Ein paar
Ideen, wie man sich herantasten kann:

1. **Lies die Dateien in dieser Reihenfolge:** `main.py` →
   `kleinanzeigen.py` → `classifier.py` → `notifier.py` → `state.py`. So
   folgst du dem tatsächlichen Ablauf eines Durchlaufs statt alles auf
   einmal verstehen zu müssen.
2. **Verändere etwas Kleines und beobachte den Effekt.** Zum Beispiel den
   Brennweitenbereich in `.env` auf `50` bis `80` einschränken und
   `python main.py` erneut laufen lassen (dafür testweise eine Zeile aus
   `state/seen_ads.json` löschen, damit eine bekannte Anzeige erneut
   klassifiziert wird).
3. **Schau dir die Log-Ausgabe genau an.** Jede Zeile wie
   `Mamiya 645 Pro + Sekor C 80mm -> lens=False ... (Es wird ein
   komplettes Set verkauft...)` zeigt, *warum* die KI so entschieden hat –
   das ist der Kern dessen, was man "strukturierte KI-Klassifikation"
   nennt: Statt Fließtext-Antwort liefert das Modell exakt definierte
   Felder (`is_lens`, `focal_length_mm`, …), die ein Programm direkt
   weiterverarbeiten kann.
4. **Begriffe, die es sich zu googlen lohnt, wenn sie neu sind:**
   - *Web-Scraping* — Daten automatisiert aus Webseiten auslesen
   - *HTML-Parsing* (hier: BeautifulSoup) — HTML-Struktur durchsuchen statt
     Text stur zu zerschneiden
   - *Environment-Variablen / `.env`-Dateien* — Zugangsdaten getrennt vom
     Code halten
   - *JSON Schema / strukturierte Ausgabe* — einem LLM ein festes
     Antwortformat vorschreiben, statt Freitext zu parsen
   - *Cron-Jobs / Aufgabenplanung* — zeitgesteuerte, automatische
     Programmausführung
   - *venv / virtuelle Umgebungen* — Projekt-Abhängigkeiten isolieren
5. **Nächste eigene Erweiterung ausprobieren**, z.B.:
   - Eine zweite Kamera (z.B. Mamiya RB67) zusätzlich durchsuchen
   - Zoomobjektive nicht ausschließen, sondern separat kennzeichnen
   - Statt Telegram eine E-Mail verschicken
   - Gefundene Treffer zusätzlich in eine kleine Datei/Tabelle protokollieren
6. **Nichts kann hier kaputtgehen**, was sich nicht reparieren lässt – es
   ist ein privates Skript ohne Produktivbetrieb. Ausprobieren, Fehler
   provozieren, Fehlermeldungen lesen ist der schnellste Lernweg.

## Fairness & Spielregeln beim Scrapen

Dieses Projekt ruft ausschließlich normale, öffentlich zugängliche
HTML-Seiten ab, die laut `robots.txt` von kleinanzeigen.de nicht gesperrt
sind – kein Login-Umgehen, kein Umgehen von Bot-Schutz/CAPTCHAs, kein
Zugriff auf gesperrte API-Endpunkte. Das ist wichtig, wenn du das Prinzip
auf andere Webseiten übertragen willst: **Nicht jede Seite erlaubt
automatisierte Zugriffe**, und selbst wenn technisch möglich, kann es gegen
die Nutzungsbedingungen verstoßen. Vor dem Nachbauen für eine andere Seite
immer erst deren `robots.txt` und Nutzungsbedingungen prüfen.

Das Tool ist für den **privaten Eigenbedarf** gedacht. Bitte die
Anfragefrequenz moderat halten (alle 15–30 Minuten reicht für diesen
Zweck völlig) und nicht in großem Stil oder kommerziell einsetzen.

## Lizenz

[MIT](LICENSE) – frei verwendbar, veränderbar und weitergebbar, ohne Gewähr.
