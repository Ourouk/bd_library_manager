#!/usr/bin/env python3
"""
Command-line interface for BD Library Manager.
"""

import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import shutil

from bdlib.config import cache_series_info, get_cached_series
from bdlib.metadata.comicvine import map_to_comicinfo, find_issue_by_number, confirm_series
from bdlib.converters import jpeg_to_jxl, cbz, dejpeg
from bdlib.metadata import extract_folder_metadata
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.plugins import discover_plugins
from bdlib.cli.dto import ProcessingConfig, ConverterConfig, MetadataConfig
from bdlib.plugins.metadata import MetadataPlugin
from bdlib.log import get_logger
from bdlib.models import ComicMetadata

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
    series_name: Optional[str],
    number: str,
    metadata_config: MetadataConfig,
    series_cache: Dict[str, Any],
) -> Optional[ComicMetadata]:
    """
    Get metadata from Comic Vine.
    """
    comicvine_client = metadata_config.client
    if not comicvine_client:
        return None

    if series_name and series_name in series_cache:
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
    else:
        logger.info("Series not cached, searching Comic Vine...")
        if not series_name:
            return None

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

            series_cache[series_name] = {
                "id": volume_id,
                "name": series_info["name"],
                "issues": issues,
            }

            issue = find_issue_by_number(issues, number) if number is not None else None
            if issue:
                logger.info(f"Found issue #{number}: {issue.get('name', 'N/A')}")
                issue_data = comicvine_client.get_issue(issue["id"])
                return map_to_comicinfo(issue_data, volume_data)
            else:
                logger.warning(f"Issue #{number} not found in series")
                return None
    return None


def find_folders(input_path: Path, single: bool) -> List[Path]:
    """Find folders to process."""
    if single:
        return [input_path]
    elif input_path.is_dir() and not any(input_path.glob("*.jpg")):
        return sorted([d for d in input_path.iterdir() if d.is_dir()])
    else:
        return [input_path.parent]


def process_folder(
    folder: Path,
    processing_config: ProcessingConfig,
    converter_config: ConverterConfig,
    metadata_config: MetadataConfig,
    series_cache: Optional[dict] = None,
):
    """Process a single folder of JPEG images to create a JXL-based CBZ archive."""
    logger.info(f"Processing: {folder.name}")

    jpeg_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
    jpeg_files += list(folder.glob("*.JPG")) + list(folder.glob("*.JPEG"))

    if not jpeg_files:
        logger.warning("No JPEG files found, skipping...")
        return False

    folder_metadata = extract_folder_metadata(folder)

    cv_metadata = None
    if metadata_config.client and series_cache is not None:
        cv_metadata = get_comicvine_metadata(
            folder_metadata.series, str(folder_metadata.number), metadata_config, series_cache
        )

    metadata = folder_metadata
    if cv_metadata:
        metadata = metadata.merge(cv_metadata)

    # Determine input folder for JXL conversion
    # If dejpeg is enabled, process JPEGs first, then convert to JXL
    # Otherwise, convert JPEGs directly to JXL
    input_for_jxl = folder
    temp_dejpeg_folder = None

    if converter_config.dejpeg:
        # Create temp folder for dejpeg output
        temp_dejpeg_folder = folder.parent / f"{folder.name}_dejpeg"
        logger.info(f"Removing JPEG artifacts from {len(jpeg_files)} files using FBCNN...")
        try:
            dejpeg.batch_convert(
                folder,
                temp_dejpeg_folder,
                max_threads=converter_config.threads,
            )
            input_for_jxl = temp_dejpeg_folder
            logger.info("JPEG artifact removal completed")
        except Exception as e:
            logger.error(f"DeJPEG processing failed: {e}")
            # Clean up temp folder on failure
            if temp_dejpeg_folder and temp_dejpeg_folder.exists():
                shutil.rmtree(temp_dejpeg_folder)
            return False

    jxl_folder = folder.parent / f"{folder.name}_jxl"

    logger.info(f"Converting {len(jpeg_files)} images to JXL...")
    try:
        jpeg_to_jxl.batch_convert(
            input_for_jxl,
            jxl_folder,
            converter_config.quality,
            converter_config.lossless,
            converter_config.threads,
        )
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        # Clean up temp dejpeg folder if it exists
        if temp_dejpeg_folder and temp_dejpeg_folder.exists():
            shutil.rmtree(temp_dejpeg_folder)
        return False

    logger.info("Generating ComicInfo.xml...")

    page_files = list(jxl_folder.glob("*.jpg")) + list(jxl_folder.glob("*.jpeg"))
    page_files += list(jxl_folder.glob("*.JPG")) + list(jxl_folder.glob("*.JPEG"))
    page_files += list(jxl_folder.glob("*.jxl")) + list(jxl_folder.glob("*.JXL"))
    page_files.sort()

    try:
        xml = generate_comicinfo(metadata, page_files=page_files if page_files else None)
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

    # Clean up temp dejpeg folder if it exists
    if converter_config.dejpeg and temp_dejpeg_folder and temp_dejpeg_folder.exists():
        logger.info("Cleaning up temporary DeJPEG folder...")
        shutil.rmtree(temp_dejpeg_folder)

    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Batch process comic folders")

    plugins = discover_plugins()
    for plugin in plugins:
        plugin.register_arguments(parser)

    args = parser.parse_args()

    config: Dict[str, Any] = {}
    for plugin in plugins:
        config.update(plugin.handle_arguments(args))

    processing_config: ProcessingConfig = config["processing"]
    converter_config: ConverterConfig = config["converter"]
    metadata_config: MetadataConfig = config["metadata"]

    series_cache = {}
    if metadata_config.enabled_sources:
        for plugin in plugins:
            if isinstance(plugin, MetadataPlugin):
                client = plugin.create_client(metadata_config)
                if client:
                    metadata_config.client = client
                    break

        if metadata_config.client:
            cached_series = get_cached_series()
            for name, info in cached_series.items():
                if "skip" not in info:
                    series_cache[name] = info
            logger.info(f"Loaded {len(series_cache)} cached series")

    folders = find_folders(Path(processing_config.input), processing_config.single)
    logger.info(f"Found {len(folders)} folder(s) to process")

    success = 0
    for folder in folders:
        if process_folder(
            folder,
            processing_config,
            converter_config,
            metadata_config,
            series_cache,
        ):
            success += 1

    if metadata_config.enabled_sources and series_cache:
        for name, info in series_cache.items():
            if "skip" not in info:
                cache_series_info(name, info)
        logger.info(f"Saved {len(series_cache)} series to cache")

    logger.info(f"Completed: {success}/{len(folders)} folders processed")


if __name__ == "__main__":
    main()
