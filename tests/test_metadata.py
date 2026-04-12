"""Test metadata module."""

from bdlib.dto import ComicMetadata
from bdlib.metadata.path import extract_folder_metadata


class TestComicMetadata:
    """Test ComicMetadata dataclass."""

    def test_defaults(self):
        """Test default values."""
        meta = ComicMetadata()
        assert meta.title is None
        assert meta.series is None
        assert meta.number is None
        assert meta.writer is None

    def test_init_with_values(self):
        """Test initialization with values."""
        meta = ComicMetadata(
            title="The Killing Joke", series="Batman", number=1, writer="Alan Moore", artist="Brian Bolland", year=1988
        )
        assert meta.title == "The Killing Joke"
        assert meta.series == "Batman"
        assert meta.number == 1
        assert meta.writer == "Alan Moore"
        assert meta.artist == "Brian Bolland"
        assert meta.year == 1988

    def test_to_dict(self):
        """Test converting to dictionary."""
        meta = ComicMetadata(title="Test", number=1, writer="Author")
        result = meta.to_dict()

        assert result == {"title": "Test", "number": 1, "writer": "Author"}
        assert "series" not in result  # None values excluded

    def test_to_dict_empty(self):
        """Test converting empty metadata to dict."""
        meta = ComicMetadata()
        result = meta.to_dict()
        assert result == {}

    def test_partial_fields(self):
        """Test with partial field set."""
        meta = ComicMetadata(publisher="DC Comics", genre="Superhero")
        result = meta.to_dict()

        assert result["publisher"] == "DC Comics"
        assert result["genre"] == "Superhero"
        assert len(result) == 2


class TestExtractFolderMetadata:
    """Test folder metadata extraction."""

    def test_folder_with_title(self, tmp_path):
        """Test parsing folder with number and title."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "01 - Knightfall"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number == 1
        assert result.title == "Knightfall"

    def test_folder_with_number_only(self, tmp_path):
        """Test parsing folder with number only."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "01"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number == 1
        assert result.title is None

    def test_folder_vol_prefix(self, tmp_path):
        """Test parsing folder with Vol. prefix."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "Vol. 05"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number == 5
        assert result.title is None

    def test_folder_tome_prefix(self, tmp_path):
        """Test parsing folder with Tome prefix."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "Tome 03"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number == 3
        assert result.title is None

    def test_folder_volume_prefix(self, tmp_path):
        """Test parsing folder with volume prefix."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "Volume 12"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number == 12
        assert result.title is None

    def test_archive_with_number_only(self, tmp_path):
        """Test parsing archive stem with number only."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "_extracted"
        folder.mkdir(parents=True)
        archive = series_dir / "01.cbz"

        result = extract_folder_metadata(folder, archive_path=archive)

        assert result.series == "Batman"
        assert result.number == 1
        assert result.title is None

    def test_archive_with_title(self, tmp_path):
        """Test parsing archive stem with number and title."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "_extracted"
        folder.mkdir(parents=True)
        archive = series_dir / "01 - Knightfall.cbz"

        result = extract_folder_metadata(folder, archive_path=archive)

        assert result.series == "Batman"
        assert result.number == 1
        assert result.title == "Knightfall"

    def test_archive_vol_prefix(self, tmp_path):
        """Test parsing archive stem with Vol. prefix."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "_extracted"
        folder.mkdir(parents=True)
        archive = series_dir / "Vol. 05.cbz"

        result = extract_folder_metadata(folder, archive_path=archive)

        assert result.series == "Batman"
        assert result.number == 5
        assert result.title is None

    def test_folder_without_number(self, tmp_path):
        """Test parsing folder without recognizable number."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "Special"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.series == "Batman"
        assert result.number is None
        assert result.title is None

    def test_folder_multidigit_number(self, tmp_path):
        """Test parsing folder with multi-digit number."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "123 - The End"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.number == 123
        assert result.title == "The End"

    def test_folder_whitespace_handling(self, tmp_path):
        """Test parsing folder with extra whitespace."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "01   -   Knightfall"
        folder.mkdir(parents=True)

        result = extract_folder_metadata(folder)

        assert result.number == 1
        assert result.title == "Knightfall"


class TestCustomPatterns:
    """Test custom regex patterns for metadata extraction."""

    def test_custom_patterns_with_title(self, tmp_path):
        """Test custom pattern for title extraction."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "some_folder"
        folder.mkdir(parents=True)
        archive = series_dir / "01#Knightfall.cbz"

        patterns = (r"(\d+)#(.+)", r"^(\d+)$", r"T(\d+)")
        result = extract_folder_metadata(folder, archive_path=archive, patterns=patterns)

        assert result.number == 1
        assert result.title == "Knightfall"

    def test_custom_patterns_number_only(self, tmp_path):
        """Test custom pattern for number-only extraction."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "some_folder"
        folder.mkdir(parents=True)
        archive = series_dir / "#42.cbz"

        patterns = (r"(\d+)#(.+)", r"#(\d+)", r"T(\d+)")
        result = extract_folder_metadata(folder, archive_path=archive, patterns=patterns)

        assert result.number == 42
        assert result.title is None

    def test_custom_patterns_volume(self, tmp_path):
        """Test custom pattern for volume extraction."""
        series_dir = tmp_path / "Batman"
        folder = series_dir / "some_folder"
        folder.mkdir(parents=True)
        archive = series_dir / "T05.cbz"

        patterns = (r"(\d+)#(.+)", r"^(\d+)$", r"T(\d+)")
        result = extract_folder_metadata(folder, archive_path=archive, patterns=patterns)

        assert result.number == 5
        assert result.title is None

    def test_module_level_patterns_can_be_modified(self, tmp_path, monkeypatch):
        """Test that module-level patterns can be overridden."""
        from bdlib.metadata import path

        monkeypatch.setattr(path, "PATTERN_WITH_TITLE", r"(\d+)\s*#\s*(.+)")
        monkeypatch.setattr(path, "PATTERN_NUMBER_ONLY", r"#(\d+)")
        monkeypatch.setattr(path, "PATTERN_VOLUME", r"Vol\.(\d+)")

        series_dir = tmp_path / "Batman"
        folder = series_dir / "some_folder"
        folder.mkdir(parents=True)
        archive = series_dir / "01#Title.cbz"

        result = extract_folder_metadata(folder, archive_path=archive)

        assert result.number == 1
        assert result.title == "Title"
