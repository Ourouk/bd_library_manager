from argparse import ArgumentParser, Namespace
from bdlib.cli import CliPlugin
from bdlib.cli.dto import ConverterConfig


class ConverterPlugin(CliPlugin):
    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-q", "--quality", type=int, default=90, help="JXL quality 1-100 (default: 90)"
        )
        parser.add_argument(
            "-l",
            "--lossless",
            action="store_true",
            help="Use lossless compression (default: lossy)",
        )
        parser.add_argument(
            "-k",
            "--keep-jxl",
            action="store_true",
            help="Keep intermediate JXL files after creating CBZ",
        )
        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            default=4,
            help="Number of threads for JXL conversion (default: 4)",
        )

    def handle_arguments(self, args: Namespace) -> dict:
        return {
            "converter": ConverterConfig(
                quality=args.quality,
                lossless=args.lossless,
                keep_jxl=args.keep_jxl,
                threads=args.threads,
            )
        }
