#!/usr/bin/env python3
"""
CBZ archive creation.
"""

import zipfile
from pathlib import Path
from typing import Optional

from bdlib.log import get_logger

logger = get_logger(__name__)

IMAGE_EXTENSIONS = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.jxl", "*.JXL"]


def create_cbz(input_dir: Path, output_path: Optional[Path] = None, comic_info: Optional[Path] = None):
    """
    Creates a CBZ archive from a directory of images.

    Args:
        input_dir (Path): The directory containing the images.
        output_path (Path, optional): The path for the output CBZ file.
                                      Defaults to the input directory name with a .cbz extension.
        comic_info (Path, optional): The path to a ComicInfo.xml file to include.
                                      Defaults to 'ComicInfo.xml' in the input directory.

    Returns:
        bool: True if the CBZ file was created successfully, False otherwise.
    """
    input_dir = Path(input_dir)

    if output_path is None:
        output_path = input_dir.with_suffix(".cbz")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_files = [file for ext in IMAGE_EXTENSIONS for file in input_dir.glob(ext)]
    image_files.sort()

    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        return False

    logger.info(f"Creating {output_path} with {len(image_files)} images...")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as cbz:
        for idx, img in enumerate(image_files):
            arcname = f"{idx + 1:03d}{img.suffix}"
            cbz.write(img, arcname)
            logger.debug(f"Added: {arcname}")

        if comic_info and comic_info.exists():
            cbz.write(comic_info, "ComicInfo.xml")
            logger.info("Added: ComicInfo.xml")

    logger.info(f"Done: {output_path}")
    return True
