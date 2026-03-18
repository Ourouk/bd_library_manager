from argparse import ArgumentParser, Namespace
from typing import Any, Optional

from bdlib.cli.dto import MetadataConfig
from bdlib.config import get_api_key, set_api_key
from bdlib.metadata.comicvine import ComicVineClient
from bdlib.plugins.metadata import MetadataPlugin


class ComicVinePlugin(MetadataPlugin):
    @property
    def name(self) -> str:
        return "comicvine"

    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--comicvine",
            action="store_true",
            help="Enrich metadata using Comic Vine API (requires API key)",
        )
        parser.add_argument(
            "--country", type=str, help="Country code for ComicInfo.xml (e.g., FR, US, GB)"
        )
        parser.add_argument(
            "--language", type=str, help="Language ISO code for ComicInfo.xml (e.g., fr, en, es)"
        )

    def handle_arguments(self, args: Namespace) -> dict:
        enabled_sources = []
        if args.comicvine:
            enabled_sources.append(self.name)

        return {
            "metadata": MetadataConfig(
                enabled_sources=enabled_sources,
                country=args.country,
                language=args.language,
            )
        }

    def create_client(self, config: MetadataConfig) -> Optional[Any]:
        if self.name not in config.enabled_sources:
            return None

        api_key = get_api_key()

        if not api_key:
            print("\\n=== Comic Vine API Setup ===")
            print("You need a free API key from https://comicvine.gamespot.com/api/")
            api_key = input("Enter your Comic Vine API key: ").strip()
            if api_key:
                set_api_key(api_key)
                print("API key saved!")
            else:
                print("No API key provided, Comic Vine lookup disabled.")
                return None

        try:
            return ComicVineClient(api_key)
        except Exception as e:
            print(f"Failed to initialize Comic Vine client: {e}")
            return None
