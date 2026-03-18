"""Test metadata module."""


from bdlib import ComicMetadata


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
            title="The Killing Joke",
            series="Batman",
            number=1,
            writer="Alan Moore",
            artist="Brian Bolland",
            year=1988,
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
