#!/usr/bin/env python3
"""
Configuration management for BD Library Manager.
Stores API keys and cached series data.
"""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".bd_library_manager"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {
            "comicvine_api_key": None,
            "cached_series": {}
        }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "comicvine_api_key": None,
            "cached_series": {}
        }


def save_config(config: dict) -> None:
    """Save configuration to file."""
    get_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_key() -> Optional[str]:
    """Get Comic Vine API key."""
    config = load_config()
    return config.get("comicvine_api_key")


def set_api_key(api_key: str) -> None:
    """Set Comic Vine API key."""
    config = load_config()
    config["comicvine_api_key"] = api_key
    save_config(config)


def get_cached_series() -> dict:
    """Get cached series data."""
    config = load_config()
    return config.get("cached_series", {})


def get_cached_series_info(series_name: str) -> Optional[dict]:
    """Get cached info for a specific series."""
    cached = get_cached_series()
    return cached.get(series_name)


def cache_series_info(series_name: str, info: dict) -> None:
    """Cache series information for future lookups."""
    config = load_config()
    if "cached_series" not in config:
        config["cached_series"] = {}
    config["cached_series"][series_name] = info
    save_config(config)
