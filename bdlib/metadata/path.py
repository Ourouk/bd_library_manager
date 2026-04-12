#!/usr/bin/env python3
"""
Extract metadata from folder structure or archive name.

Customization:
    Override module-level regex patterns to customize parsing behavior:

    >>> from bdlib.metadata import path
    >>> path.PATTERN_WITH_TITLE = r"(\\d+)\\s*#\\s*(.+)"
    >>> path.PATTERN_NUMBER_ONLY = r"#(\\d+)"
    >>> path.PATTERN_VOLUME = r"T(\\d+)"
"""

import re
from pathlib import Path
from typing import Tuple

from bdlib.dto import ComicMetadata

PATTERN_WITH_TITLE = r"(\d+)\s*-\s*(.+)"
PATTERN_NUMBER_ONLY = r"^(\d+)$"
PATTERN_VOLUME = r"(?:vol(?:ume)?\.?\s*|tome\s*|volume\s*)(\d+)"


def extract_folder_metadata(
    folder: Path, archive_path: Path | None = None, patterns: Tuple[str, str, str] | None = None
) -> ComicMetadata:
    """
    Extracts metadata from the folder structure or archive name.

    Args:
        folder (Path): The path to the comic folder.
        archive_path (Path, optional): Path to the original archive (if extracted).
        patterns (Tuple[str, str, str], optional): Custom regex patterns tuple of
            (with_title, number_only, volume). Defaults to module-level constants.

    Returns:
        ComicMetadata: An object containing the extracted metadata.

    Example:
        Override patterns for custom naming convention:

        >>> from bdlib.metadata import extract_folder_metadata
        >>> from pathlib import Path
        >>> meta = extract_folder_metadata(
        ...     Path("/series/01#Title"),
        ...     patterns=(r"(\\d+)#(.+)", r"#(\\d+)", r"T(\\d+)")
        ... )
    """
    series_name = folder.parent.name
    name_to_parse = archive_path.stem if archive_path else folder.name

    if patterns:
        pattern_title, pattern_number, pattern_volume = patterns
    else:
        pattern_title = PATTERN_WITH_TITLE
        pattern_number = PATTERN_NUMBER_ONLY
        pattern_volume = PATTERN_VOLUME

    dir_name_match = re.match(pattern_title, name_to_parse)

    if dir_name_match:
        number = int(dir_name_match.group(1))
        title = dir_name_match.group(2).strip()
    else:
        number_match = re.match(pattern_number, name_to_parse.strip())
        if number_match:
            number = int(number_match.group(1))
            title = None
        else:
            vol_match = re.match(pattern_volume, name_to_parse, re.I)
            if vol_match:
                number = int(vol_match.group(1))
                title = None
            else:
                number = None
                title = None

    return ComicMetadata(series=series_name, number=number, title=title)
