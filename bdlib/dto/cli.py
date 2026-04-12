"""CLI-related Data Transfer Objects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConverterConfig:
    """Configuration for image conversion."""

    quality: int = 90
    lossless: bool = False
    keep_jxl: bool = False
    threads: int = 4
    jxl_threads: int = 4
    dejpeg: bool = False
    dejpeg_model: str = "fbcnn_color"


@dataclass
class MetadataConfig:
    """Configuration for metadata enrichment."""

    enabled_sources: list[str] = field(default_factory=list)
    country: str | None = None
    language: str | None = None
    client: Any | None = None


@dataclass
class ProcessingConfig:
    """Configuration for input/output processing."""

    input: str
    output_folder: Path | None = None
    single: bool = False
    threads: int = 4
