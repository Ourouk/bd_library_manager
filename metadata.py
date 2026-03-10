#!/usr/bin/env python3
"""
Comic metadata classes for BD Library Manager.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ComicMetadata:
    title: Optional[str] = None
    series: Optional[str] = None
    number: Optional[int] = None
    count: Optional[int] = None
    volume: Optional[int] = None
    alternate_series: Optional[str] = None
    alternate_number: Optional[int] = None
    alternate_count: Optional[int] = None
    writer: Optional[str] = None
    artist: Optional[str] = None
    colorist: Optional[str] = None
    inker: Optional[str] = None
    letterer: Optional[str] = None
    cover_artist: Optional[str] = None
    editor: Optional[str] = None
    publisher: Optional[str] = None
    imprint: Optional[str] = None
    genre: Optional[str] = None
    summary: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    web: Optional[str] = None
    isbn: Optional[str] = None
    notes: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[int] = None
    format: Optional[str] = None
    black_and_white: Optional[str] = None
    manga: Optional[str] = None
    pages: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}
