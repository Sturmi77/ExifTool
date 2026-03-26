# Dockhand Deployment Guide — ExifTool GUI

Dockhand ist ein selbst-gehostetes Docker-Management-Tool mit GitOps-Unterstützung,
Vulnerability-Scanning und Webhook-basiertem Auto-Sync.

> Weitere Infos zu Dockhand: https://dockhand.pro

---

## Voraussetzungen

- Dockhand installiert und erreichbar
- Docker Engine 20.20+ auf dem Zielhost
- Git-Zugang zum Repository (HTTPS oder SSH)
- Kein X11-Desktop nötig — GUI läuft via noVNC im Browser
- Kein manuelles Anlegen von Verzeichnissen nötig (außer PHOTOS_DIR)

---

## GUI-Zugriff via Browser

Die App läuft als Tkinter-Desktop-App in einem noVNC-Container.
Kein X11-Display auf dem Host notwendig.

```
http://<synology-ip>:6080
```

---

## Volumes

| Volume | Typ | Beschreibung |
|---|---|---|
| `${PHOTOS_DIR}:/photos` | Bind Mount | Deine Fotos vom Host |
| `exiftool_config` | Named Volume | App-Konfiguration, von Docker automatisch verwaltet |

Das Named Volume `exiftool_config` wird von Docker **automatisch angelegt** —
kein `mkdir` notwendig. Es liegt auf Synology unter:
```
/volume1/@docker/volumes/exiftool_config/_data
```

---

## Deployment via GitOps

### 1. Repository in Dockhand hinterlegen

1. Dockhand öffnen → **Settings → Git**
2. Repository hinzufügen:
   - URL: `https://github.com/Sturmi77/ExifTool.git`
   - Branch: `main`

### 2. Stack erstellen

1. **Stacks → Create → From Git**
2. Repository und Branch wählen
3. Compose-Datei: `compose.yaml` (wird automatisch erkannt)
4. Stack-Name: `exiftool`

### 3. Config Set anlegen

In Dockhand unter **Settings → Config Sets** — nur zwei Variablen nötig:

```
NOVNC_PORT=6080
PHOTOS_DIR=/volume1/photos
```

> `STACK_DATA_DIR` wird nicht mehr benötigt!

### 4. Webhook für Auto-Sync (optional)

1. Dockhand → Stack → **Webhook-URL kopieren**
2. GitHub → Repository → **Settings → Webhooks → Add webhook**
3. Payload URL: Dockhand Webhook-URL
4. Content type: `application/json`
5. Trigger: **Just the push event**

---

## Manuelles Deployment

```bash
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool
cp .env.example .env
# PHOTOS_DIR in .env anpassen
docker compose up --build
```

---

## Troubleshooting

### Bind mount failed
Nur `PHOTOS_DIR` ist ein Bind Mount — dieser Pfad muss auf dem Host existieren.
Alle anderen Volumes werden von Docker automatisch verwaltet.

```bash
# Prüfen ob Foto-Pfad existiert:
ls /volume1/photos
```

### GUI startet nicht (noVNC leer)
```bash
docker logs exiftool-gui
docker logs exiftool-novnc
```

### Named Volume Inhalt einsehen
```bash
ls /volume1/@docker/volumes/exiftool_config/_data
```

### Image neu bauen nach Code-Änderungen
In Dockhand: Stack → **Re-pull & Redeploy** oder:
```bash
docker compose up --build --force-recreate
```
