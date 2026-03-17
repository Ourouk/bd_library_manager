"""Test CBZ creation."""

import zipfile
from pathlib import Path

import pytest

from bdlib.converters import cbz


class TestCreateCbz:
    """Test CBZ archive creation."""

    def test_create_cbz_basic(self, tmp_path):
        """Test basic CBZ creation."""
        # Create input directory with images
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        (input_dir / "page1.jpg").write_bytes(b"fake jpeg 1")
        (input_dir / "page2.jpg").write_bytes(b"fake jpeg 2")
        
        output_file = tmp_path / "output.cbz"
        
        result = cbz.create_cbz(input_dir, output_file)
        
        assert result is True
        assert output_file.exists()
        
        # Verify ZIP contents
        with zipfile.ZipFile(output_file, 'r') as zf:
            names = zf.namelist()
            assert len(names) == 2
            assert "001.jpg" in names
            assert "002.jpg" in names

    def test_create_cbz_with_metadata(self, tmp_path):
        """Test CBZ creation with ComicInfo.xml."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        (input_dir / "page1.jpg").write_bytes(b"x")
        
        # Create ComicInfo.xml
        comic_info = input_dir / "ComicInfo.xml"
        comic_info.write_text("<ComicInfo></ComicInfo>")
        
        output_file = tmp_path / "output.cbz"
        
        cbz.create_cbz(input_dir, output_file, comic_info)
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            names = zf.namelist()
            assert "001.jpg" in names
            assert "ComicInfo.xml" in names

    def test_create_cbz_no_images(self, tmp_path):
        """Test CBZ creation with no images fails gracefully."""
        input_dir = tmp_path / "empty"
        input_dir.mkdir()
        
        output_file = tmp_path / "output.cbz"
        
        result = cbz.create_cbz(input_dir, output_file)
        
        assert result is False

    def test_create_cbz_output_path_default(self, tmp_path):
        """Test default output path uses input directory name."""
        input_dir = tmp_path / "my_comic"
        input_dir.mkdir()
        (input_dir / "page.jpg").write_bytes(b"x")
        
        result = cbz.create_cbz(input_dir)
        
        assert result is True
        assert (tmp_path / "my_comic.cbz").exists()

    def test_create_cbz_sorting(self, tmp_path):
        """Test images are sorted correctly."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        # Create files in non-alphabetical order
        (input_dir / "z_page.jpg").write_bytes(b"z")
        (input_dir / "a_page.jpg").write_bytes(b"a")
        (input_dir / "m_page.jpg").write_bytes(b"m")
        
        output_file = tmp_path / "output.cbz"
        cbz.create_cbz(input_dir, output_file)
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            names = zf.namelist()
            # Should be sorted: 001, 002, 003
            assert names[0] == "001.jpg"
            assert names[1] == "002.jpg"
            assert names[2] == "003.jpg"

    def test_create_cbz_jxl_extension(self, tmp_path):
        """Test CBZ creation with JXL files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        (input_dir / "page1.jxl").write_bytes(b"fake jxl")
        (input_dir / "page2.jxl").write_bytes(b"fake jxl")
        
        output_file = tmp_path / "output.cbz"
        
        cbz.create_cbz(input_dir, output_file)
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            names = zf.namelist()
            assert "001.jxl" in names
            assert "002.jxl" in names
