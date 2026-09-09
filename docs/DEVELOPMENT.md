# Entwicklerdokumentation — ExifTool GUI

## Branch-Strategie

```
main          ← stabiler, deploybarer Stand
  └─ development  ← aktive Feature-Entwicklung
       └─ feature/xyz  ← optionale Feature-Branches
```

Pull Requests immer von `development` → `main` (nie direkt auf `main` pushen).

---

## Lokales Setup Web-UI

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
git checkout development

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# ExifTool installieren
sudo apt install libimage-exiftool-perl

export PHOTOS_DIR=/pfad/zu/deinen/fotos
uvicorn src.web.main:app --reload --port 8000
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
docker build -t sturmi77/exiftool-gui:0.1.0 .

# Lokal testen
PHOTOS_DIR=/pfad/zu/deinen/fotos \
  docker run --rm -p 8000:8000 -e PHOTOS_DIR=/photos \
  -v /pfad/zu/deinen/fotos:/photos \
  sturmi77/exiftool-gui:0.1.0
```

---

## Architektur (Web)

```
src/
├── web/
│   ├── main.py          # FastAPI-App, Routing & Templating
│   └── ...              # spätere Erweiterungen (APIs, Auth, etc.)
└── core/
    ├── exiftool.py      # Subprocess-Wrapper um ExifTool CLI
    └── utils.py         # Datum-Parsing, DMS-Konverter
```

Datenfluss (Web):

```
Browser ▷ FastAPI ▷ ExifToolWrapper ▷ Dateien unter PHOTOS_DIR
```

---

## Legacy Desktop-GUI

Die frühere Tkinter-GUI liegt unter `src/gui/` und `src/main.py`. Sie wird
nicht mehr aktiv weiterentwickelt, kann aber weiterhin genutzt werden.

Kurz-Setup:

```bash
python src/main.py
```

---

## Releases & Tags

Wir verwenden SemVer für Versionen:

- `v0.1.0`: erster Web-Release
- `v0.1.x`: Bugfixes
- `v0.2.0`: neue Features

Release-Ablauf:

1. Sicherstellen, dass `main` den gewünschten Stand enthält.
2. Version in Dockerfile/README/CHANGELOG prüfen/aktualisieren.
3. Tag setzen:

   ```bash
   git checkout main
   git pull
   git tag -a v0.1.0 -m "First public web release"
   git push origin v0.1.0
   ```

4. Auf GitHub unter **Releases** ein Release für `v0.1.0` erstellen.
5. Optional: den Docker-Publish-Workflow manuell auslösen.
