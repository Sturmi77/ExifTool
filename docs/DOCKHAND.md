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

---

## Wichtig: Keine Leerzeichen in Docker-Pfaden (Synology)

Docker auf Synology DSM unterstützt **keine Leerzeichen in Bind-Mount-Pfaden**.
Dockhand legt Stacks standardmäßig unter einem Pfad mit Leerzeichen ab
(`/volume1/docker/dockhand/stacks/Synolgy DS923+/...`).

**Lösung: Symlink ohne Leerzeichen anlegen (einmalig per SSH):**

```bash
ln -s "/volume1/docker/dockhand/stacks/Synolgy DS923+/exiftool" /volume1/docker/exiftool-gui
mkdir -p /volume1/docker/exiftool-gui/data
```

Danach im Config Set den Symlink-Pfad verwenden:
```
STACK_DATA_DIR=/volume1/docker/exiftool-gui/data
```

---

## GUI-Zugriff via Browser

Die App läuft als Tkinter-Desktop-App in einem noVNC-Container.
Kein X11-Display auf dem Host notwendig.

```
http://<synology-ip>:6080
```

---

## Deployment via GitOps

### 1. Repository in Dockhand hinterlegen

1. Dockhand öffnen → **Settings → Git**
2. Repository hinzufügen:
   - URL: `https://github.com/Sturmi77/ExifTool.git`
   - Branch: `main` (stabil)

### 2. Stack erstellen

1. **Stacks → Create → From Git**
2. Repository und Branch wählen
3. Compose-Datei: `compose.yaml` (wird automatisch erkannt)
4. Stack-Name: `exiftool`

### 3. Config Set anlegen

In Dockhand unter **Settings → Config Sets**:

```
NOVNC_PORT=6080
PHOTOS_DIR=/volume1/photos
STACK_DATA_DIR=/volume1/docker/exiftool-gui/data
```

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
# .env anpassen
docker compose up --build
```

---

## Vulnerability Scanning

Das Label in `compose.yaml` steuert die Update-Strategie:

```yaml
labels:
  - "dockhand.update.vulnerability-criteria=critical"
```

Mögliche Werte: `never`, `any`, `critical-or-high`, `critical`, `more-than-current`

---

## Fotos-Verzeichnis

| Setup | PHOTOS_DIR |
|---|---|
| Synology Standard | `/volume1/photos` |
| Eigener Ordner | `/volume1/homes/admin/Photos` |
| NAS-Mount auf Linux | `/mnt/nas/fotos` |

---

## Troubleshooting

### Bind mount failed: path does not exist
```bash
# Symlink und Datenordner anlegen:
ln -s "/volume1/docker/dockhand/stacks/Synolgy DS923+/exiftool" /volume1/docker/exiftool-gui
mkdir -p /volume1/docker/exiftool-gui/data
```

### Bind mount failed: spaces in path
Docker unterstützt keine Leerzeichen in Bind-Mount-Pfaden.
Symlink-Lösung wie oben verwenden.

### GUI startet nicht (noVNC leer)
```bash
# Container-Logs prüfen:
docker logs exiftool-gui
docker logs exiftool-novnc
```

### Image neu bauen nach Code-Änderungen
In Dockhand: Stack → **Re-pull & Redeploy** oder:
```bash
docker compose up --build --force-recreate
```
