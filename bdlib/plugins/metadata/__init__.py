from typing import Any, Optional

from bdlib.cli import CliPlugin
from bdlib.cli.dto import MetadataConfig


class MetadataPlugin(CliPlugin):
    @property
    def name(self) -> str:
        raise NotImplementedError

    def create_client(self, config: MetadataConfig) -> Optional[Any]:
        raise NotImplementedError
