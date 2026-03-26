# Bedienungsanleitung — ExifTool GUI

## Starten

```bash
python src/main.py
```

---

## 1. Bilder laden

Oben in der Leiste **"Dateien laden"** gibt es zwei Möglichkeiten:

| Aktion | Beschreibung |
|---|---|
| **📁 Ordner wählen** | Scannt alle Bilder im Ordner. Mit ☑ "Unterordner einbeziehen" auch rekursiv. |
| **🖼 Dateien wählen** | Einzelne oder mehrere Bilder per Dateidialog auswählen (Mehrfachauswahl möglich). |
| **✖ Liste leeren** | Dateiliste zurücksetzen. |

---

## 2. EXIF-Vorschau

Beim Klick auf eine Datei in der Liste erscheint rechts automatisch:
- **Thumbnail** des Bildes (benötigt `Pillow`)
- **Metadaten-Tabelle**: Datum, GPS, Kamera, Objektiv, ISO, Blende, etc.

Die Werte sind per Maus kopierbar.

---

## 3. Datum ändern

- Direkt ins Feld `Datum & Zeit` tippen (Format `YYYY:MM:DD HH:MM:SS`)
- Oder 📅 **Kalender**-Button → Monat klicken + Uhrzeit einstellen
  - Schnellwahl: **Jetzt**, **Mitternacht**, **Mittag**
  - Live-Vorschau des EXIF-Strings

---

## 4. GPS-Koordinaten ändern

- Koordinaten direkt in die Felder **Lat / Lon** tippen (Dezimalgrad, z.B. `48.401`, `16.168`)
- Oder 🗺 **Karte öffnen** (benötigt `tkintermapview`):
  - Auf die Karte klicken um Marker zu setzen
  - Adresse suchen (OpenStreetMap Nominatim)
  - 📍 **Adresse anzeigen** für Reverse-Geocoding
  - **✔ Koordinaten übernehmen** überträgt den Marker in die Felder

---

## 5. Metadaten von Referenzdatei kopieren

Ideal wenn mehrere Fotos vom gleichen Ort/Zeitpunkt stammen:

1. **📎 Referenzdatei wählen** → ein Foto mit den gewünschten EXIF-Daten
2. Vorschau zeigt Datum & GPS der Referenz
3. Checkboxen **Datum** / **GPS** nach Bedarf aktivieren
4. **→ In Felder übernehmen** → Werte werden in die Eingabefelder übertragen
5. Dateien auswählen + **Auf Auswahl/Alle anwenden**

---

## 6. Änderungen schreiben

| Button | Wirkung |
|---|---|
| **Auf Auswahl anwenden** | Schreibt nur auf markierte Dateien (Strg+Klick / Shift für Mehrfach) |
| **Auf alle Dateien anwenden** | Schreibt auf alle Dateien in der Liste |

> ⚠️ ExifTool legt automatisch Sicherungskopien als `dateiname_original` an.
> Um Backups zu deaktivieren, `exiftool.py` anpassen (`-overwrite_original` statt `-overwrite_original_in_place`).

---

## Docker / Dockge

Siehe [README.md → Docker Deployment](../README.md#docker--dockge-deployment).
