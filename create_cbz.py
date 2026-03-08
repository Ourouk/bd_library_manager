#!/usr/bin/env python3
"""
This script creates a Comic Book Archive (CBZ) file from a directory of images.
It sorts the images, adds them to a ZIP archive with a .cbz extension,
and can optionally include a ComicInfo.xml metadata file.
"""

import argparse
import zipfile
from pathlib import Path
from typing import Optional


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
    
    # Set the output path if not provided
    if output_path is None:
        output_path = input_dir.with_suffix('.cbz')
    else:
        output_path = Path(output_path)
    
    # Create parent directory for output if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Find all supported image files in the input directory
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG', '*.jxl', '*.JXL']:
        image_files.extend(input_dir.glob(ext))
    image_files.sort()
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return False
    
    print(f"Creating {output_path} with {len(image_files)} images...")
    
    # Create the ZIP archive (CBZ)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
        # Add each image to the archive, renaming it to a numbered format
        for idx, img in enumerate(image_files):
            arcname = f"{idx + 1:03d}{img.suffix}"
            cbz.write(img, arcname)
            print(f"  Added: {arcname}")
        
        # Add the ComicInfo.xml file if it exists
        if comic_info and comic_info.exists():
            cbz.write(comic_info, 'ComicInfo.xml')
            print(f"  Added: ComicInfo.xml")
    
    print(f"Done: {output_path}")
    return True


def main():
    """
    Main function to parse command-line arguments and create the CBZ archive.
    """
    parser = argparse.ArgumentParser(description='Create CBZ comic archive from images')
    parser.add_argument('input', help='Input directory containing images')
    parser.add_argument('output', nargs='?', help='Output CBZ file (default: input.cbz)')
    parser.add_argument('-m', '--metadata', help='ComicInfo.xml file to include')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    metadata_path = Path(args.metadata) if args.metadata else input_path / 'ComicInfo.xml'
    
    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        return
    
    create_cbz(input_path, output_path, metadata_path)


if __name__ == '__main__':
    main()
