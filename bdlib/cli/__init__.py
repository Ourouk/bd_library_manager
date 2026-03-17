from argparse import ArgumentParser, Namespace
from typing import Protocol, runtime_checkable


@runtime_checkable
class CliPlugin(Protocol):
    def register_arguments(self, parser: ArgumentParser) -> None: ...
    def handle_arguments(self, args: Namespace) -> dict: ...
