from pathlib import Path

from bdlib.converters.archive.base import ArchiveExtractor
from bdlib.converters.archive.cb7 import Cb7Extractor
from bdlib.converters.archive.cbr import CbrExtractor
from bdlib.converters.archive.cbz import CbzExtractor

ALL_EXTRACTORS: list[ArchiveExtractor] = [CbzExtractor(), CbrExtractor(), Cb7Extractor()]

SUPPORTED_EXTENSIONS: list[str] = []
for ext in ALL_EXTRACTORS:
    SUPPORTED_EXTENSIONS.extend(ext.extensions)


def is_archive(path: Path) -> bool:
    return path.is_file() and path.suffix in SUPPORTED_EXTENSIONS


def get_extractor(archive_path: Path) -> ArchiveExtractor | None:
    ext = archive_path.suffix
    for extractor in ALL_EXTRACTORS:
        if ext in extractor.extensions:
            return extractor
    return None


def extract_archive(archive_path: Path, output_dir: Path) -> Path:
    extractor = get_extractor(archive_path)
    if extractor is None:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
    return extractor.extract(archive_path, output_dir)
