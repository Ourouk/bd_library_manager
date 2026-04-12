"""Test archive extraction."""

import zipfile
from pathlib import Path

from bdlib.converters.archive import SUPPORTED_EXTENSIONS, get_extractor, is_archive
from bdlib.converters.archive.cb7 import Cb7Extractor
from bdlib.converters.archive.cbr import CbrExtractor
from bdlib.converters.archive.cbz import CbzExtractor


class TestArchiveFactory:
    """Test archive factory functions."""

    def test_supported_extensions_contains_all(self):
        assert ".cbz" in SUPPORTED_EXTENSIONS
        assert ".cbr" in SUPPORTED_EXTENSIONS
        assert ".cb7" in SUPPORTED_EXTENSIONS

    def test_is_archive_cbz(self, sample_cbz_archive):
        assert is_archive(sample_cbz_archive) is True

    def test_is_archive_cbr(self, sample_cbr_archive):
        assert is_archive(sample_cbr_archive) is True

    def test_is_archive_case_insensitive(self, sample_cbz_archive, tmp_path):
        upper_case = tmp_path / "test.CBZ"
        upper_case.write_bytes(sample_cbz_archive.read_bytes())
        assert is_archive(upper_case) is True

    def test_is_archive_false_for_folder(self, tmp_path):
        folder = tmp_path / "test_folder"
        folder.mkdir()
        assert is_archive(folder) is False

    def test_is_archive_false_for_regular_file(self, tmp_path):
        file = tmp_path / "test.txt"
        file.write_text("hello")
        assert is_archive(file) is False

    def test_get_extractor_cbz(self):
        extractor = get_extractor(Path("test.cbz"))
        assert extractor is not None
        assert isinstance(extractor, CbzExtractor)

    def test_get_extractor_cbr(self):
        extractor = get_extractor(Path("test.cbr"))
        assert extractor is not None
        assert isinstance(extractor, CbrExtractor)

    def test_get_extractor_cb7(self):
        extractor = get_extractor(Path("test.cb7"))
        assert extractor is not None
        assert isinstance(extractor, Cb7Extractor)

    def test_get_extractor_unsupported(self):
        assert get_extractor(Path("test.zip")) is None
        assert get_extractor(Path("test.rar")) is None


class TestCbzExtractor:
    """Test CBZ archive extraction."""

    def test_extract_cbz_creates_directory(self, tmp_path, sample_cbz_archive):
        extractor = CbzExtractor()
        output_dir = tmp_path / "extracted"

        result = extractor.extract(sample_cbz_archive, output_dir)

        assert result == output_dir
        assert output_dir.exists()

    def test_extract_cbz_contains_images(self, tmp_path, sample_cbz_archive):
        extractor = CbzExtractor()
        output_dir = tmp_path / "extracted"

        extractor.extract(sample_cbz_archive, output_dir)

        images = list(output_dir.glob("**/*.jpg")) + list(output_dir.glob("**/*.jpeg"))
        images += list(output_dir.glob("**/*.JPG")) + list(output_dir.glob("**/*.JPEG"))
        assert len(images) > 0

    def test_cbz_is_valid_zip(self, sample_cbz_archive):
        with zipfile.ZipFile(sample_cbz_archive, "r") as zf:
            assert zf.testzip() is None


class TestCbrExtractor:
    """Test CBR archive extraction."""

    def test_extensions(self):
        extractor = CbrExtractor()
        assert ".cbr" in extractor.extensions
        assert ".CBR" in extractor.extensions


class TestCb7Extractor:
    """Test CB7 archive extraction."""

    def test_extensions(self):
        extractor = Cb7Extractor()
        assert ".cb7" in extractor.extensions
        assert ".CB7" in extractor.extensions
