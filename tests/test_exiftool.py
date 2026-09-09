"""Basic tests for ExifToolWrapper, utils and web helper functions."""
import asyncio

import pytest
from src.core.utils import parse_exif_date, format_exif_date, decimal_to_dms
from src.core.exiftool import BASIC_TAGS, ExifToolWrapper, _normalize_tags
from src.web.main import _safe_join, health, BASE_PHOTOS_DIR


def test_parse_valid_date():
    dt = parse_exif_date("2024:08:15 12:30:00")
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 8
    assert dt.day == 15


def test_parse_invalid_date():
    assert parse_exif_date("not-a-date") is None


def test_format_date():
    from datetime import datetime

    dt = datetime(2024, 8, 15, 12, 30, 0)
    assert format_exif_date(dt) == "2024:08:15 12:30:00"


def test_decimal_to_dms():
    d, m, s = decimal_to_dms(48.401)
    assert d == 48
    assert m == 24
    assert round(s, 1) == 3.6


@pytest.fixture
def wrapper():
    tool = ExifToolWrapper()
    yield tool
    tool.close()


def test_normalize_tags_strips_leading_dash():
    assert _normalize_tags(["-DateTimeOriginal", "GPSLatitude"]) == [
        "DateTimeOriginal",
        "GPSLatitude",
    ]


def test_read_metadata_batch_empty_does_not_start_process(wrapper):
    assert wrapper.read_metadata_batch([]) == []
    assert wrapper._helper is None


def test_read_metadata_batch_uses_helper(wrapper, monkeypatch):
    captured = {}

    class FakeHelper:
        def get_tags(self, files, tags, params=None):
            captured["files"] = files
            captured["tags"] = tags
            return [
                {"SourceFile": "a.jpg", "DateTimeOriginal": "2024:01:01 00:00:00"},
                {"SourceFile": "b.jpg"},
            ]

    monkeypatch.setattr(wrapper, "_get_helper", lambda: FakeHelper())
    rows = wrapper.read_metadata_batch(["a.jpg", "b.jpg"], ["-DateTimeOriginal"])
    assert captured["files"] == ["a.jpg", "b.jpg"]
    assert captured["tags"] == ["DateTimeOriginal"]
    assert len(rows) == 2
    assert rows[0]["DateTimeOriginal"] == "2024:01:01 00:00:00"


def test_exiftool_available(wrapper):
    if not wrapper.is_available():
        pytest.skip("exiftool not installed on this system")


def test_read_metadata_batch_roundtrip(wrapper, tmp_path):
    if not wrapper.is_available():
        pytest.skip("exiftool not installed on this system")

    from PIL import Image

    paths = []
    for name in ("one.jpg", "two.jpg"):
        path = tmp_path / name
        Image.new("RGB", (16, 16), color="red").save(path, "JPEG")
        paths.append(str(path))

    wrapper.write_metadata(paths, date="2024:08:15 12:30:00", lat="48.4", lon="16.2")
    rows = wrapper.read_metadata_batch(paths, BASIC_TAGS)
    by_name = {row["SourceFile"].replace("\\", "/").split("/")[-1]: row for row in rows}
    assert set(by_name) == {"one.jpg", "two.jpg"}
    for row in by_name.values():
        assert row.get("DateTimeOriginal") == "2024:08:15 12:30:00"
        assert abs(float(row["GPSLatitude"]) - 48.4) < 0.001
        assert abs(float(row["GPSLongitude"]) - 16.2) < 0.001


def test_safe_join_inside_base(tmp_path, monkeypatch):
    # Use a temporary base dir to avoid depending on real /photos
    base = tmp_path
    # Monkeypatch BASE_PHOTOS_DIR to match our temp dir for this test
    monkeypatch.setattr("src.web.main.BASE_PHOTOS_DIR", base)
    p = _safe_join(base, "subdir/file.jpg")
    assert str(p).startswith(str(base))


def test_safe_join_outside_base_raises(tmp_path, monkeypatch):
    base = tmp_path
    monkeypatch.setattr("src.web.main.BASE_PHOTOS_DIR", base)
    with pytest.raises(ValueError):
        _safe_join(base, "../etc/passwd")


@pytest.mark.asyncio
async def test_health_returns_expected_keys():
    data = await health()
    assert data["status"] == "ok"
    assert "exiftool" in data
