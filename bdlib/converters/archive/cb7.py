from pathlib import Path

import py7zr

from bdlib.converters.archive.base import ArchiveExtractor


class Cb7Extractor(ArchiveExtractor):
    @property
    def extensions(self) -> list[str]:
        return [".cb7", ".CB7"]

    def extract(self, archive_path: Path, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        with py7zr.SevenZipFile(archive_path, "r") as szf:
            szf.extractall(output_dir)
        return output_dir
