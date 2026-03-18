import zipfile
from pathlib import Path
from typing import List

from bdlib.converters.archive.base import ArchiveExtractor


class CbzExtractor(ArchiveExtractor):
    @property
    def extensions(self) -> List[str]:
        return [".cbz", ".CBZ"]

    def extract(self, archive_path: Path, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(output_dir)
        return output_dir
