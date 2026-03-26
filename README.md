# ExifTool GUI

> A lightweight Python/Tkinter GUI to quickly edit **date** and **GPS location** metadata of photos — powered by [ExifTool by Phil Harvey](https://exiftool.org/).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![ExifTool](https://img.shields.io/badge/Requires-ExifTool-green.svg)](https://exiftool.org/)

---

## Features

| Feature | Details |
|---|---|
| 📁 Ordner & Einzeldateien | Ordner (inkl. Unterordner) oder einzelne Bilder wählen |
| 📅 Datepicker | Kalender + Uhrzeit-Spinboxes (tkcalendar), direkteingabe immer möglich |
| 🗺 Kartenauswahl | Interaktive OpenStreetMap-Karte, Adresssuche, Reverse-Geocoding |
| 📎 Metadaten kopieren | Datum & GPS aus Referenzbild in andere Bilder übertragen |
| 🔍 EXIF-Vorschau | Thumbnail + vollständige EXIF-Tabelle für ausgewähltes Bild |
| 💾 Automatische Sicherung | ExifTool erstellt `_original`-Backups vor Änderungen |
| 🐳 Docker-Support | Image + docker-compose für Dockge/Dockhand-Deployment |

---

## Voraussetzungen

- Python 3.10+
- [ExifTool](https://exiftool.org/) im System-PATH
- Python-Pakete: siehe `requirements.txt`

```bash
# ExifTool installieren
sudo apt install libimage-exiftool-perl   # Debian/Ubuntu
brew install exiftool                      # macOS
# Windows: https://exiftool.org/ (installer)
```

---

## Lokale Installation

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
pip install -r requirements.txt
python src/main.py
```

---

## Docker / Dockge Deployment

### Voraussetzung: X11 Forwarding

Da die App eine GUI hat, muss der X11-Socket des Hosts in den Container gemountet werden.

```bash
# Einmalig auf dem Host ausführen:
xhost +local:docker
```

### .env anlegen

```bash
cp .env.example .env
# PHOTOS_DIR anpassen – z.B. /mnt/nas/fotos
```

### Starten mit docker compose

```bash
docker compose up --build
```

### Starten über Dockge

1. `docker-compose.yml` in Dockge importieren
2. Umgebungsvariable `PHOTOS_DIR` auf dein Foto-Verzeichnis setzen (z.B. NAS-Mount)
3. Stack starten — das GUI öffnet sich via X11 auf dem Host-Desktop

> **Hinweis:** Auf einem Headless-Server (z.B. Hetzner) wird zusätzlich ein VNC-Server oder X11-Forwarding über SSH (`ssh -X`) benötigt.

---

## Projektstruktur

```
ExifTool/
├── src/
│   ├── main.py                  # Einstiegspunkt
│   ├── gui/
│   │   ├── app.py               # Hauptfenster (1100×720)
│   │   ├── folder_panel.py      # Ordner + Einzeldatei-Auswahl
│   │   ├── edit_panel.py        # Datum/GPS + Metadaten-Kopieren
│   │   ├── date_picker.py       # Kalender-Dialog
│   │   ├── map_picker.py        # OpenStreetMap-Dialog
│   │   └── exif_preview.py      # EXIF-Vorschau + Thumbnail
│   └── core/
│       ├── exiftool.py          # ExifTool-Wrapper (subprocess)
│       └── utils.py             # Datums-/Koordinaten-Helfer
├── tests/
│   └── test_exiftool.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── .gitignore
└── LICENSE (MIT)
```

---

## Python-Abhängigkeiten

| Paket | Zweck | Optional |
|---|---|---|
| `tkintermapview` | OpenStreetMap-Karte im Kartendialog | Ja (Karte deaktiviert ohne) |
| `tkcalendar` | Kalender-Widget im Datepicker | Ja (Fallback: Texteingabe) |
| `Pillow` | Thumbnail-Vorschau im EXIF-Panel | Ja (kein Bild ohne) |
| `geopy` | Reverse-Geocoding (Adresse aus GPS) | Ja |
| `pytest` | Tests | Dev only |

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE)

Dieses Projekt verwendet [ExifTool](https://exiftool.org/) von Phil Harvey (Perl Artistic License / GPL). ExifTool wird nicht gebundled, sondern als Systemtool über subprocess aufgerufen.

---

## Branch-Strategie

| Branch | Zweck |
|---|---|
| `main` | Stabiler Release-Stand |
| `development` | Aktive Entwicklung, neues Feature-Merging |
