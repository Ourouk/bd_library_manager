"""Test ComicInfo.xml generation."""

import tempfile
from pathlib import Path

import pytest

from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.models import ComicMetadata


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
        metadata = ComicMetadata(
            title="Batman #1",
            series="Batman",
            number=1,
            year=1940,
        )
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
        meta = ComicMetadata(
            title="From Object",
            series="Test Series",
            number=5,
            writer="Author",
            year=2021,
        )
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

    def test_pages_xml_generation(self):
        """Test page files generate Pages section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_dir = Path(tmpdir)

            # Create dummy files
            (img_dir / "page1.jpg").write_bytes(b"x")
            (img_dir / "page2.jpg").write_bytes(b"x")

            result = generate_comicinfo(
                ComicMetadata(title="Test"),
                page_files=[img_dir / "page1.jpg", img_dir / "page2.jpg"],
            )

            assert "<Pages>" in result
            assert "</Pages>" in result
            assert 'Image="0"' in result
            assert 'Image="1"' in result
