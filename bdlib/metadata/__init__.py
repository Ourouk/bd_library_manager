"""Metadata package for ComicInfo.xml generation."""

from bdlib.metadata.comicinfo import generate_comicinfo, get_image_info
from bdlib.metadata.folder import extract_folder_metadata

__all__ = [
    "generate_comicinfo",
    "get_image_info",
    "extract_folder_metadata",
]
