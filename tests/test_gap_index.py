"""Tests for the SQLite gap index."""
from datetime import datetime

from src.core.gap_index import (
    FileRow,
    GapIndex,
    GapQuery,
    editor_parts,
    folder_ancestors,
    root_of,
    utc_now,
)


def _row(
    relpath: str,
    *,
    has_exif=1,
    has_date=1,
    has_gps=0,
    has_make=1,
    writable=True,
    datetime_value="2024:01:01 00:00:00",
    file_mtime=1.0,
):
    return FileRow(
        relpath=relpath,
        root=root_of(relpath),
        mtime=file_mtime,
        size=10,
        has_exif=bool(has_exif),
        has_date=bool(has_date),
        has_gps=bool(has_gps),
        has_make=bool(has_make),
        datetime=datetime_value if has_date else None,
        file_mtime=file_mtime,
        lat=48.4 if has_gps else None,
        lon=16.2 if has_gps else None,
        mime="image/jpeg",
        writable=writable,
        scanned_at=utc_now(),
    )


def test_folder_ancestors():
    assert folder_ancestors("dir1/a/b/c.jpg") == ["dir1/a/b", "dir1/a", "dir1", ""]
    assert folder_ancestors("dir1/x.jpg") == ["dir1", ""]


def test_upsert_and_fingerprint(tmp_path):
    index = GapIndex(tmp_path / "gaps.sqlite")
    index.upsert_files([_row("dir1/a.jpg")])
    known = index.known_fingerprints()
    assert known["dir1/a.jpg"][1] == 10
    index.close()


def test_rebuild_folders_rolls_up_parents(tmp_path):
    index = GapIndex(tmp_path / "gaps.sqlite")
    index.upsert_files([
        _row("dir1/sub/one.jpg", has_gps=0),
        _row("dir1/sub/two.jpg", has_gps=1),
        _row("dir1/three.jpg", has_gps=0),
    ])
    index.rebuild_folders({
        "": True,
        "dir1": True,
        "dir1/sub": False,
    })
    by_path = {f["relpath"]: f for f in index.list_folders()}
    assert by_path["dir1/sub"]["photo_count"] == 2
    assert by_path["dir1/sub"]["missing_gps_count"] == 1
    assert by_path["dir1/sub"]["is_writable"] == 0
    assert by_path["dir1"]["photo_count"] == 3
    assert by_path["dir1"]["missing_gps_count"] == 2
    assert by_path[""]["photo_count"] == 3
    index.close()


def test_delete_missing(tmp_path):
    index = GapIndex(tmp_path / "gaps.sqlite")
    index.upsert_files([_row("dir1/a.jpg"), _row("dir1/b.jpg")])
    removed = index.delete_missing({"dir1/a.jpg"})
    assert removed == 1
    assert list(index.known_fingerprints()) == ["dir1/a.jpg"]
    index.close()


def test_editor_parts():
    assert editor_parts("dir1/sub/a.jpg") == ("dir1/sub", "a.jpg")
    assert editor_parts("a.jpg") == ("", "a.jpg")


def test_query_files_filters_and_pagination(tmp_path):
    index = GapIndex(tmp_path / "gaps.sqlite")
    june = datetime(2024, 6, 15, 12, 0, 0).timestamp()
    index.upsert_files([
        _row("dir1/a.jpg", has_gps=0, has_date=1),
        _row("dir1/sub/b.jpg", has_gps=0, has_date=0, datetime_value=None),
        _row("dir1/c.png", has_gps=1, has_date=1, has_exif=1),
        _row(
            "dir2/d.jpg",
            has_gps=0,
            has_date=1,
            writable=False,
            datetime_value="2024:06:15 12:00:00",
            file_mtime=june,
        ),
    ])
    gps_rows, gps_total = index.query_files(GapQuery(missing_gps=True))
    assert gps_total == 3
    assert [r["relpath"] for r in gps_rows] == [
        "dir1/a.jpg",
        "dir1/sub/b.jpg",
        "dir2/d.jpg",
    ]

    both, both_total = index.query_files(GapQuery(missing_gps=True, missing_date=True))
    assert both_total == 1
    assert both[0]["relpath"] == "dir1/sub/b.jpg"

    prefixed, _ = index.query_files(GapQuery(prefix="dir1/sub"))
    assert [r["relpath"] for r in prefixed] == ["dir1/sub/b.jpg"]

    png, _ = index.query_files(GapQuery(ext="png"))
    assert [r["relpath"] for r in png] == ["dir1/c.png"]

    ro, _ = index.query_files(GapQuery(writable="ro"))
    assert [r["relpath"] for r in ro] == ["dir2/d.jpg"]

    page1, total = index.query_files(GapQuery(missing_gps=True, page=1, per_page=2))
    page2, _ = index.query_files(GapQuery(missing_gps=True, page=2, per_page=2))
    assert total == 3
    assert len(page1) == 2
    assert len(page2) == 1

    by_exif, _ = index.query_files(
        GapQuery(date_field="exif", date_from="2024-06-15", date_to="2024-06-15")
    )
    assert [r["relpath"] for r in by_exif] == ["dir2/d.jpg"]

    by_file, _ = index.query_files(
        GapQuery(date_field="file", date_from="2024-06-15", date_to="2024-06-15")
    )
    assert [r["relpath"] for r in by_file] == ["dir2/d.jpg"]
    index.close()


def test_list_folders_respects_prefix_and_threshold(tmp_path):
    index = GapIndex(tmp_path / "gaps.sqlite")
    index.upsert_files([
        _row("dir1/sub/one.jpg", has_gps=0),
        _row("dir1/sub/two.jpg", has_gps=1),
        _row("dir1/three.jpg", has_gps=0),
        _row("dir2/x.jpg", has_gps=1),
    ])
    index.rebuild_folders({
        "": True,
        "dir1": True,
        "dir1/sub": False,
        "dir2": True,
    })
    with_prefix = {f["relpath"] for f in index.list_folders(GapQuery(prefix="dir1/sub"))}
    assert with_prefix == {"", "dir1", "dir1/sub"}

    hot = {f["relpath"] for f in index.list_folders(GapQuery(missing_gps=True, min_count=2))}
    assert "dir1" in hot
    assert "dir1/sub" not in hot

    ro = {f["relpath"] for f in index.list_folders(GapQuery(writable="ro"))}
    assert ro == {"dir1/sub"}
    index.close()
