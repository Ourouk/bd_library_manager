"""Metadata package for ComicInfo.xml generation."""

from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.folder import extract_folder_metadata
from bdlib.models import PageInfo

__all__ = [
    "generate_comicinfo",
    "extract_folder_metadata",
    "PageInfo",
]
