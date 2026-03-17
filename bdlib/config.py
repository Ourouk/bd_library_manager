#!/usr/bin/env python3
"""
Configuration management for BD Library Manager.
Stores API keys and cached series data.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from bdlib.log import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path.home() / ".bd_library_manager"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    """Manages the application's configuration."""

    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.config: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            logger.info("Config file not found, creating a new one.")
            return {"comicvine_api_key": None, "cached_series": {}}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config file: {e}")
            return {"comicvine_api_key": None, "cached_series": {}}

    def _save(self) -> None:
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Error saving config file: {e}")

    def get_api_key(self) -> Optional[str]:
        """Get Comic Vine API key."""
        return self.config.get("comicvine_api_key")

    def set_api_key(self, api_key: str) -> None:
        """Set Comic Vine API key."""
        self.config["comicvine_api_key"] = api_key
        self._save()

    def get_cached_series(self) -> Dict[str, Any]:
        """Get cached series data."""
        return self.config.get("cached_series", {})

    def get_cached_series_info(self, series_name: str) -> Optional[Dict[str, Any]]:
        """Get cached info for a specific series."""
        return self.get_cached_series().get(series_name)

    def cache_series_info(self, series_name: str, info: Dict[str, Any]) -> None:
        """Cache series information for future lookups."""
        if "cached_series" not in self.config:
            self.config["cached_series"] = {}
        self.config["cached_series"][series_name] = info
        self._save()


# Global config instance
config = Config()

get_api_key = config.get_api_key
set_api_key = config.set_api_key
get_cached_series = config.get_cached_series
get_cached_series_info = config.get_cached_series_info
cache_series_info = config.cache_series_info
