"""Test fixtures and configuration."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_folder():
    """Return path to the sample comic folder."""
    return Path(__file__).parent / "sample" / "Avant l'Incal" / "01 - Adieu le père"


@pytest.fixture
def sample_series_folder():
    """Return path to the sample series folder."""
    return Path(__file__).parent / "sample" / "Avant l'Incal"


@pytest.fixture
def sample_image_files(sample_folder):
    """Return list of actual sample JPEG image files."""
    return sorted(sample_folder.glob("*.jpg"))


@pytest.fixture
def sample_image_file(sample_folder):
    """Return a single sample JPEG image file."""
    return next(sample_folder.glob("*.jpg"))


@pytest.fixture
def sample_jpeg_bytes():
    """Return minimal JPEG-like bytes for testing."""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


@pytest.fixture
def temp_image_folder(tmp_path, sample_image_files):
    """Create a temporary directory with copies of sample images."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()

    for i, src in enumerate(sample_image_files[:5], start=1):
        dst = img_dir / f"page{i:02d}.jpg"
        dst.write_bytes(src.read_bytes())

    return img_dir
