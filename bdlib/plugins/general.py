from argparse import ArgumentParser, Namespace
from pathlib import Path

from bdlib.cli import CliPlugin
from bdlib.cli.dto import ProcessingConfig


class GeneralPlugin(CliPlugin):
    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("input", help="Input folder, archive (.cbz/.cbr/.cb7), or directory containing them")
        parser.add_argument(
            "--single", action="store_true", help="Process single folder instead of batch of subfolders"
        )
        parser.add_argument(
            "-o", "--output-folder", type=Path, help="Output folder for CBZ files (default: same as input)"
        )

    def handle_arguments(self, args: Namespace) -> dict:
        return {"processing": ProcessingConfig(input=args.input, single=args.single, output_folder=args.output_folder)}
