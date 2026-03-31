from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.exiftool import ExifToolWrapper

import io
import os

from PIL import Image, ImageOps

BASE_PHOTOS_DIR = Path(os.environ.get("PHOTOS_DIR", "/photos")).resolve()

app = FastAPI(title="ExifTool GUI (Web)")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

exiftool = ExifToolWrapper()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".raw",
              ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2"}


@app.get("/health", include_in_schema=False)
async def health() -> dict:
  return {"status": "ok", "exiftool": exiftool.is_available()}


def _safe_join(base: Path, sub: str) -> Path:
  target = (base / sub).resolve() if sub else base.resolve()
  if not str(target).startswith(str(base)):
    raise ValueError("Pfad liegt ausserhalb des Foto-Verzeichnisses")
  return target


def _rel(path: Path) -> str:
  try:
    return path.relative_to(BASE_PHOTOS_DIR).as_posix()
  except ValueError:
    return ""


def _list_subdirs(folder: Path) -> list:
  if not folder.is_dir():
    return []
  return sorted(
    e.name for e in folder.iterdir() if e.is_dir() and not e.name.startswith(".")
  )


def _list_images(folder: Path) -> list:
  files = []
  if not folder.is_dir():
    return files
  for entry in sorted(folder.iterdir()):
    if entry.is_file() and entry.suffix.lower() in IMAGE_EXTS:
      files.append(entry)
  return files


def _breadcrumb(subdir: str) -> list:
  crumbs = [{"label": "Basis", "path": ""}]
  parts = [p for p in subdir.split("/") if p]
  accumulated = ""
  for part in parts:
    accumulated = f"{accumulated}/{part}" if accumulated else part
    crumbs.append({"label": part, "path": accumulated})
  return crumbs


@app.get("/", response_class=HTMLResponse)
async def index(
  request: Request,
  subdir: str = "",
  selected: Optional[str] = None,
  msg: str = "",
):
  base = BASE_PHOTOS_DIR
  try:
    folder = _safe_join(base, subdir)
  except ValueError:
    folder = base
    subdir = ""
    msg = "Ungultiger Pfad - auf Basisverzeichnis zuruckgesetzt."

  subdirs = _list_subdirs(folder)
  files = _list_images(folder)
  breadcrumb = _breadcrumb(subdir)

  parent_subdir = None
  if subdir:
    parent_path = folder.parent
    if str(parent_path).startswith(str(base)):
      parent_subdir = _rel(parent_path)

  preview_file = None
  if selected:
    candidate = (folder / selected).resolve()
    if candidate.exists() and str(candidate).startswith(str(folder)):
      preview_file = candidate
  if preview_file is None and files:
    preview_file = files[0]

  preview_meta = None
  if preview_file is not None:
    try:
      preview_meta = exiftool.read_metadata_extended(str(preview_file))
    except Exception as e:
      preview_meta = {"error": str(e)}

  rel_files = [f.name for f in files]

  current_index = 0
  prev_file = None
  next_file = None
  if rel_files and preview_file and preview_file.name in rel_files:
    current_index = rel_files.index(preview_file.name)
    if current_index > 0:
      prev_file = rel_files[current_index - 1]
    if current_index < len(rel_files) - 1:
      next_file = rel_files[current_index + 1]

  return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={
      "base_dir": str(base),
      "subdir": subdir,
      "folder": str(folder),
      "subdirs": subdirs,
      "breadcrumb": breadcrumb,
      "parent_subdir": parent_subdir,
      "files": rel_files,
      "selected": preview_file.name if preview_file else "",
      "preview_file": preview_file.name if preview_file else "",
      "preview_meta": preview_meta or {},
      "prev_file": prev_file,
      "next_file": next_file,
      "message": msg,
    },
  )


@app.get("/browse", response_class=JSONResponse)
async def browse(subdir: str = ""):
  base = BASE_PHOTOS_DIR
  try:
    folder = _safe_join(base, subdir)
  except ValueError:
    return JSONResponse({"error": "invalid path"}, status_code=400)
  return {
    "subdir": _rel(folder),
    "subdirs": _list_subdirs(folder),
    "files": [f.name for f in _list_images(folder)],
  }


@app.get("/thumb")
async def thumb(subdir: str, file: str):
  """Return a JPEG thumbnail for the given file."""
  base = BASE_PHOTOS_DIR
  folder = _safe_join(base, subdir)
  path = (folder / file).resolve()
  if not path.is_file() or not str(path).startswith(str(folder)):
    return JSONResponse({"error": "not found"}, status_code=404)

  try:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img.thumbnail((800, 800))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
  except Exception as exc:
    return JSONResponse({"error": f"thumb error: {exc}"}, status_code=500)

  return StreamingResponse(buf, media_type="image/jpeg")


@app.post("/rotate", response_class=JSONResponse)
async def rotate(
  subdir: str = Form(""),
  file: str = Form(""),
  direction: str = Form("cw"),  # cw / ccw
):
  base = BASE_PHOTOS_DIR
  folder = _safe_join(base, subdir)
  path = (folder / file).resolve()
  if not path.is_file() or not str(path).startswith(str(folder)):
    return JSONResponse({"error": "not found"}, status_code=404)

  suffix = path.suffix.lower()
  allowed = {".jpg", ".jpeg", ".jpe", ".jfif", ".heic", ".heif"}
  if suffix not in allowed:
    return JSONResponse(
      {"error": f"rotate not supported for format {suffix}"},
      status_code=400,
    )

  angle = -90 if direction == "cw" else 90

  try:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.rotate(angle, expand=True)
    img.save(path, quality=90)
  except Exception as exc:
    return JSONResponse({"error": f"rotate error: {exc}"}, status_code=500)

  return {"ok": True}


@app.post("/apply", response_class=HTMLResponse)
async def apply_metadata(
  request: Request,
  subdir: str = Form(""),
  selected_files: List[str] = Form([]),
  exif_datetime: str = Form(""),
  lat: str = Form(""),
  lon: str = Form(""),
):
  base = BASE_PHOTOS_DIR
  try:
    folder = _safe_join(base, subdir)
  except ValueError:
    folder = base
    subdir = ""

  if not selected_files:
    url = request.url_for("index")
    return RedirectResponse(
      url=f"{url}?subdir={subdir}&msg=Keine Dateien ausgewahlt.", status_code=303
    )

  files = []
  for name in selected_files:
    p = (folder / name).resolve()
    if str(p).startswith(str(folder)) and p.is_file():
      files.append(str(p))

  date = exif_datetime.strip() or None
  lat_val = lat.strip() or None
  lon_val = lon.strip() or None

  if not any([date, lat_val, lon_val]):
    url = request.url_for("index")
    return RedirectResponse(
      url=f"{url}?subdir={subdir}&msg=Keine Anderungen - bitte Datum oder GPS eingeben.",
      status_code=303,
    )

  try:
    exiftool.write_metadata(files, date=date, lat=lat_val, lon=lon_val)
    msg = f"{len(files)} Datei(en) aktualisiert."
  except Exception as e:
    msg = f"Fehler beim Schreiben der Metadaten: {e}"

  url = request.url_for("index")
  return RedirectResponse(url=f"{url}?subdir={subdir}&msg={msg}", status_code=303)
