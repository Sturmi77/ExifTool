"""Point test imports at a throwaway config dir before src.web.main loads."""
import os
from pathlib import Path

_test_root = Path(__file__).resolve().parent / "_tmp"
os.environ.setdefault("EXIFTOOL_CONFIG_DIR", str(_test_root / "config"))
os.environ.setdefault("PHOTOS_DIR", str(_test_root / "photos"))
