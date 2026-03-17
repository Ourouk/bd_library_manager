#!/usr/bin/env python3
"""
ComicInfo.xml generation.
"""

from pathlib import Path
from typing import Optional, List
from jxlpy import JXLImagePlugin
from PIL import Image

from bdlib.models import ComicMetadata
from bdlib.log import get_logger

logger = get_logger(__name__)


def get_image_info(image_path: Path) -> dict:
    """
    Gets the width, height, and size of an image file.

    Args:
        image_path (Path): The path to the image file.

    Returns:
        dict: A dictionary containing the image's width, height, and size.
    """
    info = {"width": 0, "height": 0, "size": image_path.stat().st_size}

    try:
        with Image.open(image_path) as img:
            info["width"] = img.width
            info["height"] = img.height
    except Exception as e:
        logger.error(f"Error getting image info for {image_path}: {e}")

    return info


def generate_pages_xml(page_files: list) -> str:
    """
    Generates the <Pages> section of the ComicInfo.xml file.

    Args:
        page_files (list): A list of paths to the page image files.

    Returns:
        str: The XML string for the <Pages> section.
    """
    if not page_files:
        return ""

    pages_xml = "  <Pages>\n"
    for idx, page_file in enumerate(page_files):
        info = get_image_info(page_file)

        is_double = info["height"] > 0 and (info["width"] / info["height"]) > 1.3
        page_type = "FrontCover" if idx == 0 else "DoublePage" if is_double else ""
        type_attr = f' Type="{page_type}"' if page_type else ""
        double_attr = ' DoublePage="True"' if is_double else ' DoublePage="False"'

        pages_xml += (
            f'    <Page{double_attr} Image="{idx}" '
            f'ImageHeight="{info["height"]}" ImageSize="{info["size"]}" '
            f'ImageWidth="{info["width"]}"{type_attr} />\n'
        )
    pages_xml += "  </Pages>\n"
    return pages_xml


def generate_comicinfo(
    metadata: ComicMetadata,
    page_files: Optional[List[Path]] = None,
) -> str:
    """
    Generates the full ComicInfo.xml content.

    Args:
        metadata (ComicMetadata): The metadata for the comic.
        page_files (Optional[List[Path]]): A list of paths to the page image files.

    Returns:
        str: The complete XML content as a string.
    """
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml += '<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'

    def add_field(name, value):
        nonlocal xml
        if value is not None:
            # Convert field name to correct case for XML
            xml_name = "".join(word.capitalize() for word in name.split("_"))
            xml += f"  <{xml_name}>{value}</{xml_name}>\n"

    # Add all fields from metadata
    for field, value in metadata.to_dict().items():
        add_field(field, value)

    if page_files:
        xml += generate_pages_xml(page_files)

    xml += "</ComicInfo>"
    return xml
