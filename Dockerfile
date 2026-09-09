# ─────────────────────────────────────────────────────────────────────
# ExifTool GUI — Docker Image
# Now serves a FastAPI-based web UI instead of a Tkinter desktop via noVNC.
# Base: python:3.12-slim + ExifTool CLI + FastAPI + Uvicorn
# ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Sturmi77" \
      description="ExifTool GUI — EXIF date & location editor (web UI)" \
      version="0.1.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        libimage-exiftool-perl \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application source (core logic + web modules)
COPY src/ ./src/
COPY templates ./templates
COPY static ./static

# UID 1026 = Michael auf Synology DS923+
RUN useradd -m -u 1026 -g users exifuser
USER exifuser

# FastAPI app entrypoint
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
