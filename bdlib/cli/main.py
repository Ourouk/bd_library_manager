#!/usr/bin/env python3
"""
Command-line interface for BD Library Manager.
"""

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Any

from bdlib.cli.dto import ConverterConfig, MetadataConfig, ProcessingConfig
from bdlib.converters import cbz, dejpeg, jpeg_to_jxl
from bdlib.converters.archive import is_archive
from bdlib.dto import ComicMetadata
from bdlib.log import get_logger
from bdlib.metadata import extract_folder_metadata
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata.comicvine import confirm_series, find_issue_by_number, map_to_comicinfo
from bdlib.plugins import discover_plugins
from bdlib.plugins.metadata import MetadataPlugin

logger = get_logger(__name__)


def handle_not_found(series_name: str, number: str) -> str:
    """Prompt user for action when comic not found in Comic Vine."""
    logger.warning(f"Comic not found in Comic Vine: {series_name} #{number}")
    print("    1. Skip (use folder metadata only)")
    print("    2. Enter summary manually")
    print("    3. Use partial data (year, publisher only)")

    while True:
        choice = input("  Choice [1]: ").strip() or "1"

        if choice == "1":
            return "skip"
        elif choice == "2":
            return "manual"
        elif choice == "3":
            return "partial"
        print("  Invalid choice. Enter 1, 2, or 3.")


def get_comicvine_metadata(
    series_name: str | None, number: str, metadata_config: MetadataConfig, series_cache: dict[str, Any]
) -> ComicMetadata | None:
    """
    Get metadata from Comic Vine.
    """
    comicvine_client = metadata_config.client
    if not comicvine_client:
        return None

    if not series_name:
        return None

    if series_name in series_cache:
        cached = series_cache[series_name]
        if cached.get("skip"):
            logger.info("Skipping Comic Vine lookup (marked as skip)")
            return None

        logger.info(f"Using cached series: {cached['name']}")
        issues = cached.get("issues", [])
        issue = find_issue_by_number(issues, number) if issues and number is not None else None

        if issue:
            logger.info(f"Found issue #{number}: {issue.get('name', 'N/A')}")
            issue_data = comicvine_client.get_issue(issue["id"])
            volume_data = comicvine_client.get_volume(cached.get("id"))
            return map_to_comicinfo(issue_data, volume_data)
        else:
            logger.warning(f"Issue #{number} not found in series")
            return None

    logger.info("Series not cached, searching Comic Vine...")

    series_info = confirm_series(comicvine_client, series_name)

    if series_info and series_info.get("skip_all"):
        series_cache[series_name] = {"skip": True, "name": series_name}
        logger.info(f"Skipping Comic Vine for series: {series_name}")
        return None
    elif series_info:
        logger.info(f"Fetching issues for {series_info['name']}...")
        volume_id = series_info["id"]
        volume_data = comicvine_client.get_volume(volume_id)
        issues = comicvine_client.get_volume_issues(volume_id)
        logger.info(f"Found {len(issues)} issues")

        series_cache[series_name] = {"id": volume_id, "name": series_info["name"], "issues": issues}

        issue = find_issue_by_number(issues, number) if number is not None else None
        if issue:
            logger.info(f"Found issue #{number}: {issue.get('name', 'N/A')}")
            issue_data = comicvine_client.get_issue(issue["id"])
            return map_to_comicinfo(issue_data, volume_data)
        else:
            logger.warning(f"Issue #{number} not found in series")
            return None

    return None


def find_inputs(input_path: Path, single: bool) -> list[Path]:
    """Find folders or archives to process."""
    if single:
        return [input_path]
    elif input_path.is_dir():
        items = []
        for item in input_path.iterdir():
            if item.is_dir() and not is_archive(item):
                items.append(item)
            elif is_archive(item):
                items.append(item)
        return sorted(items, key=lambda p: p.name)
    elif is_archive(input_path):
        return [input_path.parent]
    elif input_path.is_dir() and not any(input_path.glob("*.jpg")):
        return sorted([d for d in input_path.iterdir() if d.is_dir()])
    else:
        return [input_path.parent]


