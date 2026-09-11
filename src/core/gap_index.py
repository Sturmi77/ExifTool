"""SQLite index of photo metadata gaps."""
from __future__ import annotations

import os
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


def _ensure_writable_dir(path: Path) -> Path:
    """Return *path* if it is writable, otherwise a temp fallback."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=path):
            return path
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "exiftool-gui"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def default_db_path() -> Path:
    """Store the index next to app config, never inside the photo tree."""
    base = os.environ.get("EXIFTOOL_CONFIG_DIR")
    if base:
        preferred = Path(base)
    else:
        preferred = Path.home() / ".config" / "exiftool-gui"
    return _ensure_writable_dir(preferred) / "gaps.sqlite"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def folder_ancestors(file_relpath: str) -> list[str]:
    """Folder relpaths from the file's directory up to the photo root ('')."""
    parent = str(Path(file_relpath).parent).replace("\\", "/")
    if parent == ".":
        parent = ""
    chain: list[str] = []
    while True:
        chain.append(parent)
        if parent == "":
            break
        parent = str(Path(parent).parent).replace("\\", "/")
        if parent == ".":
            parent = ""
    return chain


def root_of(relpath: str) -> str:
    if not relpath:
        return ""
    return relpath.split("/", 1)[0]


def _like_escape(value: str) -> str:
    """Escape LIKE wildcards so folder names with _ or % match literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def editor_parts(file_relpath: str) -> tuple[str, str]:
    """Split an indexed file path into editor subdir + filename."""
    parent = str(Path(file_relpath).parent).replace("\\", "/")
    if parent == ".":
        parent = ""
    return parent, Path(file_relpath).name


def _day_start_ts(day: str) -> float:
    return datetime.strptime(day, "%Y-%m-%d").timestamp()


def _day_end_ts(day: str) -> float:
    return datetime.strptime(day + " 23:59:59", "%Y-%m-%d %H:%M:%S").timestamp()


@dataclass
class GapQuery:
    missing_exif: bool = False
    missing_date: bool = False
    missing_gps: bool = False
    missing_make: bool = False
    root: str = ""
    prefix: str = ""
    ext: str = ""
    writable: str = "all"
    date_field: str = "exif"
    date_from: str = ""
    date_to: str = ""
    min_count: int = 0
    min_pct: float = 0.0
    page: int = 1
    per_page: int = 100


@dataclass
class FileRow:
    relpath: str
    root: str
    mtime: float
    size: int
    has_exif: bool
    has_date: bool
    has_gps: bool
    has_make: bool
    datetime: Optional[str]
    file_mtime: float
    lat: Optional[float]
    lon: Optional[float]
    mime: Optional[str]
    writable: bool
    scanned_at: str


class GapIndex:
    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS files (
                relpath TEXT PRIMARY KEY,
                root TEXT NOT NULL,
                mtime REAL NOT NULL,
                size INTEGER NOT NULL,
                has_exif INTEGER NOT NULL DEFAULT 0,
                has_date INTEGER NOT NULL DEFAULT 0,
                has_gps INTEGER NOT NULL DEFAULT 0,
                has_make INTEGER NOT NULL DEFAULT 0,
                datetime TEXT,
                file_mtime REAL,
                lat REAL,
                lon REAL,
                mime TEXT,
                writable INTEGER NOT NULL DEFAULT 1,
                scanned_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS folders (
                relpath TEXT PRIMARY KEY,
                root TEXT NOT NULL,
                photo_count INTEGER NOT NULL DEFAULT 0,
                missing_exif_count INTEGER NOT NULL DEFAULT 0,
                missing_date_count INTEGER NOT NULL DEFAULT 0,
                missing_gps_count INTEGER NOT NULL DEFAULT 0,
                missing_make_count INTEGER NOT NULL DEFAULT 0,
                missing_exif_pct REAL NOT NULL DEFAULT 0,
                missing_date_pct REAL NOT NULL DEFAULT 0,
                missing_gps_pct REAL NOT NULL DEFAULT 0,
                missing_make_pct REAL NOT NULL DEFAULT 0,
                is_writable INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                total INTEGER NOT NULL DEFAULT 0,
                done INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                started_at TEXT,
                finished_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_files_root ON files(root);
            CREATE INDEX IF NOT EXISTS idx_files_gaps
                ON files(has_exif, has_date, has_gps, has_make);
            """
        )
        self._conn.commit()

    def known_fingerprints(self) -> dict[str, tuple[float, int, int]]:
        """relpath -> (mtime, size, writable)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT relpath, mtime, size, writable FROM files"
            ).fetchall()
        return {r["relpath"]: (r["mtime"], r["size"], int(r["writable"])) for r in rows}

    def upsert_files(self, rows: Iterable[FileRow]) -> None:
        payload = [
            (
                r.relpath, r.root, r.mtime, r.size,
                int(r.has_exif), int(r.has_date), int(r.has_gps), int(r.has_make),
                r.datetime, r.file_mtime, r.lat, r.lon, r.mime,
                int(r.writable), r.scanned_at,
            )
            for r in rows
        ]
        if not payload:
            return
        with self._lock:
            self._conn.executemany(
                """
                INSERT INTO files (
                    relpath, root, mtime, size,
                    has_exif, has_date, has_gps, has_make,
                    datetime, file_mtime, lat, lon, mime,
                    writable, scanned_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(relpath) DO UPDATE SET
                    root=excluded.root,
                    mtime=excluded.mtime,
                    size=excluded.size,
                    has_exif=excluded.has_exif,
                    has_date=excluded.has_date,
                    has_gps=excluded.has_gps,
                    has_make=excluded.has_make,
                    datetime=excluded.datetime,
                    file_mtime=excluded.file_mtime,
                    lat=excluded.lat,
                    lon=excluded.lon,
                    mime=excluded.mime,
                    writable=excluded.writable,
                    scanned_at=excluded.scanned_at
                """,
                payload,
            )
            self._conn.commit()

    def update_writable(self, relpath: str, writable: bool) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE files SET writable=? WHERE relpath=?",
                (int(writable), relpath),
            )
            self._conn.commit()

    def delete_missing(self, keep: set[str]) -> int:
        with self._lock:
            existing = {
                r["relpath"]
                for r in self._conn.execute("SELECT relpath FROM files").fetchall()
            }
            gone = existing - keep
            if gone:
                self._conn.executemany(
                    "DELETE FROM files WHERE relpath=?",
                    [(p,) for p in gone],
                )
                self._conn.commit()
            return len(gone)

    def rebuild_folders(self, writable_map: dict[str, bool]) -> None:
        """Aggregate file gaps into folders; parents include descendants."""
        with self._lock:
            files = self._conn.execute(
                """
                SELECT relpath, has_exif, has_date, has_gps, has_make
                FROM files
                """
            ).fetchall()

        agg: dict[str, dict[str, int]] = {}
        for row in files:
            for folder in folder_ancestors(row["relpath"]):
                bucket = agg.setdefault(
                    folder,
                    {
                        "photo": 0,
                        "miss_exif": 0,
                        "miss_date": 0,
                        "miss_gps": 0,
                        "miss_make": 0,
                    },
                )
                bucket["photo"] += 1
                if not row["has_exif"]:
                    bucket["miss_exif"] += 1
                if not row["has_date"]:
                    bucket["miss_date"] += 1
                if not row["has_gps"]:
                    bucket["miss_gps"] += 1
                if not row["has_make"]:
                    bucket["miss_make"] += 1

        # Folders with photos plus empty dirs that were walked (writable_map)
        all_folders = set(agg) | set(writable_map)

        payload = []
        for folder in all_folders:
            stats = agg.get(
                folder,
                {
                    "photo": 0,
                    "miss_exif": 0,
                    "miss_date": 0,
                    "miss_gps": 0,
                    "miss_make": 0,
                },
            )
            n = stats["photo"] or 0
            def pct(count: int) -> float:
                return round(100.0 * count / n, 1) if n else 0.0

            writable = writable_map.get(folder, True)
            payload.append(
                (
                    folder,
                    root_of(folder),
                    stats["photo"],
                    stats["miss_exif"],
                    stats["miss_date"],
                    stats["miss_gps"],
                    stats["miss_make"],
                    pct(stats["miss_exif"]),
                    pct(stats["miss_date"]),
                    pct(stats["miss_gps"]),
                    pct(stats["miss_make"]),
                    int(writable),
                )
            )

        with self._lock:
            self._conn.execute("DELETE FROM folders")
            if payload:
                self._conn.executemany(
                    """
                    INSERT INTO folders (
                        relpath, root, photo_count,
                        missing_exif_count, missing_date_count,
                        missing_gps_count, missing_make_count,
                        missing_exif_pct, missing_date_pct,
                        missing_gps_pct, missing_make_pct,
                        is_writable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
            self._conn.commit()

    def create_job(self) -> int:
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO jobs (status, total, done, skipped, started_at)
                VALUES ('running', 0, 0, 0, ?)
                """,
                (utc_now(),),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def update_job(
        self,
        job_id: int,
        *,
        status: Optional[str] = None,
        total: Optional[int] = None,
        done: Optional[int] = None,
        skipped: Optional[int] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        fields: list[str] = []
        values: list[object] = []
        if status is not None:
            fields.append("status=?")
            values.append(status)
        if total is not None:
            fields.append("total=?")
            values.append(total)
        if done is not None:
            fields.append("done=?")
            values.append(done)
        if skipped is not None:
            fields.append("skipped=?")
            values.append(skipped)
        if error is not None:
            fields.append("error=?")
            values.append(error)
        if finished:
            fields.append("finished_at=?")
            values.append(utc_now())
        if not fields:
            return
        values.append(job_id)
        with self._lock:
            self._conn.execute(
                f"UPDATE jobs SET {', '.join(fields)} WHERE id=?",
                values,
            )
            self._conn.commit()

    def latest_job(self) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM jobs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def list_folders(self, query: GapQuery | None = None) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM folders
                ORDER BY relpath
                """
            ).fetchall()
        folders = [dict(r) for r in rows]
        if query is None:
            return folders
        match_counts = None
        selected_gaps = sum(
            [
                query.missing_exif,
                query.missing_date,
                query.missing_gps,
                query.missing_make,
            ]
        )
        if selected_gaps > 1 and (query.min_count or query.min_pct):
            match_counts = self._matching_counts_by_folder(query)
        return [f for f in folders if self._folder_matches(f, query, match_counts)]

    def query_files(self, query: GapQuery) -> tuple[list[dict], int]:
        where, params = self._file_where(query)
        page = max(1, query.page)
        per_page = min(max(1, query.per_page), 500)
        offset = (page - 1) * per_page
        with self._lock:
            total = self._conn.execute(
                f"SELECT COUNT(*) FROM files{where}", params
            ).fetchone()[0]
            rows = self._conn.execute(
                f"""
                SELECT * FROM files{where}
                ORDER BY relpath
                LIMIT ? OFFSET ?
                """,
                [*params, per_page, offset],
            ).fetchall()
        return [dict(r) for r in rows], int(total)

    def iter_files(self, query: GapQuery, batch_size: int = 500):
        where, params = self._file_where(query)
        offset = 0
        while True:
            with self._lock:
                rows = self._conn.execute(
                    f"""
                    SELECT * FROM files{where}
                    ORDER BY relpath
                    LIMIT ? OFFSET ?
                    """,
                    [*params, batch_size, offset],
                ).fetchall()
            if not rows:
                break
            for row in rows:
                yield dict(row)
            if len(rows) < batch_size:
                break
            offset += batch_size

    def _matching_counts_by_folder(self, query: GapQuery) -> dict[str, int]:
        """Count files matching the file query, rolled up to ancestor folders."""
        where, params = self._file_where(query)
        with self._lock:
            rows = self._conn.execute(
                f"SELECT relpath FROM files{where}", params
            ).fetchall()
        counts: dict[str, int] = {}
        for row in rows:
            for folder in folder_ancestors(row["relpath"]):
                counts[folder] = counts.get(folder, 0) + 1
        return counts

    def _file_where(self, q: GapQuery) -> tuple[str, list]:
        clauses: list[str] = []
        params: list = []
        if q.missing_exif:
            clauses.append("has_exif = 0")
        if q.missing_date:
            clauses.append("has_date = 0")
        if q.missing_gps:
            clauses.append("has_gps = 0")
        if q.missing_make:
            clauses.append("has_make = 0")
        if q.root:
            clauses.append("root = ?")
            params.append(q.root)
        if q.prefix:
            prefix = q.prefix.rstrip("/")
            clauses.append("relpath LIKE ? ESCAPE '\\'")
            params.append(_like_escape(prefix) + "/%")
        if q.writable == "ro":
            clauses.append("writable = 0")
        elif q.writable == "rw":
            clauses.append("writable = 1")
        if q.ext:
            ext = q.ext.lower().lstrip(".")
            clauses.append("lower(relpath) LIKE ? ESCAPE '\\'")
            params.append("%." + _like_escape(ext))
        if q.date_from or q.date_to:
            if q.date_field == "file":
                if q.date_from:
                    clauses.append("file_mtime >= ?")
                    params.append(_day_start_ts(q.date_from))
                if q.date_to:
                    clauses.append("file_mtime <= ?")
                    params.append(_day_end_ts(q.date_to))
            else:
                if q.date_from:
                    clauses.append("datetime IS NOT NULL AND datetime >= ?")
                    params.append(q.date_from.replace("-", ":") + " 00:00:00")
                if q.date_to:
                    clauses.append("datetime IS NOT NULL AND datetime <= ?")
                    params.append(q.date_to.replace("-", ":") + " 23:59:59")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params

    @staticmethod
    def _folder_matches(
        folder: dict,
        q: GapQuery,
        match_counts: dict[str, int] | None = None,
    ) -> bool:
        relpath = folder["relpath"]
        if folder["photo_count"] <= 0 and relpath != "":
            return False
        if q.root and folder["root"] != q.root and relpath != q.root:
            if relpath != "" and not relpath.startswith(q.root + "/"):
                return False
            if relpath == "":
                return False
        if q.prefix:
            prefix = q.prefix.rstrip("/")
            is_self = relpath == prefix
            is_desc = relpath.startswith(prefix + "/")
            is_anc = relpath == "" or prefix.startswith(relpath + "/")
            if not (is_self or is_desc or is_anc):
                return False
        if q.writable == "ro" and folder["is_writable"]:
            return False
        if q.writable == "rw" and not folder["is_writable"]:
            return False

        if match_counts is not None:
            count = match_counts.get(relpath, 0)
            n = folder["photo_count"] or 0
            pct = round(100.0 * count / n, 1) if n else 0.0
        elif q.missing_exif:
            count, pct = folder["missing_exif_count"], folder["missing_exif_pct"]
        elif q.missing_date:
            count, pct = folder["missing_date_count"], folder["missing_date_pct"]
        elif q.missing_gps:
            count, pct = folder["missing_gps_count"], folder["missing_gps_pct"]
        elif q.missing_make:
            count, pct = folder["missing_make_count"], folder["missing_make_pct"]
        else:
            count = max(
                folder["missing_exif_count"],
                folder["missing_date_count"],
                folder["missing_gps_count"],
                folder["missing_make_count"],
            )
            pct = max(
                folder["missing_exif_pct"],
                folder["missing_date_pct"],
                folder["missing_gps_pct"],
                folder["missing_make_pct"],
            )
        if q.min_count and count < q.min_count:
            return False
        if q.min_pct and pct < q.min_pct:
            return False
        return True
