"""BD Library Manager - Comic archive preparation tools."""

from bdlib.config import cache_series_info, config, get_api_key, get_cached_series, get_cached_series_info, set_api_key
from bdlib.converters import cbz, jpeg_to_jxl
from bdlib.dto import ComicMetadata
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.comicvine import ComicVineClient, find_issue_by_number, map_to_comicinfo

__all__ = [
    "ComicMetadata",
    "ComicVineClient",
    "cache_series_info",
    "cbz",
    "config",
    "find_issue_by_number",
    "generate_comicinfo",
    "get_api_key",
    "get_cached_series",
    "get_cached_series_info",
    "jpeg_to_jxl",
    "map_to_comicinfo",
    "set_api_key",
]
