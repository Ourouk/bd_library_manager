#!/usr/bin/env python3
"""
Configuration management for BD Library Manager.
Stores API keys.
"""

import json
from pathlib import Path
from typing import Any

from bdlib.log import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path.home() / ".bd_library_manager"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    """Manages the application's configuration."""

    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.config: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            logger.info("Config file not found, creating a new one.")
            return {"comicvine_api_key": None}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config file: {e}")
            return {"comicvine_api_key": None}

    def _save(self) -> None:
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Error saving config file: {e}")

    def get_api_key(self) -> str | None:
        """Get Comic Vine API key."""
        return self.config.get("comicvine_api_key")

    def set_api_key(self, api_key: str) -> None:
        """Set Comic Vine API key."""
        self.config["comicvine_api_key"] = api_key
        self._save()


# Global config instance
config = Config()

get_api_key = config.get_api_key
set_api_key = config.set_api_key
