"""Utility helpers."""
from datetime import datetime


def parse_exif_date(date_str: str) -> datetime | None:
    """Parse EXIF date string 'YYYY:MM:DD HH:MM:SS' into a datetime object."""
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def format_exif_date(dt: datetime) -> str:
    """Format a datetime object as EXIF date string."""
    return dt.strftime("%Y:%m:%d %H:%M:%S")


def decimal_to_dms(decimal: float) -> tuple[int, int, float]:
    """Convert decimal degrees to (degrees, minutes, seconds)."""
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes_float = (decimal - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return degrees, minutes, seconds
