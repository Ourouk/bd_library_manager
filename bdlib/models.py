#!/usr/bin/env python3
"""
Comic metadata classes for BD Library Manager.
"""

from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class PageInfo:
    """Information about a single page from conversion."""

    filename: str
    width: int
    height: int
    size: int
    double_page: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ConversionResult:
    """Result of a batch conversion."""

    success: bool
    pages: List[PageInfo]
    total_duration_ms: int


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
    denoise_model: Optional[str] = None
    denoise_noise_level: Optional[int] = None
    denoise_scale_factor: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def merge(self, other: "ComicMetadata") -> "ComicMetadata":
        """
        Merge another ComicMetadata object into this one.
        Fields from the other object will only be used if the corresponding field in this object is None.
        """
        for k, v in asdict(other).items():
            if getattr(self, k) is None and v is not None:
                setattr(self, k, v)
        return self
