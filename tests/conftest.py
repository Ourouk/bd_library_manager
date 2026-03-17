"""Test fixtures and configuration."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_folder():
    """Return path to the sample comic folder."""
    return Path(__file__).parent / "sample" / "Avant l'Incal" / "01 - Adieu le père"


@pytest.fixture
def sample_series_folder():
    """Return path to the sample series folder."""
    return Path(__file__).parent / "sample" / "Avant l'Incal"


@pytest.fixture
def sample_jpeg_bytes():
    """Return minimal JPEG-like bytes for testing."""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


@pytest.fixture
def sample_image_files(tmp_path, sample_jpeg_bytes):
    """Create a temporary directory with sample image files."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    
    (img_dir / "page01.jpg").write_bytes(sample_jpeg_bytes)
    (img_dir / "page02.jpg").write_bytes(sample_jpeg_bytes)
    (img_dir / "page03.jpg").write_bytes(sample_jpeg_bytes)
    
    return img_dir
