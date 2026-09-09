# Bedienungsanleitung — ExifTool GUI (Web)

## Starten

### Docker / Compose (empfohlen)

1. `.env` anlegen und `PHOTOS_DIR` konfigurieren:

   ```bash
   cp .env.example .env
   # PHOTOS_DIR auf dein Foto-Verzeichnis setzen
   ```

2. Stack starten:

   ```bash
   docker compose up --build -d
   ```

3. Weboberfläche aufrufen:

   ```text
   http://<host>:8000/
   ```

### Lokale Entwicklung

Siehe [README.md → Lokale Entwicklung (Web)](../README.md#lokale-entwicklung-web).

---

## 1. Ordner & Dateien

Links befindet sich der Ordner-Browser:

| Element | Beschreibung |
|---|---|
| Breadcrumb | Zeigt den aktuellen Pfad relativ zu `PHOTOS_DIR`, Klick auf Elemente navigiert nach oben. |
| Unterordnerliste | Klick auf einen Ordner springt in diesen Ordner. |
| Dateiliste | Alle unterstützten Bilddateien im aktuellen Ordner. |

- Klick auf einen Dateinamen lädt **rechts die Vorschau** (Thumbnail + EXIF-Tabelle).
- Checkboxen in der Liste bestimmen, auf welche Dateien Änderungen angewendet werden.

---

## 2. EXIF-Vorschau & Navigation

Rechts zeigt die **EXIF-Vorschau**:

- Oben: Dateiname der aktuell ausgewählten Datei.
- Darunter: Thumbnail der Datei.
- Buttons **Links drehen / Rechts drehen** drehen die Datei physisch.
- Buttons **Vorheriges / Nächstes** wechseln zur benachbarten Datei im aktuellen Ordner.
- EXIF-Tabelle listet die wichtigsten Metadaten (Datum, GPS, Kamera, Objektiv usw.).

Nach einem Drehvorgang lädt die Seite neu, sodass Thumbnail und EXIF-Daten garantiert aktuell sind.

---

## 3. Datum ändern

Im Bereich **Metadaten bearbeiten**:

- Feld **Datum & Zeit** ist ein `datetime-local` Eingabefeld.
- Beim Tippen oder Ändern wird automatisch ein EXIF-konformer String im Format
  `YYYY:MM:DD HH:MM:SS` erzeugt und beim Schreiben verwendet.

Du kannst entweder direkt tippen oder den Browser-Datepicker verwenden.

---

## 4. GPS-Koordinaten ändern

### Direkte Eingabe

- Felder **Lat** und **Lon** akzeptieren Dezimalgrad (z.B. `48.4010`, `16.1680`).

### Karte

- Die Karte zeigt die aktuelle Position des Markers.
- Klick in die Karte setzt den Marker.
- Drag & Drop des Markers verschiebt die Position.
- Die Felder **Lat/Lon** werden bei Änderungen automatisch aktualisiert.

### Ortssuche (Nominatim)

- Im Feld **Ort suchen** kannst du z.B. eine Adresse oder einen Ortsnamen eingeben.
- Klick auf **Suchen** nutzt OpenStreetMap Nominatim, um Koordinaten zu finden.
- Bei Erfolg wird der Marker versetzt, die Karte zentriert und Lat/Lon übernommen.

> Hinweis: Die Nutzung von Nominatim unterliegt den Nutzungsbedingungen der OSMF.

---

## 5. Änderungen schreiben

Unterhalb der Metadatenfelder befindet sich der Button:

| Button | Wirkung |
|---|---|
| **Auf ausgewählte Dateien anwenden** | Schreibt Datum/GPS auf alle markierten Dateien im aktuellen Ordner. |

Ablauf:

1. Dateien in der Liste per Checkbox markieren.
2. Datum und/oder GPS-Felder ausfüllen.
3. Button klicken.
4. Status-Meldung oben (grüner Kasten) bestätigt Erfolg oder zeigt einen Fehler.

ExifTool legt je nach Konfiguration interne Backups an oder überschreibt Dateien
in-place. Siehe `src/core/exiftool.py` für Details.

---

## 6. Desktop-GUI (Legacy)

Die ursprüngliche Tkinter-GUI wird weiter unterstützt, ist aber nicht mehr
Standard. Für die Bedienung siehe die frühere Dokumentation oder ältere Tags.

Kurzfassung:

```bash
python src/main.py
```

Voraussetzung: Die in `requirements.txt` aufgeführten Desktop-Pakete
(`tkintermapview`, `tkcalendar`, `geopy`) sind installiert.
