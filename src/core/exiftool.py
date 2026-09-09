"""Wrapper around the ExifTool CLI via a persistent PyExifTool process."""
from __future__ import annotations

import atexit
import json
import shutil
import threading
from typing import Optional

from exiftool import ExifToolHelper
from exiftool.exceptions import ExifToolExecuteError

# Tags fetched for the preview panel (leading dash optional)
PREVIEW_TAGS = [
    "-FileName", "-DateTimeOriginal", "-CreateDate", "-ModifyDate",
    "-GPSLatitude", "-GPSLongitude", "-GPSAltitude",
    "-Make", "-Model", "-LensModel",
    "-FocalLength", "-Aperture", "-ExposureTime", "-ISO",
    "-ImageSize", "-FileSize", "-MIMEType",
]

BASIC_TAGS = ["DateTimeOriginal", "GPSLatitude", "GPSLongitude"]

# Stay-open defaults: numeric values, skip MakerNotes. No -G so existing
# unprefixed keys (DateTimeOriginal, GPSLatitude, …) stay unchanged.
COMMON_ARGS = ["-n", "-fast2"]


def _normalize_tags(tags: list[str]) -> list[str]:
    """Strip a leading dash so callers can pass '-DateTimeOriginal' or the name."""
    return [t[1:] if t.startswith("-") else t for t in tags]


class ExifToolWrapper:
    """One stay_open ExifTool process for reads and writes."""

    BINARY = "exiftool"

    def __init__(self) -> None:
        self._helper: ExifToolHelper | None = None
        self._lock = threading.Lock()
        atexit.register(self.close)

    def is_available(self) -> bool:
        """Check whether exiftool is installed and in PATH."""
        return shutil.which(self.BINARY) is not None

    def _get_helper(self) -> ExifToolHelper:
        if self._helper is None or not self._helper.running:
            self._helper = ExifToolHelper(
                executable=self.BINARY,
                common_args=list(COMMON_ARGS),
                auto_start=True,
                check_execute=True,
            )
        return self._helper

    def close(self) -> None:
        """Stop the stay_open process if it is running."""
        with self._lock:
            helper = self._helper
            self._helper = None
            if helper is None:
                return
            try:
                helper.terminate()
            except Exception:
                pass

    def read_metadata_batch(
        self,
        paths: list[str],
        tags: list[str] | None = None,
    ) -> list[dict]:
        """Return selected tags for many files in one ExifTool round-trip."""
        if not paths:
            return []
        tag_names = _normalize_tags(tags if tags is not None else BASIC_TAGS)
        with self._lock:
            helper = self._get_helper()
            try:
                return helper.get_tags(paths, tag_names)
            except ExifToolExecuteError as exc:
                stdout = getattr(exc, "stdout", None) or helper.last_stdout
                if stdout:
                    data = json.loads(stdout)
                    if isinstance(data, list):
                        return data
                stderr = getattr(exc, "stderr", None) or helper.last_stderr or str(exc)
                raise RuntimeError(f"ExifTool error:\n{stderr}") from exc

    def read_metadata(self, filepath: str) -> dict:
        """Return basic EXIF tags (date + GPS) for a single file."""
        rows = self.read_metadata_batch([filepath], BASIC_TAGS)
        return rows[0] if rows else {}

    def read_metadata_extended(self, filepath: str) -> dict:
        """Return extended EXIF tags for the preview panel."""
        rows = self.read_metadata_batch([filepath], PREVIEW_TAGS)
        return rows[0] if rows else {}

    def write_metadata(
        self,
        files: list[str],
        date: Optional[str] = None,
        lat: Optional[str] = None,
        lon: Optional[str] = None
    ) -> None:
        """
        Write date and/or GPS coordinates to one or more files.
        ExifTool automatically creates _original backup files.
        """
        if not files:
            return

        args = ["-overwrite_original_in_place", "-preserve"]

        if date:
            args += [
                f"-DateTimeOriginal={date}",
                f"-CreateDate={date}",
                f"-ModifyDate={date}",
            ]
        if lat:
            ref = "S" if float(lat) < 0 else "N"
            args += [f"-GPSLatitude={abs(float(lat))}", f"-GPSLatitudeRef={ref}"]
        if lon:
            ref = "W" if float(lon) < 0 else "E"
            args += [f"-GPSLongitude={abs(float(lon))}", f"-GPSLongitudeRef={ref}"]

        args += files

        with self._lock:
            helper = self._get_helper()
            try:
                helper.execute(*args)
            except ExifToolExecuteError as exc:
                stderr = getattr(exc, "stderr", None) or helper.last_stderr or str(exc)
                raise RuntimeError(f"ExifTool error:\n{stderr}") from exc
