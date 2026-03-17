"""Integration tests using sample data."""

import pytest

from bdlib.converters import cbz
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.models import ComicMetadata


class TestWithSampleData:
    """Tests using the real sample comic folder."""

    def test_sample_folder_exists(self, sample_folder):
        """Verify sample folder exists and has images."""
        assert sample_folder.exists()
        images = list(sample_folder.glob("*.jpg"))
        assert len(images) > 0

    def test_sample_image_count(self, sample_folder):
        """Test that sample has expected number of images."""
        images = list(sample_folder.glob("*.jpg"))
        assert len(images) == 46

    def test_create_cbz_from_sample(self, sample_folder, tmp_path):
        """Test creating CBZ from sample folder."""
        output_file = tmp_path / "test.cbz"

        result = cbz.create_cbz(sample_folder, output_file)

        assert result is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_create_cbz_with_metadata_from_sample(self, sample_folder, tmp_path):
        """Test creating CBZ with ComicInfo.xml from sample."""
        comic_info = sample_folder / "ComicInfo.xml"

        metadata = ComicMetadata(
            title="Adieu le père",
            series="Avant l'Incal",
            number=1,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
        )
        xml = generate_comicinfo(metadata)
        comic_info.write_text(xml)

        output_file = tmp_path / "test_with_meta.cbz"

        result = cbz.create_cbz(sample_folder, output_file, comic_info)

        assert result is True

        import zipfile

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "ComicInfo.xml" in names

    def test_generate_comicinfo_parsing_sample_folder(self, sample_folder):
        """Test ComicInfo generation with sample folder metadata."""
        series = sample_folder.parent.name
        folder_name = sample_folder.name

        import re

        dir_name_match = re.match(r"(\d+)\s*-\s*(.+)", folder_name)
        number = int(dir_name_match.group(1)) if dir_name_match else None
        title = dir_name_match.group(2).strip() if dir_name_match else None

        metadata = ComicMetadata(
            title=title,
            series=series,
            number=number,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
        )
        xml = generate_comicinfo(metadata)

        assert "<Series>Avant l'Incal</Series>" in xml
        assert "<Number>1</Number>" in xml
        assert "<Title>Adieu le père</Title>" in xml

    def test_comic_metadata_from_sample(self, sample_folder):
        """Test ComicMetadata with sample data."""
        meta = ComicMetadata(
            series="Avant l'Incal",
            number=1,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
            publisher="Les Humanoïdes Associés",
            year=1981,
            summary="Premier tome de la série Avant l'Incal.",
        )

        xml = generate_comicinfo(meta)

        assert "<Series>Avant l'Incal</Series>" in xml
        assert "<Number>1</Number>" in xml
        assert "<Writer>Alexandro Jodorowsky</Writer>" in xml
        assert "<Artist>Moebius</Artist>" in xml
        assert "<Publisher>Les Humanoïdes Associés</Publisher>" in xml
        assert "<Year>1981</Year>" in xml

    def test_sample_series_folder_structure(self, sample_series_folder):
        """Test the sample series folder structure."""
        assert sample_series_folder.exists()
        assert sample_series_folder.name == "Avant l'Incal"

        issues = [d for d in sample_series_folder.iterdir() if d.is_dir()]
        assert len(issues) == 1
        assert issues[0].name == "01 - Adieu le père"
