"""Test CBZ creation."""

import zipfile

from bdlib.converters import cbz


class TestCreateCbz:
    """Test CBZ archive creation."""

    def test_create_cbz_with_real_images(self, temp_image_folder, tmp_path):
        """Test CBZ creation with real sample images."""
        output_file = tmp_path / "output.cbz"

        result = cbz.create_cbz(temp_image_folder, output_file)

        assert result is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert len(names) == 5
            assert "001.jpg" in names
            assert "002.jpg" in names

    def test_create_cbz_with_metadata(self, temp_image_folder, tmp_path):
        """Test CBZ creation with ComicInfo.xml."""
        comic_info = temp_image_folder / "ComicInfo.xml"
        comic_info.write_text("<ComicInfo><Title>Test</Title></ComicInfo>")

        output_file = tmp_path / "output.cbz"

        cbz.create_cbz(temp_image_folder, output_file, comic_info)

        with zipfile.ZipFile(output_file, "r") as zf:
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

    def test_create_cbz_output_path_default(self, temp_image_folder, tmp_path):
        """Test default output path uses input directory name."""
        result = cbz.create_cbz(temp_image_folder)

        assert result is True
        assert (tmp_path / "images.cbz").exists()

    def test_create_cbz_sorting(self, tmp_path, sample_image_files):
        """Test images are sorted correctly."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        for i, src in enumerate(sample_image_files[:3], start=1):
            dst = input_dir / f"z_page{i}.jpg"
            dst.write_bytes(src.read_bytes())

        output_file = tmp_path / "output.cbz"
        cbz.create_cbz(input_dir, output_file)

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert names[0] == "001.jpg"
            assert names[1] == "002.jpg"
            assert names[2] == "003.jpg"

    def test_create_cbz_jxl_extension(self, tmp_path, sample_image_files):
        """Test CBZ creation with JXL files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        for i in range(2):
            dst = input_dir / f"page{i + 1}.jxl"
            src = sample_image_files[i]
            dst.write_bytes(src.read_bytes())

        output_file = tmp_path / "output.cbz"

        cbz.create_cbz(input_dir, output_file)

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "001.jxl" in names
            assert "002.jxl" in names

    def test_create_cbz_from_sample_folder(self, sample_folder, tmp_path):
        """Test creating CBZ from the full sample folder."""
        output_file = tmp_path / "full_output.cbz"

        result = cbz.create_cbz(sample_folder, output_file)

        assert result is True
        assert output_file.exists()
        assert output_file.stat().st_size > 1000000