def process_folder(
    folder: Path,
    processing_config: ProcessingConfig,
    converter_config: ConverterConfig,
    metadata_config: MetadataConfig,
    series_cache: dict[str, Any] | None = None,
    archive_path: Path | None = None,
):
    """Process a single folder of JPEG images to create a JXL-based CBZ archive."""
    logger.info(f"Processing: {folder.name}")

    jpeg_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
    jpeg_files += list(folder.glob("*.JPG")) + list(folder.glob("*.JPEG"))

    if not jpeg_files:
        logger.warning("No JPEG files found, skipping...")
        return False

    folder_metadata = extract_folder_metadata(folder, archive_path)

    cv_metadata = None
    if metadata_config.client and series_cache is not None:
        cv_metadata = get_comicvine_metadata(
            folder_metadata.series, str(folder_metadata.number), metadata_config, series_cache
        )

    metadata = folder_metadata
    if cv_metadata:
        metadata = metadata.merge(cv_metadata)

    jxl_folder = folder.parent / f"{folder.name}_jxl"
    jxl_folder.mkdir(parents=True, exist_ok=True)

    dejpeg_result = None
    if converter_config.dejpeg:
        logger.info(f"Removing JPEG artifacts from {len(jpeg_files)} files using {converter_config.dejpeg_model}...")

        try:
            dejpeg_result = dejpeg.batch_convert(
                folder,
                jxl_folder,
                max_threads=converter_config.threads,
                model_string=converter_config.dejpeg_model,
                output_jxl=True,
                jxl_quality=converter_config.quality,
                jxl_lossless=converter_config.lossless,
            )
            logger.info("JPEG artifact removal completed")
        except Exception as e:
            logger.error(f"DeJPEG processing failed: {e}")
            return False
    else:
        logger.info(f"Converting {len(jpeg_files)} images to JXL...")
        try:
            jpeg_to_jxl.batch_convert(
                folder, jxl_folder, converter_config.quality, converter_config.lossless, converter_config.jxl_threads
            )
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False

    logger.info("Generating ComicInfo.xml...")

    page_infos = None
    denoise_info = None

    if converter_config.dejpeg and dejpeg_result and dejpeg_result.success:
        page_infos = dejpeg_result.pages
        denoise_info = dejpeg_result.config
    elif not converter_config.dejpeg:
        page_files = list(jxl_folder.glob("*.jxl")) + list(jxl_folder.glob("*.JXL"))
        page_files.sort()
        if page_files:
            from bdlib.dto import PageInfo

            page_infos = []
            for pf in page_files:
                size = pf.stat().st_size
                page_infos.append(PageInfo(filename=pf.name, width=0, height=0, size=size))

    try:
        xml = generate_comicinfo(metadata, page_infos=page_infos, denoise_info=denoise_info)
        comicinfo_path = jxl_folder / "ComicInfo.xml"
        comicinfo_path.write_text(xml, encoding="utf-8")
    except Exception as e:
        logger.error(f"Metadata generation failed: {e}")
        return False

    logger.info("Creating CBZ archive...")
    if processing_config.output_folder:
        cbz_path = processing_config.output_folder / f"{folder.name}.cbz"
    else:
        cbz_path = folder.parent / f"{folder.name}.cbz"
    try:
        cbz.create_cbz(jxl_folder, cbz_path, jxl_folder / "ComicInfo.xml")
    except Exception as e:
        logger.error(f"CBZ creation failed: {e}")
        return False

    if not converter_config.keep_jxl:
        logger.info("Cleaning up JXL folder...")
        shutil.rmtree(jxl_folder)

    logger.info(f"Done: {cbz_path.name}")

    return True


def process_archive(
    archive: Path,
    processing_config: ProcessingConfig,
    converter_config: ConverterConfig,
    metadata_config: MetadataConfig,
    series_cache: dict[str, Any] | None = None,
):
    """Extract archive and process images to create a JXL-based CBZ."""
    from bdlib.converters.archive import extract_archive

    logger.info(f"Extracting archive: {archive.name}")

    archive_stem = archive.stem

    try:
        with tempfile.TemporaryDirectory(prefix="bdlib_") as temp_dir:
            extract_dir = Path(temp_dir) / archive_stem
            extract_archive(archive, extract_dir)

            logger.info(f"Processing extracted archive: {archive_stem}")
            result = process_folder(
                extract_dir, processing_config, converter_config, metadata_config, series_cache, archive_path=archive
            )
            return result
    except ImportError as e:
        logger.error(f"Missing dependency for archive extraction: {e}")
        return False
    except Exception as e:
        logger.error(f"Archive processing failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Batch process comic folders")

    plugins = discover_plugins()
    for plugin in plugins:
        plugin.register_arguments(parser)

    args = parser.parse_args()

    config: dict[str, Any] = {}
    for plugin in plugins:
        config.update(plugin.handle_arguments(args))

    processing_config: ProcessingConfig = config["processing"]
    converter_config: ConverterConfig = config["converter"]
    metadata_config: MetadataConfig = config["metadata"]

    for plugin in plugins:
        if isinstance(plugin, MetadataPlugin):
            client = plugin.create_client(metadata_config)
            if client:
                metadata_config.client = client
                break

    folders = find_inputs(Path(processing_config.input), processing_config.single)
    logger.info(f"Found {len(folders)} item(s) to process")

    series_cache: dict[str, Any] = {}

    success = 0
    for item in folders:
        if is_archive(item):
            result = process_archive(item, processing_config, converter_config, metadata_config, series_cache)
        else:
            result = process_folder(item, processing_config, converter_config, metadata_config, series_cache)
        if result:
            success += 1

    logger.info(f"Completed: {success}/{len(folders)} items processed")


if __name__ == "__main__":
    main()
