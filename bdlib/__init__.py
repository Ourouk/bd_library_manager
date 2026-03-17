"""BD Library Manager - Comic archive preparation tools."""

from bdlib.models import ComicMetadata
from bdlib.config import (
    config,
    get_api_key,
    set_api_key,
    get_cached_series,
    get_cached_series_info,
    cache_series_info,
)
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.comicvine import ComicVineClient, map_to_comicinfo, find_issue_by_number

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
