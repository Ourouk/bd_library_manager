"""Comic Vine API client package."""

from bdlib.metadata.comicvine.client import (
    ComicVineClient,
    confirm_series,
    find_issue_by_number,
    map_to_comicinfo,
    normalize_issue_number,
)

__all__ = ["ComicVineClient", "confirm_series", "find_issue_by_number", "map_to_comicinfo", "normalize_issue_number"]
