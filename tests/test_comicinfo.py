"""Test ComicInfo.xml generation."""

import zipfile

from bdlib.converters import cbz
from bdlib.dto import ComicMetadata, PageInfo
from bdlib.metadata.comicinfo import generate_comicinfo


class TestGenerateComicinfo:
    """Test ComicInfo.xml generation."""

    def test_empty_generates_minimal_xml(self):
        """Test minimal XML output."""
        result = generate_comicinfo(ComicMetadata())
        assert '<?xml version="1.0"' in result
        assert "<ComicInfo " in result or "<ComicInfo>" in result
        assert "</ComicInfo>" in result

    def test_simple_fields(self):
        """Test generating with simple fields."""
        metadata = ComicMetadata(title="Batman #1", series="Batman", number=1, year=1940)
        result = generate_comicinfo(metadata)
        assert "<Title>Batman #1</Title>" in result
        assert "<Series>Batman</Series>" in result
        assert "<Number>1</Number>" in result
        assert "<Year>1940</Year>" in result

    def test_all_fields(self):
        """Test generating with all fields."""
        metadata = ComicMetadata(
            title="Test",
            series="Series",
            number=1,
            count=10,
            volume=2,
            writer="Writer",
            artist="Artist",
            colorist="Colorist",
            inker="Inker",
            letterer="Letterer",
            cover_artist="Cover",
            editor="Editor",
            publisher="Publisher",
            imprint="Imprint",
            genre="Genre",
            summary="Summary text",
            year=2020,
            month=6,
            day=15,
            web="https://example.com",
            isbn="123456789",
            notes="Notes",
            language="en",
            country="US",
            rating=5,
        )
        result = generate_comicinfo(metadata)
        assert "<Title>Test</Title>" in result
        assert "<Writer>Writer</Writer>" in result
        assert "<Artist>Artist</Artist>" in result
        assert "<Publisher>Publisher</Publisher>" in result
        assert "<Summary>Summary text</Summary>" in result
        assert "<Language>en</Language>" in result

    def test_metadata_object(self):
        """Test using ComicMetadata object."""
        meta = ComicMetadata(title="From Object", series="Test Series", number=5, writer="Author", year=2021)
        result = generate_comicinfo(meta)

        assert "<Title>From Object</Title>" in result
        assert "<Series>Test Series</Series>" in result
        assert "<Number>5</Number>" in result
        assert "<Writer>Author</Writer>" in result

    def test_optional_fields_not_included(self):
        """Test optional fields are not included when None."""
        result = generate_comicinfo(ComicMetadata(title="Test"))

        assert "<Series>" not in result
        assert "<Number>" not in result
        assert "<Writer>" not in result


class TestPageFiles:
    """Test page files handling."""

    def test_pages_xml_generation(self, temp_image_folder):
        """Test page files generate Pages section."""
        page_infos = [
            PageInfo(filename="01.jpg", width=1920, height=2492, size=100000),
            PageInfo(filename="02.jpg", width=1920, height=2492, size=100000),
        ]

        result = generate_comicinfo(ComicMetadata(title="Test"), page_infos=page_infos)

        assert "<Pages>" in result
        assert "</Pages>" in result
        assert 'Image="0"' in result
        assert 'Image="1"' in result

    def test_pages_with_real_dimensions(self):
        """Test pages section with PageInfo."""
        page_infos = [
            PageInfo(filename="01.jpg", width=1920, height=2492, size=100000),
            PageInfo(filename="02.jpg", width=1920, height=2492, size=100000),
            PageInfo(filename="03.jpg", width=3000, height=2000, size=150000),
        ]

        result = generate_comicinfo(ComicMetadata(title="Avant l'Incal"), page_infos=page_infos)

        assert "<Pages>" in result
        assert 'Image="0"' in result
        assert 'Image="1"' in result
        assert 'Image="2"' in result
        assert 'ImageWidth="1920"' in result
        assert 'ImageHeight="2492"' in result

    def test_comicinfo_in_cbz(self, temp_image_folder, tmp_path):
        """Test that ComicInfo.xml is properly generated and can be included in CBZ."""
        metadata = ComicMetadata(title="Test Comic", series="Test Series", number=1, writer="Test Writer", year=2024)
        xml = generate_comicinfo(metadata)
        comic_info_path = temp_image_folder / "ComicInfo.xml"
        comic_info_path.write_text(xml)

        output_file = tmp_path / "test.cbz"
        cbz.create_cbz(temp_image_folder, output_file, comic_info_path)

        with zipfile.ZipFile(output_file, "r") as zf:
            content = zf.read("ComicInfo.xml").decode("utf-8")
            assert "<Title>Test Comic</Title>" in content
            assert "<Series>Test Series</Series>" in content
