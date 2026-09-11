"""Detect whether a directory is writable (NAS, Docker :ro, Windows)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def is_writable_dir(path: Path | str) -> bool:
    """
    Return True if files can be created in *path*.

    `os.access(..., W_OK)` is not reliable on Windows/SMB, so a throwaway
    TemporaryFile probe is used when access looks allowed. The probe is
    deleted on close; nothing is left in the photo folder.
    """
    folder = Path(path)
    try:
        if not folder.is_dir():
            return False
        if not os.access(folder, os.W_OK):
            return False
        with tempfile.TemporaryFile(dir=folder):
            return True
    except OSError:
        return False
