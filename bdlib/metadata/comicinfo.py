#!/usr/bin/env python3
"""
ComicInfo.xml generation.
"""

from typing import List, Optional

from bdlib.log import get_logger
from bdlib.models import ComicMetadata, PageInfo

logger = get_logger(__name__)


def generate_pages_xml(page_infos: List[PageInfo]) -> str:
    """
    Generates the <Pages> section of the ComicInfo.xml file.

    Args:
        page_infos: List of PageInfo with dimensions from conversion.

    Returns:
        str: The XML string for the <Pages> section.
    """
    if not page_infos:
        return ""

    pages_xml = "  <Pages>\n"
    for idx, page_info in enumerate(page_infos):
        is_double = page_info.height > 0 and (page_info.width / page_info.height) > 1.3
        page_type = "FrontCover" if idx == 0 else "DoublePage" if is_double else ""
        type_attr = f' Type="{page_type}"' if page_type else ""
        double_attr = ' DoublePage="True"' if is_double else ' DoublePage="False"'

        pages_xml += (
            f'    <Page{double_attr} Image="{idx}" '
            f'ImageHeight="{page_info.height}" ImageSize="{page_info.size}" '
            f'ImageWidth="{page_info.width}"{type_attr} />\n'
        )
    pages_xml += "  </Pages>\n"
    return pages_xml


def generate_comicinfo(
    metadata: ComicMetadata,
    page_infos: Optional[List[PageInfo]] = None,
    denoise_info: Optional[dict] = None,
) -> str:
    """
    Generates the full ComicInfo.xml content.

    Args:
        metadata: The metadata for the comic.
        page_infos: List of PageInfo with dimensions from conversion.
        denoise_info: Denoise processing info to include in metadata.

    Returns:
        str: The complete XML content as a string.
    """
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml += '<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'

    def add_field(name, value):
        nonlocal xml
        if value is not None:
            xml_name = "".join(word.capitalize() for word in name.split("_"))
            xml += f"  <{xml_name}>{value}</{xml_name}>\n"

    for field, value in metadata.to_dict().items():
        add_field(field, value)

    if denoise_info:
        if "model_name" in denoise_info:
            add_field("denoise_model", denoise_info["model_name"])
        if "noise_level" in denoise_info:
            add_field("denoise_noise_level", denoise_info["noise_level"])
        if "scale_factor" in denoise_info:
            add_field("denoise_scale_factor", denoise_info["scale_factor"])

    if page_infos:
        xml += generate_pages_xml(page_infos)

    xml += "</ComicInfo>"
    return xml
