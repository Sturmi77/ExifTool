# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei festgehalten.

## [0.2.0] – 2026-04-16

### Added
- Anzahl ausgewählter Dateien wird live im Metadaten-Bereich angezeigt (Issue #6).
- Apply-Button wird deaktiviert wenn keine Dateien ausgewählt sind.
- Dateiliste auf fixe Höhe (420px) begrenzt mit internem Scroll (Issue #7).
- Tabellenkopf bleibt beim Scrollen sichtbar (sticky header).
- Ausgewählte Zeile scrollt automatisch in den sichtbaren Bereich.

### Fixed
- URL-Encoding für Dateinamen und Unterordner mit Sonderzeichen (+, &, #, Leerzeichen) (Issue #5).
- HTML-Escaping aller onclick-Attribute zur XSS-Absicherung.
- `urllib.parse.unquote_plus` im /thumb-Endpoint gegen doppeltes Encoding.

### Changed
- GitHub Actions Workflow: automatischer Docker-Build + Push bei `v*.*.*`-Tags zusätzlich zu manuellem Dispatch.
- Docker-Image erhält nun zusätzlich einen semantischen Versions-Tag (z.B. `v0.2.0`).

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
