# Entwicklerdokumentation — ExifTool GUI

## Branch-Strategie

```
main          ← stabiler, deploybarer Stand
  └─ development  ← aktive Feature-Entwicklung
       └─ feature/xyz  ← optionale Feature-Branches
```

Pull Requests immer von `development` → `main` (nie direkt auf `main` pushen).

---

## Lokales Setup

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
git checkout development

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# ExifTool installieren
sudo apt install libimage-exiftool-perl

python src/main.py
```

---

## Tests ausführen

```bash
pytest tests/ -v
```

> `test_exiftool_available` wird übersprungen wenn ExifTool nicht installiert ist.

---

## Docker Image bauen

```bash
# Bauen
docker build -t sturmi77/exiftool-gui:latest .

# Lokal testen (Linux mit X11)
xhost +local:docker
docker compose up
```

---

## Architektur

```
src/
├── main.py              # Einstiegspunkt – startet App()
├── gui/
│   ├── app.py           # Hauptfenster, Layout (PanedWindow-artig)
│   ├── folder_panel.py  # Ordner-/Dateiauswahl, Scan-Logik
│   ├── edit_panel.py    # Eingabefelder, Buttons, Referenz-Kopie
│   ├── date_picker.py   # Modaler Dialog: tkcalendar + Spinboxes
│   ├── map_picker.py    # Modaler Dialog: TkinterMapView + Geocoding
│   └── exif_preview.py  # Seitenpanel: Thumbnail + EXIF-Tag-Tabelle
└── core/
    ├── exiftool.py      # Subprocess-Wrapper um ExifTool CLI
    └── utils.py         # Datum-Parsing, DMS-Konverter
```

### Datenfluss

```
FolderPanel ──on_files_changed─► App._on_files_changed ─► Listbox befüllen
Listbox     ──<<ListboxSelect>>─► App._on_file_select   ─► ExifPreviewPanel.load_file()
EditPanel   ──_apply()───────► ExifToolWrapper.write_metadata()
EditPanel   ──_copy_from_reference()► ExifToolWrapper.read_metadata_extended()
```

---

## Neue Features hinzufügen

1. Branch von `development` erstellen: `git checkout -b feature/mein-feature`
2. Implementieren, committen
3. Pull Request → `development`
4. Nach Review: Merge in `development`, später Release-PR → `main`
