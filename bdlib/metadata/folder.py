#!/usr/bin/env python3
"""
Extract metadata from folder structure.
"""

import re
from pathlib import Path

from bdlib.models import ComicMetadata


def extract_folder_metadata(folder: Path) -> ComicMetadata:
    """
    Extracts metadata from the folder structure.

    Args:
        folder (Path): The path to the comic folder.

    Returns:
        ComicMetadata: An object containing the extracted metadata.
    """
    series_name = folder.parent.name
    dir_name_match = re.match(r"(\d+)\s*-\s*(.+)", folder.name)

    if dir_name_match:
        number = int(dir_name_match.group(1))
        title = dir_name_match.group(2).strip()
    else:
        number = None
        title = None

    return ComicMetadata(
        series=series_name,
        number=number,
        title=title,
    )
