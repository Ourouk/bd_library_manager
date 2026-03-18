from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class ConverterConfig:
    quality: int = 90
    lossless: bool = False
    keep_jxl: bool = False
    threads: int = 4
    jxl_threads: int = 4
    dejpeg: bool = False
    dejpeg_model: str = "fbcnn_color"


@dataclass
class MetadataConfig:
    enabled_sources: List[str] = field(default_factory=list)
    country: Optional[str] = None
    language: Optional[str] = None
    client: Optional[Any] = None


@dataclass
class ProcessingConfig:
    input: str
    output_folder: Optional[Path] = None
    single: bool = False
    threads: int = 4
