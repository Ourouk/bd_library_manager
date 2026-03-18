"""BD Library Manager - Comic archive preparation tools."""

from bdlib.config import (
    cache_series_info,
    config,
    get_api_key,
    get_cached_series,
    get_cached_series_info,
    set_api_key,
)
from bdlib.converters import cbz, jpeg_to_jxl
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.comicvine import ComicVineClient, find_issue_by_number, map_to_comicinfo
from bdlib.models import ComicMetadata

__all__ = [
    "ComicMetadata",
    "config",
    "get_api_key",
    "set_api_key",
    "get_cached_series",
    "get_cached_series_info",
    "cache_series_info",
    "jpeg_to_jxl",
    "cbz",
    "generate_comicinfo",
    "ComicVineClient",
    "map_to_comicinfo",
    "find_issue_by_number",
]
