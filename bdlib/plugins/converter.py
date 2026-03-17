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
            "--dejpeg-threads",
            type=int,
            default=1,
            help="Number of threads for DeJPEG (default: 1, use 1 for CUDA)",
        )
        parser.add_argument(
            "--dejpeg",
            action="store_true",
            help="Remove JPEG artifacts using FBCNN model before conversion",
        )
        parser.add_argument(
            "--dejpeg-model",
            type=str,
            default="fbcnn_color",
            choices=["fbcnn_color"],
            help="DeJPEG model to use (default: fbcnn_color)",
        )

    def handle_arguments(self, args: Namespace) -> dict:
        return {
            "converter": ConverterConfig(
                quality=args.quality,
                lossless=args.lossless,
                keep_jxl=args.keep_jxl,
                threads=args.dejpeg_threads,
                jxl_threads=4,  # JXL always uses 4 threads on CPU
                dejpeg=args.dejpeg,
                dejpeg_model=args.dejpeg_model,
            )
        }
