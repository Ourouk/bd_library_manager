import subprocess
from pathlib import Path
from typing import List

from bdlib.converters.archive.base import ArchiveExtractor


class CbrExtractor(ArchiveExtractor):
    @property
    def extensions(self) -> List[str]:
        return [".cbr", ".CBR"]

    def extract(self, archive_path: Path, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            import rarfile

            with rarfile.RarFile(archive_path) as rf:
                rf.extractall(output_dir)
        except ImportError:
            try:
                subprocess.run(
                    ["unrar", "x", str(archive_path), str(output_dir)],
                    check=True,
                    capture_output=True,
                )
            except FileNotFoundError:
                raise ImportError(
                    "RAR extraction requires 'unrar' system package and 'rarfile' Python package. "
                    "Install with: pip install bdlib[cbr] && apt install unrar"
                )
        return output_dir
