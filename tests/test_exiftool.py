"""Basic tests for ExifToolWrapper, utils and web helper functions."""
import asyncio

import pytest
from src.core.utils import parse_exif_date, format_exif_date, decimal_to_dms
from src.core.exiftool import ExifToolWrapper
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


def test_exiftool_available():
    wrapper = ExifToolWrapper()
    # This test passes only if exiftool is installed on the system
    # Skip gracefully if not available
    if not wrapper.is_available():
        pytest.skip("exiftool not installed on this system")


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
