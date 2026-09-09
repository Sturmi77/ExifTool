"""API tests for /gaps scan endpoints."""
from fastapi.testclient import TestClient
from PIL import Image

from src.core.gap_index import GapIndex
from src.core.gap_scanner import GapScanner
from src.web import main


class FakeExif:
    def read_metadata_batch(self, paths, tags=None):
        return [{"SourceFile": p} for p in paths]


def test_gaps_scan_and_status(tmp_path, monkeypatch):
    photos = tmp_path / "photos"
    jpg = photos / "dir1" / "a.jpg"
    jpg.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8), color="blue").save(jpg, "JPEG")

    index = GapIndex(tmp_path / "gaps.sqlite")
    scanner = GapScanner(index, FakeExif(), photos, writable_fn=lambda p: True)
    monkeypatch.setattr(main, "gap_scanner", scanner)
    monkeypatch.setattr(main, "gap_index", index)

    with TestClient(main.app) as client:
        started = client.post("/gaps/scan")
        assert started.status_code == 200
        job_id = started.json()["job_id"]
        assert scanner._thread is not None
        scanner._thread.join(timeout=5)
        status = client.get("/gaps/status")
        assert status.status_code == 200
        body = status.json()
        assert body["id"] == job_id
        assert body["status"] == "done"
        assert body["total"] == 1
        folders = client.get("/gaps/folders").json()["folders"]
        assert any(f["relpath"] == "dir1" and f["photo_count"] == 1 for f in folders)

    index.close()


def _seeded_scanner(tmp_path, monkeypatch):
    from src.core.gap_index import FileRow, root_of, utc_now

    def row(relpath, **kwargs):
        has_gps = kwargs.get("has_gps", 0)
        has_date = kwargs.get("has_date", 1)
        return FileRow(
            relpath=relpath,
            root=root_of(relpath),
            mtime=1.0,
            size=10,
            has_exif=bool(kwargs.get("has_exif", 1)),
            has_date=bool(has_date),
            has_gps=bool(has_gps),
            has_make=bool(kwargs.get("has_make", 1)),
            datetime="2024:01:01 00:00:00" if has_date else None,
            file_mtime=1.0,
            lat=48.4 if has_gps else None,
            lon=16.2 if has_gps else None,
            mime="image/jpeg",
            writable=kwargs.get("writable", True),
            scanned_at=utc_now(),
        )

    index = GapIndex(tmp_path / "gaps.sqlite")
    index.upsert_files([
        row("dir1/a.jpg", has_gps=0),
        row("dir1/sub/b.jpg", has_gps=0, has_date=0, writable=False),
        row("dir2/c.jpg", has_gps=1),
    ])
    index.rebuild_folders({"": True, "dir1": True, "dir1/sub": False, "dir2": True})
    scanner = GapScanner(index, FakeExif(), tmp_path, writable_fn=lambda p: True)
    monkeypatch.setattr(main, "gap_scanner", scanner)
    monkeypatch.setattr(main, "gap_index", index)
    return index


def test_gaps_html_nav_and_filters(tmp_path, monkeypatch):
    index = _seeded_scanner(tmp_path, monkeypatch)
    with TestClient(main.app) as client:
        home = client.get("/")
        assert home.status_code == 200
        assert 'href="/gaps"' in home.text
        assert "Lückenfinder" in home.text

        page = client.get("/gaps")
        assert page.status_code == 200
        assert "EXIF-Lückenfinder" in page.text
        assert "dir1/a.jpg" in page.text
        assert "Im Editor" in page.text
        assert 'href="/?subdir=dir1&amp;selected=a.jpg"' in page.text or \
            'href="/?subdir=dir1&selected=a.jpg"' in page.text

        filtered = client.get("/gaps/files", params={"missing_gps": "1", "missing_date": "1"})
        assert filtered.status_code == 200
        body = filtered.json()
        assert body["total"] == 1
        assert body["files"][0]["relpath"] == "dir1/sub/b.jpg"
        assert body["files"][0]["editor_subdir"] == "dir1/sub"
        assert body["files"][0]["editor_name"] == "b.jpg"

        paged = client.get("/gaps/files", params={"per_page": 1, "page": 2})
        assert paged.json()["total"] == 3
        assert len(paged.json()["files"]) == 1

        csv_resp = client.get("/gaps/export.csv", params={"missing_gps": "1"})
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["content-type"]
        text = csv_resp.text
        assert "writable" in text.splitlines()[0]
        assert "dir1/a.jpg" in text
        assert "dir1/sub/b.jpg" in text
        assert "dir2/c.jpg" not in text

        html_filtered = client.get("/gaps", params={"writable": "ro"})
        assert "dir1/sub/b.jpg" in html_filtered.text
        assert "dir2/c.jpg" not in html_filtered.text
        assert "nur lesen" in html_filtered.text
        assert 'class="gap-select"' not in html_filtered.text

        writable_page = client.get("/gaps")
        assert 'class="gap-select"' in writable_page.text
        assert "Auswahl im Editor öffnen" in writable_page.text
        assert "ohne GPS" in page.text
        assert "/?subdir=dir1" in page.text

        status = client.get("/gaps/status")
        assert status.status_code == 200
        assert "running" in status.json()
        assert "eta_seconds" in status.json()

    index.close()


def test_editor_read_only_disables_writes(tmp_path, monkeypatch):
    photos = tmp_path / "photos"
    jpg = photos / "dir1" / "a.jpg"
    jpg.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8), color="blue").save(jpg, "JPEG")
    monkeypatch.setattr(main, "BASE_PHOTOS_DIR", photos)
    monkeypatch.setattr(main, "is_writable_dir", lambda p: False)

    with TestClient(main.app) as client:
        page = client.get("/", params={"subdir": "dir1", "selected": "a.jpg"})
        assert page.status_code == 200
        assert "nur lesen" in page.text
        assert "Schreiben deaktiviert" in page.text
        rotate = client.post(
            "/rotate",
            data={"subdir": "dir1", "file": "a.jpg", "direction": "cw"},
        )
        assert rotate.status_code == 403


def test_editor_prechecks_writable_selection(tmp_path, monkeypatch):
    photos = tmp_path / "photos"
    jpg = photos / "dir1" / "a.jpg"
    jpg.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8), color="blue").save(jpg, "JPEG")
    other = photos / "dir1" / "b.jpg"
    Image.new("RGB", (8, 8), color="green").save(other, "JPEG")
    monkeypatch.setattr(main, "BASE_PHOTOS_DIR", photos)

    with TestClient(main.app) as client:
        page = client.get(
            "/",
            params=[("subdir", "dir1"), ("selected", "a.jpg"), ("checked", "a.jpg"), ("checked", "b.jpg")],
        )
        assert page.status_code == 200
        assert page.text.count("checked") >= 2
        assert 'value="a.jpg"' in page.text
        assert 'value="b.jpg"' in page.text


def test_gaps_scan_conflict_when_running(tmp_path, monkeypatch):
    index = GapIndex(tmp_path / "gaps.sqlite")
    scanner = GapScanner(index, FakeExif(), tmp_path, writable_fn=lambda p: True)
    monkeypatch.setattr(scanner, "is_running", lambda: True)
    monkeypatch.setattr(main, "gap_scanner", scanner)

    with TestClient(main.app) as client:
        response = client.post("/gaps/scan")
        assert response.status_code == 409
        assert response.json()["running"] is True

    index.close()
