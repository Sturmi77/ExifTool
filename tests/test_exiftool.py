"""Basic tests for ExifToolWrapper and utility functions."""
import pytest
from src.core.utils import parse_exif_date, format_exif_date, decimal_to_dms
from src.core.exiftool import ExifToolWrapper


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
