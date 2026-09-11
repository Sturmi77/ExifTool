"""Tests for writable-directory detection."""
from pathlib import Path
from unittest.mock import patch

from src.core.writable import is_writable_dir


def test_writable_tmp_path(tmp_path):
    assert is_writable_dir(tmp_path) is True


def test_missing_dir_is_not_writable(tmp_path):
    assert is_writable_dir(tmp_path / "nope") is False


def test_probe_oserror_means_read_only(tmp_path):
    with patch("src.core.writable.tempfile.TemporaryFile", side_effect=OSError("erofs")):
        assert is_writable_dir(tmp_path) is False
