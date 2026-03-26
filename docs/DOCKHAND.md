# Dockhand Deployment Guide — ExifTool GUI

Dockhand ist ein selbst-gehostetes Docker-Management-Tool mit GitOps-Unterstützung,
Vulnerability-Scanning und Webhook-basiertem Auto-Sync.
Dieses Dokument beschreibt das Deployment der ExifTool GUI via Dockhand.

> Weitere Infos zu Dockhand: https://dockhand.pro

---

## Voraussetzungen

- Dockhand installiert und erreichbar
- Docker Engine 20.20+ auf dem Zielhost
- X11-Display auf dem Host (GUI-App)
- Git-Zugang zum Repository (HTTPS oder SSH)

---

## X11 einrichten (einmalig)

Da ExifTool GUI eine Desktop-Anwendung ist, muss der X11-Socket des Hosts
in den Container freigegeben werden:

```bash
# Einmalig auf dem Host ausführen (bei jedem Reboot wiederholen oder in /etc/rc.local):
xhost +local:docker
```

Für einen permanenten Eintrag in die Autostart-Konfiguration:
```bash
echo 'xhost +local:docker' >> ~/.profile
```

---

## Datenverzeichnis anlegen

```bash
mkdir -p /opt/dockhand/stacks/exiftool-gui/data
```

> Dockhand verwendet **matching paths**: Der Volume-Pfad im Container muss
> identisch mit dem Host-Pfad sein. Daher absoluter Pfad statt relativer.

---

## Deployment via GitOps (empfohlen)

### 1. Repository in Dockhand hinterlegen

1. Dockhand öffnen → **Settings → Git**
2. Repository hinzufügen:
   - URL: `https://github.com/Sturmi77/ExifTool.git`
   - Branch: `development` (für aktive Entwicklung) oder `main` (stabil)
   - Auth: HTTPS ohne Token (public repo) oder SSH-Key

### 2. Stack erstellen

1. **Stacks → Create → From Git**
2. Repository und Branch wählen
3. Compose-Datei: `compose.yaml` (wird automatisch erkannt)
4. Stack-Name: `exiftool-gui`

### 3. Config Set anlegen (statt .env-Datei)

In Dockhand unter **Settings → Config Sets** ein neues Config Set erstellen:

```
DISPLAY=:0
PHOTOS_DIR=/mnt/nas/fotos
STACK_DATA_DIR=/opt/dockhand/stacks/exiftool-gui/data
```

Das Config Set beim Stack-Deployment auswählen — so bleiben keine Secrets im Git-Repo.

### 4. Webhook für Auto-Sync einrichten (optional)

1. Dockhand → Stack → **Webhook-URL kopieren**
2. GitHub → Repository → **Settings → Webhooks → Add webhook**
3. Payload URL: Dockhand Webhook-URL einfügen
4. Content type: `application/json`
5. Trigger: **Just the push event**

Ab jetzt deployed Dockhand automatisch bei jedem Push auf den konfigurierten Branch.

---

## Manuelles Deployment (ohne GitOps)

```bash
# Repository klonen
git clone https://github.com/Sturmi77/ExifTool.git
cd ExifTool

# Umgebungsvariablen setzen
cp .env.example .env
nano .env   # PHOTOS_DIR und STACK_DATA_DIR anpassen

# Datenverzeichnis erstellen
mkdir -p /opt/dockhand/stacks/exiftool-gui/data

# X11 freigeben
xhost +local:docker

# Stack starten
docker compose up --build
```

Oder in Dockhand: **Stacks → Create → Editor** → Inhalt von `compose.yaml` einfügen.

---

## Vulnerability Scanning

Dockhand scannt das Image automatisch mit Grype/Trivy.
Das Label in `compose.yaml` steuert die Update-Strategie:

```yaml
labels:
  - "dockhand.update.vulnerability-criteria=critical"
```

Mögliche Werte: `never`, `any`, `critical-or-high`, `critical`, `more-than-current`

---

## Fotos-Verzeichnis konfigurieren

Der Container mountet `PHOTOS_DIR` als `/photos`.
Innerhalb der GUI kann dieser Pfad als Startordner gewählt werden.

| Setup | PHOTOS_DIR-Wert |
|---|---|
| Linux Desktop | `/home/user/Pictures` |
| Synology NAS | `/volume1/photos` |
| NAS-Mount auf Linux | `/mnt/nas/fotos` |
| Benutzerdefiniert | Beliebiger absoluter Pfad |

---

## Troubleshooting

### GUI startet nicht (X11-Fehler)
```bash
# Prüfen ob xhost gesetzt ist:
xhost
# Falls nicht:
xhost +local:docker
# DISPLAY-Variable prüfen:
echo $DISPLAY
```

### Volume-Pfad-Fehler in Dockhand
```bash
# Verzeichnis muss auf dem Host existieren:
mkdir -p /opt/dockhand/stacks/exiftool-gui/data
# Berechtigungen:
chown 1000:1000 /opt/dockhand/stacks/exiftool-gui/data
```

### Image neu bauen nach Code-Änderungen
In Dockhand: Stack → **Re-pull & Redeploy** oder:
```bash
docker compose up --build --force-recreate
```
