"""Wrapper around the ExifTool CLI binary."""
import subprocess
import shutil
from typing import Optional


class ExifToolWrapper:
    """Calls the system exiftool binary via subprocess."""

    BINARY = "exiftool"

    def is_available(self) -> bool:
        """Check whether exiftool is installed and in PATH."""
        return shutil.which(self.BINARY) is not None

    def read_metadata(self, filepath: str) -> dict:
        """Return a dict of EXIF tags for a single file."""
        result = subprocess.run(
            [self.BINARY, "-j", "-DateTimeOriginal", "-GPSLatitude", "-GPSLongitude", filepath],
            capture_output=True, text=True, check=True
        )
        import json
        data = json.loads(result.stdout)
        return data[0] if data else {}

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

        :param files: List of file paths to update.
        :param date: Date string in format 'YYYY:MM:DD HH:MM:SS'.
        :param lat: Latitude as decimal string (e.g. '48.4010').
        :param lon: Longitude as decimal string (e.g. '16.1680').
        """
        if not files:
            return

        args = [self.BINARY, "-overwrite_original_in_place", "-preserve"]

        if date:
            args += [
                f"-DateTimeOriginal={date}",
                f"-CreateDate={date}",
                f"-ModifyDate={date}",
            ]
        if lat:
            # Handle negative values as South
            ref = "S" if float(lat) < 0 else "N"
            args += [f"-GPSLatitude={abs(float(lat))}", f"-GPSLatitudeRef={ref}"]
        if lon:
            ref = "W" if float(lon) < 0 else "E"
            args += [f"-GPSLongitude={abs(float(lon))}", f"-GPSLongitudeRef={ref}"]

        args += files

        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ExifTool error:\n{result.stderr}")
