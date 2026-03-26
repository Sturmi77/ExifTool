# ─────────────────────────────────────────────────────────────────────
# ExifTool GUI — Docker Image
# Base: python:3.12-slim + ExifTool + Tkinter via X11 forwarding
# ─────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Sturmi77" \
      description="ExifTool GUI — EXIF date & location editor" \
      version="0.1.0"

# System dependencies:
#   exiftool        – Perl-based EXIF tool
#   tk + python3-tk – Tkinter GUI
#   libimage-exiftool-perl – ExifTool Perl library
#   xauth, x11-apps – X11 forwarding support
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

# Non-root user for security
RUN useradd -m -u 1000 exifuser
USER exifuser

# X11 display (overridable via env / docker-compose)
ENV DISPLAY=:0

CMD ["python", "src/main.py"]
