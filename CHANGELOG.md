# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei festgehalten.

## [0.1.0] – 2026-03-31

### Added
- Weboberfläche auf Basis FastAPI + Uvicorn (`src/web/main.py`).
- Ordner-Browser mit Breadcrumb, Unterordnerliste und Dateitabelle.
- Thumbnail-Vorschau + EXIF-Tabelle für ausgewählte Dateien.
- Kartenintegration (OpenStreetMap) mit Marker und Ortssuche (Nominatim).
- Drehen von Fotos (links/rechts) über die Weboberfläche.
- Dockerfile und Compose-Setup für NAS-/Home-Server-Deployment.

### Changed
- Tkinter-Desktop-GUI gilt als Legacy, Web-UI ist der empfohlene Einstiegspunkt.

### Fixed
- Sichereres Pfad-Handling über `_safe_join` zur Vermeidung von Directory Traversal.
