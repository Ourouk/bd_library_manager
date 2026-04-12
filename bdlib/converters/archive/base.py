from abc import ABC, abstractmethod
from pathlib import Path


class ArchiveExtractor(ABC):
    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        """Supported file extensions including case variants."""
        pass

    @abstractmethod
    def extract(self, archive_path: Path, output_dir: Path) -> Path:
        """Extract archive to output_dir. Returns the extraction root path."""
        pass
