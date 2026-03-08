#!/usr/bin/env python3
"""
This script generates a ComicInfo.xml file for a comic book archive.
It creates the XML file based on metadata provided via command-line arguments.
No default values are used; only extracted or provided information is added.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
from jxlpy import JXLImagePlugin
from PIL import Image


def get_image_info(image_path: Path) -> dict:
    """
    Gets the width, height, and size of an image file.

    Args:
        image_path (Path): The path to the image file.

    Returns:
        dict: A dictionary containing the image's width, height, and size.
    """
    info = {
        'width': 0,
        'height': 0,
        'size': image_path.stat().st_size
    }
    
    try:
        with Image.open(image_path) as img:
            info['width'] = img.width
            info['height'] = img.height
    except Exception:
        pass  # Ignore errors for unsupported image types
    
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
        
        # Heuristic to detect double-page spreads
        is_double = info['height'] > 0 and (info['width'] / info['height']) > 1.3
        page_type = 'FrontCover' if idx == 0 else 'DoublePage' if is_double else ''
        type_attr = f' Type="{page_type}"' if page_type else ''
        double_attr = ' DoublePage="True"' if is_double else ' DoublePage="False"'
        
        pages_xml += (
            f'    <Page{double_attr} Image="{idx}" '
            f'ImageHeight="{info["height"]}" ImageSize="{info["size"]}" '
            f'ImageWidth="{info["width"]}"{type_attr} />\n'
        )
    pages_xml += "  </Pages>\n"
    return pages_xml


def generate_comicinfo(
    title: Optional[str] = None,
    series: Optional[str] = None,
    number: Optional[int] = None,
    writer: Optional[str] = None,
    artist: Optional[str] = None,
    colorist: Optional[str] = None,
    inker: Optional[str] = None,
    letterer: Optional[str] = None,
    cover_artist: Optional[str] = None,
    editor: Optional[str] = None,
    publisher: Optional[str] = None,
    genre: Optional[str] = None,
    summary: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    web: Optional[str] = None,
    isbn: Optional[str] = None,
    notes: Optional[str] = None,
    language: Optional[str] = None,
    country: Optional[str] = None,
    rating: Optional[int] = None,
    pages: Optional[int] = None,
    page_files: Optional[list] = None,
) -> str:
    """
    Generates the full ComicInfo.xml content.

    Args:
        All arguments correspond to standard ComicInfo.xml fields.

    Returns:
        str: The complete XML content as a string.
    """
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml += '<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">\n'

    def add_field(name, value):
        nonlocal xml
        if value is not None:
            xml += f'  <{name}>{value}</{name}>\n'

    # Add all the provided metadata fields to the XML
    add_field('Title', title)
    add_field('Series', series)
    add_field('Number', number)
    add_field('Writer', writer)
    add_field('Penciller', artist)
    add_field('Inker', inker)
    add_field('Colorist', colorist)
    add_field('Letterer', letterer)
    add_field('CoverArtist', cover_artist)
    add_field('Editor', editor)
    add_field('Publisher', publisher)
    add_field('Genre', genre)
    add_field('Summary', summary)
    add_field('Year', year)
    add_field('Month', month)
    add_field('Day', day)
    add_field('Web', web)
    add_field('ISBN', isbn)
    add_field('Notes', notes)
    add_field('LanguageISO', language)
    add_field('Country', country)
    add_field('Rating', rating)
    add_field('Pages', pages)

    if page_files:
        xml += generate_pages_xml(page_files)

    xml += '</ComicInfo>'
    return xml


def main():
    """
    Main function to parse command-line arguments and generate the ComicInfo.xml file.
    """
    parser = argparse.ArgumentParser(description='Generate ComicInfo.xml for comics')
    parser.add_argument('output', help='Output directory for the ComicInfo.xml file')

    # Arguments for manual metadata entry
    parser.add_argument('--title', help='Comic title', default=None)
    parser.add_argument('--series', help='Series name', default=None)
    parser.add_argument('--number', type=int, help='Tome/issue number', default=None)
    parser.add_argument('--writer', help='Writer', default=None)
    parser.add_argument('--artist', help='Artist/Penciller', default=None)
    parser.add_argument('--colorist', help='Colorist', default=None)
    parser.add_argument('--inker', help='Inker', default=None)
    parser.add_argument('--letterer', help='Letterer', default=None)
    parser.add_argument('--cover-artist', help='Cover artist', default=None)
    parser.add_argument('--editor', help='Editor', default=None)
    parser.add_argument('--publisher', help='Publisher', default=None)
    parser.add_argument('--genre', help='Genre', default=None)
    parser.add_argument('--summary', help='Summary/Description', default=None)
    parser.add_argument('--year', type=int, help='Year', default=None)
    parser.add_argument('--month', type=int, help='Month', default=None)
    parser.add_argument('--day', type=int, help='Day', default=None)
    parser.add_argument('--web', help='Website', default=None)
    parser.add_argument('--isbn', help='ISBN', default=None)
    parser.add_argument('--notes', help='Notes', default=None)
    parser.add_argument('--language', help='Language (e.g., en)', default=None)
    parser.add_argument('--country', help='Country', default=None)
    parser.add_argument('--rating', type=int, help='Rating (0-10)', default=None)
    parser.add_argument('--pages', type=int, help='Number of pages', default=None)
    parser.add_argument('--images', help='Directory containing images to include in the <Pages> section', default=None)

    args = parser.parse_args()

    output_path = Path(args.output)
    image_path = Path(args.images) if args.images else None
    
    page_files = []
    if image_path:
        page_files = list(image_path.glob('*.jpg')) + list(image_path.glob('*.jpeg'))
        page_files += list(image_path.glob('*.JPG')) + list(image_path.glob('*.JPEG'))
        page_files += list(image_path.glob('*.jxl')) + list(image_path.glob('*.JXL'))
        page_files.sort()

    # Generate XML from manual arguments
    xml = generate_comicinfo(
        title=args.title,
        series=args.series,
        number=args.number,
        writer=args.writer,
        artist=args.artist,
        colorist=args.colorist,
        inker=args.inker,
        letterer=args.letterer,
        cover_artist=args.cover_artist,
        editor=args.editor,
        publisher=args.publisher,
        genre=args.genre,
        summary=args.summary,
        year=args.year,
        month=args.month,
        day=args.day,
        web=args.web,
        isbn=args.isbn,
        notes=args.notes,
        language=args.language,
        country=args.country,
        rating=args.rating,
        pages=args.pages if args.pages else len(page_files) if page_files else None,
        page_files=page_files if page_files else None
    )

    out_path = output_path / 'ComicInfo.xml'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xml, encoding='utf-8')
    print(f"Generated: {out_path}")


if __name__ == '__main__':
    main()
