#!/usr/bin/env python3
"""
JPEG to JPEG XL (JXL) image conversion.
"""

import concurrent.futures
from pathlib import Path

import numpy as np
import pylibjxl
from PIL import Image

from bdlib.log import get_logger

logger = get_logger(__name__)

IMAGE_EXTENSIONS = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG"]


def quality_to_distance(quality: int) -> float:
    """Convert JPEG quality (1-100) to JXL distance (0-15)."""
    if quality >= 100:
        return 0.0
    return max(0.1, (100 - quality) / 100 * 15)


def convert_jpeg_to_jxl(input_path: Path, output_path: Path, quality: int = 90, lossless: bool = True) -> bool:
    """
    Converts a single image (JPEG or PNG) to JXL format.
    Args:
        input_path (Path): The path to the input image (JPEG or PNG).
        output_path (Path): The path to the output JXL image.
        quality (int): The JXL encoding quality (1-100). Defaults to 90. Used in lossy mode.
        lossless (bool): Whether to use lossless JXL encoding. Defaults to True.
    """
    try:
        input_suffix = input_path.suffix.lower()
        if lossless:
            if input_suffix in (".jpg", ".jpeg"):
                pylibjxl.convert_jpeg_to_jxl(str(input_path), str(output_path))
            else:
                with Image.open(input_path) as _img:
                    img = _img.convert("RGB") if _img.mode != "RGB" else _img
                    arr = np.array(img)
                jxl_data = pylibjxl.encode(arr, effort=7, distance=0.0, lossless=True)
                with open(output_path, "wb") as f:
                    f.write(jxl_data)
        else:
            distance = quality_to_distance(quality)
            with Image.open(input_path) as _img:
                img = _img.convert("RGB") if _img.mode != "RGB" else _img
                arr = np.array(img)
            jxl_data = pylibjxl.encode(arr, effort=7, distance=distance, lossless=False)
            with open(output_path, "wb") as f:
                f.write(jxl_data)
        return True
    except Exception as e:
        logger.error(f"Error converting {input_path}: {e}")
        return False


def process_file(jpeg_file: Path, output_dir: Path, quality: int, lossless: bool) -> None:
    output_file = output_dir / (jpeg_file.stem + ".jxl")
    if convert_jpeg_to_jxl(jpeg_file, output_file, quality, lossless):
        logger.info(f"Converted {jpeg_file.name} -> {output_file.name} ... OK")
    else:
        logger.error(f"Converted {jpeg_file.name} -> {output_file.name} ... FAILED")


def batch_convert(
    input_dir: Path, output_dir: Path, quality: int = 90, lossless: bool = True, max_threads: int = 4
) -> None:
    """
    Converts all JPEG images in a directory to JXL format using multiple threads.
    Args:
        input_dir (Path): The path to the input directory.
        output_dir (Path): The path to the output directory.
        quality (int): The JXL encoding quality (1-100). Defaults to 90.
        lossless (bool): Whether to use lossless JXL encoding. Defaults to True.
        max_threads (int): The maximum number of threads to use. Defaults to 4.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jpeg_files = [file for ext in IMAGE_EXTENSIONS for file in input_dir.glob(ext)]

    if not jpeg_files:
        logger.warning(f"No JPEG files found in {input_dir}")
        return

    logger.info(f"Converting {len(jpeg_files)} files with up to {max_threads} threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_file, jpeg_file, output_dir, quality, lossless) for jpeg_file in jpeg_files]
        concurrent.futures.wait(futures)
    logger.info("Done.")
