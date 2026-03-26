# ─────────────────────────────────────────────────────────────────────
# ExifTool GUI — Docker Image
# Base: python:3.12-slim + ExifTool + Tkinter via noVNC
# User: exifuser mit UID 1026 = Michael auf Synology DS923+
# ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Sturmi77" \
      description="ExifTool GUI — EXIF date & location editor" \
      version="0.1.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libimage-exiftool-perl \
        python3-tk \
        tk \
        xauth \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxtst6 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# UID 1026 = Michael auf Synology DS923+
# Muss mit dem Host-User übereinstimmen damit Datei-Zugriff funktioniert.
# Für andere Systeme: UID im Dockerfile oder via --user Flag anpassen.
RUN useradd -m -u 1026 -g users exifuser
USER exifuser

ENV DISPLAY=:0

CMD ["python", "src/main.py"]
