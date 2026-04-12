"""Test configuration module."""

import tempfile
from pathlib import Path

import pytest

from bdlib.config import Config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "config.json"
        yield test_file


class TestConfig:
    """Test configuration functions."""

    def test_load_config_default(self, temp_config_file):
        """Test loading config returns defaults when file doesn't exist."""
        cfg = Config(config_path=temp_config_file)
        assert cfg.get_api_key() is None

    def test_load_config_existing(self, temp_config_file):
        """Test loading config from existing file."""
        temp_config_file.write_text('{"comicvine_api_key": "test123"}')

        cfg = Config(config_path=temp_config_file)
        assert cfg.get_api_key() == "test123"

    def test_save_and_load_config(self, temp_config_file):
        """Test saving and loading config."""
        cfg = Config(config_path=temp_config_file)
        test_config = {"comicvine_api_key": "mykey"}
        cfg.config = test_config
        cfg._save()

        new_cfg = Config(config_path=temp_config_file)
        assert new_cfg.get_api_key() == "mykey"

    def test_get_api_key(self, temp_config_file):
        """Test getting API key."""
        cfg = Config(config_path=temp_config_file)
        cfg.set_api_key("testkey")
        assert cfg.get_api_key() == "testkey"

    def test_set_api_key(self, temp_config_file):
        """Test setting API key."""
        cfg = Config(config_path=temp_config_file)
        cfg.set_api_key("newkey")
        assert cfg.get_api_key() == "newkey"
