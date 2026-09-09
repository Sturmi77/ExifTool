# ExifTool GUI

> Webbasierte Oberfläche zum schnellen Bearbeiten von **Datum** und **GPS-Position** in Fotometadaten – powered by [ExifTool von Phil Harvey](https://exiftool.org/).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![ExifTool](https://img.shields.io/badge/Requires-ExifTool-green.svg)](https://exiftool.org/)

---

## Features (Web UI)

| Feature | Details |
|---|---|
| 📁 Ordner-Browser | Start im konfigurierten `PHOTOS_DIR`, Navigation per Breadcrumb & Unterordnerliste |
| 🖼 Thumbnail-Vorschau | Rechte Seite zeigt Vorschaubild + EXIF-Tabelle für die aktuelle Datei |
| 🔄 Drehen & Speichern | Fotos direkt im Browser links/rechts drehen und in neuer Orientierung speichern |
| 📅 EXIF-Datum setzen | Datum/Zeit via `datetime-local` Eingabe, automatischer EXIF-String (`YYYY:MM:DD HH:MM:SS`) |
| 🗺 Karte & Ortssuche | OpenStreetMap-Karte, Marker per Klick verschiebbar, Ortssuche (Nominatim) mit Übernahme in Lat/Lon |
| 📍 GPS schreiben | GPS-Koordinaten für mehrere ausgewählte Dateien in einem Rutsch setzen |
| 🐳 Docker-optimiert | Schlankes Image auf Basis `python:3.12-slim`, ideal für NAS / Home-Server |

Die frühere Desktop-GUI auf Basis Tkinter existiert weiterhin im Code, der Fokus liegt aber auf der Weboberfläche.

---

## Voraussetzungen

- [ExifTool](https://exiftool.org/) im Container/Host installiert
- Docker / Docker Compose (für Deployment empfohlen)
- Optional für lokale Entwicklung: Python 3.12+

ExifTool wird **nicht** gebundled, sondern als externes CLI-Tool über `subprocess` aufgerufen.

---

## Quickstart (Docker, empfohlen)

### 1. Repo klonen

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
```

### 2. `.env` anlegen und `PHOTOS_DIR` setzen

```bash
cp .env.example .env
# PHOTOS_DIR in .env anpassen – z.B. auf dein Fotoverzeichnis
# Beispiel Synology: /volume1/photo oder /volume1/homes/Michael
```

`PHOTOS_DIR` definiert das Wurzelverzeichnis, in dem der Ordner-Browser startet. Navigation darüber hinaus ist aus Sicherheitsgründen gesperrt.

### 3. Mit Docker Compose starten

```bash
docker compose up --build -d
```

Die Weboberfläche ist danach unter:

```text
http://<host>:8000/
```

oder – je nach Setup – über den konfigurierten Reverse-Proxy/NoVNC-Port erreichbar.

---

## Web-Bedienung (Kurzüberblick)

Details siehe [docs/USAGE.md](docs/USAGE.md).

1. **Ordner öffnen**: Links im Ordner-Browser einen Ordner auswählen (Startpunkt = `PHOTOS_DIR`).
2. **Datei wählen**: Klick auf einen Dateinamen lädt rechts die Vorschau (Thumbnail + EXIF).
3. **EXIF-Datum setzen**: Datum/Zeit mit dem Picker eintragen – der EXIF-String wird automatisch generiert.
4. **GPS setzen**:
   - Direkt Lat/Lon eintippen oder
   - Ort über das Suchfeld finden (Nominatim) oder
   - Marker in der Karte verschieben.
5. **Auf Auswahl anwenden**: Checkboxen in der Dateiliste setzen und Änderungen schreiben.
6. **Drehen**: Rechts in der Vorschau mit „Links drehen“ / „Rechts drehen“ die Datei physisch rotieren.

---

## Lokale Entwicklung (Web)

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# ExifTool installieren (Host)
sudo apt install libimage-exiftool-perl   # Debian/Ubuntu
# oder siehe https://exiftool.org/ für andere Plattformen

export PHOTOS_DIR=/pfad/zu/deinen/fotos
uvicorn src.web.main:app --reload --port 8000
```

Danach ist die App unter `http://localhost:8000/` erreichbar.

---

## Legacy: Desktop-GUI (Tkinter)

Die ursprüngliche Tkinter-Anwendung ist weiterhin im Repository enthalten, wird aber nicht mehr aktiv weiterentwickelt.

- Einstiegspunkt: `src/main.py`
- Module unter `src/gui/` (FolderPanel, EditPanel, DatePicker, MapPicker, ExifPreview)

Für reine Desktop-Nutzung kannst du lokal weiterhin:

```bash
python src/main.py
```

verwenden, solange die Python-Abhängigkeiten (`tkintermapview`, `tkcalendar`, `geopy`) installiert sind.

---

## Dokumentation

- **Benutzung (Web)**: [docs/USAGE.md](docs/USAGE.md)
- **Entwicklung / Architektur**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Dockhand/Dockge-spezifisches Deployment**: [docs/DOCKHAND.md](docs/DOCKHAND.md)

---

## Versionierung & Releases

- Branch `main`: stabiler, releasefähiger Stand.
- Branch `development`: aktive Entwicklung, Feature-Branches landen hier.

Geplante SemVer-Versionierung:

- `v0.1.0` – erster öffentlicher Web-Release (aktueller Stand)
- `v0.1.x` – Bugfixes und kleinere Verbesserungen
- `v0.2.0` – größere Feature-Updates

Releases werden über Git-Tags und GitHub Releases verwaltet (siehe [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)).

---

## Lizenz & Attribution

- **Code** dieses Projekts: [MIT License](LICENSE).
- **ExifTool**: © Phil Harvey – siehe [exiftool.org](https://exiftool.org/).
- **OpenStreetMap & Nominatim**: Kartendaten & Geocoding von [OpenStreetMap-Mitwirkenden](https://www.openstreetmap.org/copyright).
  - Bitte beachte die Nutzungsbedingungen von Nominatim: <https://operations.osmfoundation.org/policies/nominatim/>.
