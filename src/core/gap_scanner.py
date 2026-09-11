"""Walk photo trees and fill the gap index via batched ExifTool reads."""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.core.exiftool import SCAN_TAGS, ExifToolWrapper
from src.core.gap_index import FileRow, GapIndex, folder_ancestors, root_of, utc_now
from src.core.utils import IMAGE_EXTS
from src.core.writable import is_writable_dir

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


class ScanInProgress(RuntimeError):
    """Raised when a scan is already running."""


def _to_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_str(value) -> Optional[str]:
    if value is None or value == "":
        return None
    return str(value)


def row_from_meta(
    relpath: str,
    mtime: float,
    size: int,
    writable: bool,
    meta: dict,
) -> FileRow:
    dto = _to_str(meta.get("DateTimeOriginal"))
    created = _to_str(meta.get("CreateDate"))
    return FileRow(
        relpath=relpath,
        root=root_of(relpath),
        mtime=mtime,
        size=size,
        has_exif=bool(meta.get("ExifByteOrder")),
        has_date=bool(dto or created),
        has_gps=(
            meta.get("GPSLatitude") not in (None, "")
            and meta.get("GPSLongitude") not in (None, "")
        ),
        has_make=bool(meta.get("Make")),
        datetime=dto or created,
        file_mtime=mtime,
        lat=_to_float(meta.get("GPSLatitude")),
        lon=_to_float(meta.get("GPSLongitude")),
        mime=_to_str(meta.get("MIMEType")),
        writable=writable,
        scanned_at=utc_now(),
    )


def walk_images(photos_dir: Path, extensions: set[str] = IMAGE_EXTS) -> list[Path]:
    """Return image files under photos_dir; skip hidden directories."""
    results: list[Path] = []
    if not photos_dir.is_dir():
        return results
    for dirpath, dirnames, filenames in os.walk(photos_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            if Path(name).suffix.lower() in extensions:
                results.append(Path(dirpath) / name)
    return results


def _eta_seconds(job: dict) -> int | None:
    if not job.get("running"):
        return None
    done = int(job.get("done") or 0)
    total = int(job.get("total") or 0)
    started = job.get("started_at")
    if done <= 0 or total <= done or not started:
        return None
    try:
        started_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        if started_dt.tzinfo is None:
            started_dt = started_dt.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - started_dt).total_seconds()
    except ValueError:
        return None
    if elapsed < 1:
        return None
    return max(0, int((total - done) * (elapsed / done)))


class GapScanner:
    def __init__(
        self,
        index: GapIndex,
        exiftool: ExifToolWrapper,
        photos_dir: Path,
        extensions: set[str] = IMAGE_EXTS,
        batch_size: int = BATCH_SIZE,
        writable_fn: Callable[[Path], bool] = is_writable_dir,
    ):
        self.index = index
        self.exiftool = exiftool
        self.photos_dir = photos_dir
        self.extensions = extensions
        self.batch_size = batch_size
        self.writable_fn = writable_fn
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._job_id: int | None = None

    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def status(self) -> dict:
        job = self.index.latest_job() or {}
        job["running"] = self.is_running()
        job["eta_seconds"] = _eta_seconds(job)
        return job

    def start(self) -> int:
        with self._lock:
            if self.is_running():
                raise ScanInProgress("Ein Scan läuft bereits.")
            self._cancel.clear()
            job_id = self.index.create_job()
            self._job_id = job_id
            self._thread = threading.Thread(
                target=self._run,
                args=(job_id,),
                name="gap-scanner",
                daemon=True,
            )
            self._thread.start()
            return job_id

    def cancel(self) -> bool:
        if not self.is_running():
            return False
        self._cancel.set()
        return True

    def _run(self, job_id: int) -> None:
        try:
            self._scan(job_id)
        except Exception as exc:
            logger.exception("Gap scan failed")
            self.index.update_job(
                job_id, status="error", error=str(exc), finished=True
            )

    def _scan(self, job_id: int) -> None:
        photos_dir = self.photos_dir.resolve()
        files = walk_images(photos_dir, self.extensions)
        total = len(files)
        self.index.update_job(job_id, total=total)

        known = self.index.known_fingerprints()
        writable_cache: dict[str, bool] = {}
        seen: set[str] = set()
        done = 0
        skipped = 0
        pending: list[tuple[Path, str, float, int, bool]] = []

        def folder_rel(path: Path) -> str:
            try:
                rel = path.resolve().relative_to(photos_dir).as_posix()
            except ValueError:
                return ""
            return "" if rel == "." else rel

        def writable_for(folder: Path) -> bool:
            key = folder_rel(folder)
            if key not in writable_cache:
                writable_cache[key] = self.writable_fn(folder)
            return writable_cache[key]

        def flush(batch: list[tuple[Path, str, float, int, bool]]) -> None:
            if not batch:
                return
            paths = [str(item[0]) for item in batch]
            metas = self.exiftool.read_metadata_batch(paths, SCAN_TAGS)
            by_src = {}
            for meta in metas:
                src = meta.get("SourceFile")
                if not src:
                    continue
                by_src[str(Path(src).resolve())] = meta
            rows = []
            for abs_path, relpath, mtime, size, writable in batch:
                meta = by_src.get(str(abs_path.resolve()), {})
                rows.append(row_from_meta(relpath, mtime, size, writable, meta))
            self.index.upsert_files(rows)

        for abs_path in files:
            if self._cancel.is_set():
                break
            try:
                relpath = abs_path.resolve().relative_to(photos_dir).as_posix()
            except ValueError:
                continue
            seen.add(relpath)
            try:
                stat = abs_path.stat()
            except OSError:
                done += 1
                continue
            mtime = stat.st_mtime
            size = stat.st_size
            writable = writable_for(abs_path.parent) and os.access(abs_path, os.W_OK)
            fingerprint = known.get(relpath)
            if fingerprint and fingerprint[0] == mtime and fingerprint[1] == size:
                if int(writable) != fingerprint[2]:
                    self.index.update_writable(relpath, writable)
                skipped += 1
                done += 1
                if done % 50 == 0:
                    self.index.update_job(job_id, done=done, skipped=skipped)
                continue
            pending.append((abs_path, relpath, mtime, size, writable))
            if len(pending) >= self.batch_size:
                flush(pending)
                done += len(pending)
                pending.clear()
                self.index.update_job(job_id, done=done, skipped=skipped)

        if not self._cancel.is_set() and pending:
            flush(pending)
            done += len(pending)
            pending.clear()

        # Ensure every walked folder (even empty) is in writable_cache
        if not self._cancel.is_set() and photos_dir.is_dir():
            writable_for(photos_dir)
            for dirpath, dirnames, _ in os.walk(photos_dir):
                if self._cancel.is_set():
                    break
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                writable_for(Path(dirpath))

        if not self._cancel.is_set():
            self.index.delete_missing(seen)

        self.index.rebuild_folders(writable_cache)
        status = "cancelled" if self._cancel.is_set() else "done"
        self.index.update_job(
            job_id,
            status=status,
            done=done,
            skipped=skipped,
            finished=True,
        )
