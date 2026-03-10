#!/usr/bin/env python3
"""
This script converts JPEG images to the JPEG XL (JXL) format.
It can be used to convert a single file or a batch of files from a directory.
The script uses the 'pylibjxl' library.
"""

import argparse
import concurrent.futures
from pathlib import Path
import sys

import numpy as np
import pylibjxl
from PIL import Image


def quality_to_distance(quality: int) -> float:
    """Convert JPEG quality (1-100) to JXL distance (0-15)."""
    if quality >= 100:
        return 0.0
    return max(0.1, (100 - quality) / 100 * 15)


def convert_jpeg_to_jxl(input_path: Path, output_path: Path, quality: int = 90, lossless: bool = True):
    """
    Converts a single JPEG image to JXL format.
    Args:
        input_path (Path): The path to the input JPEG image.
        output_path (Path): The path to the output JXL image.
        quality (int): The JXL encoding quality (1-100). Defaults to 90. Used in lossy mode.
        lossless (bool): Whether to use lossless JXL encoding. Defaults to True.
    """
    try:
        if lossless:
            pylibjxl.convert_jpeg_to_jxl(str(input_path), str(output_path))
        else:
            distance = quality_to_distance(quality)
            with Image.open(input_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                arr = np.array(img)
            jxl_data = pylibjxl.encode(arr, effort=7, distance=distance, lossless=False)
            with open(output_path, 'wb') as f:
                f.write(jxl_data)
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}", file=sys.stderr)
        return False


def process_file(jpeg_file, output_dir, quality, lossless):
    output_file = output_dir / (jpeg_file.stem + '.jxl')
    if convert_jpeg_to_jxl(jpeg_file, output_file, quality, lossless):
        print(f"  Converted {jpeg_file.name} -> {output_file.name} ... OK")
    else:
        print(f"  Converted {jpeg_file.name} -> {output_file.name} ... FAILED")


def batch_convert(input_dir: Path, output_dir: Path, quality: int = 90, lossless: bool = True, max_threads: int = 4):
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
    jpeg_files = list(input_dir.glob('*.jpg')) + list(input_dir.glob('*.jpeg'))
    jpeg_files += list(input_dir.glob('*.JPG')) + list(input_dir.glob('*.JPEG'))
    if not jpeg_files:
        print(f"No JPEG files found in {input_dir}")
        return
    print(f"Converting {len(jpeg_files)} files with up to {max_threads} threads...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_file, jpeg_file, output_dir, quality, lossless) for jpeg_file in jpeg_files]
        concurrent.futures.wait(futures)
    print("Done.")


def main():
    """
    Main function to parse command-line arguments and start the conversion.
    """
    parser = argparse.ArgumentParser(description='Batch convert JPEG to JXL')
    parser.add_argument('input_dir', help='Input directory containing JPEG files')
    parser.add_argument('output_dir', help='Output directory for JXL files')
    parser.add_argument('-q', '--quality', type=int, default=90, help='JXL quality (1-100, default: 90) for lossy mode')
    parser.add_argument('--lossy', action='store_true', help='Use lossy mode (default is lossless)')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Number of threads to use')
    args = parser.parse_args()
    batch_convert(args.input_dir, args.output_dir, args.quality, not args.lossy, args.threads)


if __name__ == '__main__':
    main()
