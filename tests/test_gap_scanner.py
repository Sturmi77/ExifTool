"""Tests for the gap scanner (ExifTool mocked)."""
from pathlib import Path

from PIL import Image

from src.core.gap_index import GapIndex
from src.core.gap_scanner import GapScanner, row_from_meta, walk_images


class FakeExif:
    def __init__(self, by_path: dict[str, dict] | None = None):
        self.by_path = by_path or {}
        self.calls: list[list[str]] = []

    def read_metadata_batch(self, paths, tags=None):
        self.calls.append(list(paths))
        rows = []
        resolved_map = {str(Path(key).resolve()): value for key, value in self.by_path.items()}
        for path in paths:
            meta = dict(resolved_map.get(str(Path(path).resolve()), {}))
            meta.setdefault("SourceFile", path)
            rows.append(meta)
        return rows


def _jpg(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color="red").save(path, "JPEG")


def test_walk_images_skips_hidden(tmp_path):
    _jpg(tmp_path / "dir1" / "a.jpg")
    _jpg(tmp_path / "dir1" / ".hidden.jpg")
    _jpg(tmp_path / "dir1" / ".trash" / "b.jpg")
    found = {p.name for p in walk_images(tmp_path)}
    assert found == {"a.jpg"}


def test_row_from_meta_gap_flags():
    row = row_from_meta(
        "dir1/a.jpg",
        mtime=1.0,
        size=10,
        writable=False,
        meta={"DateTimeOriginal": "2024:01:01 00:00:00", "Make": "Canon"},
    )
    assert row.has_date is True
    assert row.has_exif is False
    assert row.has_gps is False
    assert row.has_make is True
    assert row.writable is False


def test_scan_indexes_files_and_skips_unchanged(tmp_path):
    photos = tmp_path / "photos"
    one = photos / "dir1" / "one.jpg"
    two = photos / "dir1" / "sub" / "two.jpg"
    _jpg(one)
    _jpg(two)

    fake = FakeExif({
        str(one): {
            "SourceFile": str(one),
            "ExifByteOrder": "MM",
            "DateTimeOriginal": "2024:01:01 00:00:00",
            "GPSLatitude": 48.4,
            "Make": "Canon",
        },
        str(two): {"SourceFile": str(two)},
    })
    index = GapIndex(tmp_path / "gaps.sqlite")
    scanner = GapScanner(
        index, fake, photos, batch_size=10, writable_fn=lambda p: True
    )
    scanner._scan(index.create_job())

    assert len(fake.calls) == 1
    folders = {f["relpath"]: f for f in index.list_folders()}
    assert folders["dir1"]["photo_count"] == 2
    assert folders["dir1/sub"]["missing_gps_count"] == 1
    assert folders["dir1/sub"]["missing_date_count"] == 1

    fake.calls.clear()
    scanner._scan(index.create_job())
    assert fake.calls == []
    job = index.latest_job()
    assert job["skipped"] == 2
    assert job["status"] == "done"
    index.close()


def test_scan_marks_read_only_folder(tmp_path):
    photos = tmp_path / "photos"
    path = photos / "dir1" / "ro" / "a.jpg"
    _jpg(path)
    fake = FakeExif({str(path): {"SourceFile": str(path)}})
    index = GapIndex(tmp_path / "gaps.sqlite")

    def writable_fn(folder: Path) -> bool:
        return folder.name != "ro"

    scanner = GapScanner(index, fake, photos, writable_fn=writable_fn)
    scanner._scan(index.create_job())
    folders = {f["relpath"]: f for f in index.list_folders()}
    assert folders["dir1/ro"]["is_writable"] == 0
    assert folders["dir1"]["is_writable"] == 1
    known = index.known_fingerprints()
    assert known["dir1/ro/a.jpg"][2] == 0
    index.close()


def test_eta_seconds_from_progress():
    from datetime import datetime, timedelta, timezone

    from src.core.gap_scanner import _eta_seconds

    started = (datetime.now(timezone.utc) - timedelta(seconds=10)).replace(microsecond=0).isoformat()
    eta = _eta_seconds({"running": True, "done": 10, "total": 100, "started_at": started})
    assert eta is not None and eta > 0
    assert _eta_seconds({"running": False, "done": 10, "total": 100, "started_at": started}) is None
    assert _eta_seconds({"running": True, "done": 0, "total": 100, "started_at": started}) is None
