"""Metadata package for ComicInfo.xml generation."""

from bdlib.dto import PageInfo
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.path import extract_folder_metadata

__all__ = ["PageInfo", "extract_folder_metadata", "generate_comicinfo"]
