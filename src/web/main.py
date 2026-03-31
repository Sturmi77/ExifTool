from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.exiftool import ExifToolWrapper

import os

BASE_PHOTOS_DIR = Path(os.environ.get("PHOTOS_DIR", "/photos")).resolve()

app = FastAPI(title="ExifTool GUI (Web)")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

exiftool = ExifToolWrapper()


@app.get("/health", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok", "exiftool": exiftool.is_available()}


def _safe_join(base: Path, sub: str) -> Path:
    target = (base / sub).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Pfad liegt außerhalb des Foto-Verzeichnisses")
    return target


def _list_images(folder: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw",
            ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2"}
    files: list[Path] = []
    if not folder.is_dir():
        return files
    for entry in sorted(folder.iterdir()):
        if entry.is_file() and entry.suffix.lower() in exts:
            files.append(entry)
    return files


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, subdir: str = "", selected: Optional[str] = None, msg: str = ""):
    base = BASE_PHOTOS_DIR
    folder: Path
    try:
        folder = _safe_join(base, subdir) if subdir else base
    except ValueError:
        folder = base
        subdir = ""
        msg = "Ungültiger Unterordner – auf Basisverzeichnis zurückgesetzt."

    files = _list_images(folder)

    preview_file: Optional[Path] = None
    if selected:
        candidate = (folder / selected).resolve()
        if candidate.exists():
            preview_file = candidate
    if preview_file is None and files:
        preview_file = files[0]

    preview_meta: dict | None = None
    if preview_file is not None:
        try:
            preview_meta = exiftool.read_metadata_extended(str(preview_file))
        except Exception as e:
            preview_meta = {"error": str(e)}

    rel_files = [f.name for f in files]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "base_dir": str(base),
            "subdir": subdir,
            "folder": str(folder),
            "files": rel_files,
            "selected": preview_file.name if preview_file else "",
            "preview_file": preview_file.name if preview_file else "",
            "preview_meta": preview_meta or {},
            "message": msg,
        },
    )


@app.post("/apply", response_class=HTMLResponse)
async def apply_metadata(
    request: Request,
    subdir: str = Form(""),
    selected_files: List[str] = Form([]),
    exif_datetime: str = Form(""),
    lat: str = Form(""),
    lon: str = Form("")
):
    base = BASE_PHOTOS_DIR
    try:
        folder = _safe_join(base, subdir) if subdir else base
    except ValueError:
        folder = base
        subdir = ""

    if not selected_files:
        url = request.url_for("index")
        return RedirectResponse(url=f"{url}?subdir={subdir}&msg=Keine Dateien ausgewählt.", status_code=303)

    files: list[str] = []
    for name in selected_files:
        p = (folder / name).resolve()
        if str(p).startswith(str(folder)) and p.is_file():
            files.append(str(p))

    date = exif_datetime.strip() or None
    lat_val = lat.strip() or None
    lon_val = lon.strip() or None

    if not any([date, lat_val, lon_val]):
        url = request.url_for("index")
        return RedirectResponse(url=f"{url}?subdir={subdir}&msg=Keine Änderungen – bitte Datum oder GPS eingeben.", status_code=303)

    try:
        exiftool.write_metadata(files, date=date, lat=lat_val, lon=lon_val)
        msg = f"{len(files)} Datei(en) aktualisiert."
    except Exception as e:
        msg = f"Fehler beim Schreiben der Metadaten: {e}"

    url = request.url_for("index")
    return RedirectResponse(url=f"{url}?subdir={subdir}&msg={msg}", status_code=303)
