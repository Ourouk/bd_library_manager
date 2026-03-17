# BD Library Manager

A Python library and CLI tool for automating comic archive preparation.

## What this project does

Process folders of comic pages (JPEG) into clean comic archives:

- Converts JPEG pages to JPEG XL (`.jxl`)
- Generates `ComicInfo.xml` metadata
- Optionally enriches metadata from Comic Vine API
- Builds `.cbz` archives ready for comic readers
- Supports batch processing for multiple folders

## Installation

```bash
# Clone and install in editable mode
pip install -e .

# Or install dependencies only
pip install requests Pillow jxlpy pylibjxl numpy
```

## Requirements

- Python 3.10+
- `cjxl` (from libjxl) in PATH for some operations
- Python packages: `requests`, `Pillow`, `jxlpy`, `pylibjxl`, `numpy`

## Usage

### CLI

```bash
# Full batch workflow
bdlib /path/to/library_root

# With Comic Vine enrichment
bdlib /path/to/comics --comicvine

# Process single folder
bdlib /path/to/folder --single

# Custom quality and threads
bdlib /path/to/comics -q 85 -t 8
```

### Python API

```python
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.config import set_api_key

# Convert images
jpeg_to_jxl.batch_convert("input/", "output/", quality=90)

# Generate metadata
xml = generate_comicinfo(title="Issue #1", series="My Series", number=1)

# Create CBZ
cbz.create_cbz("images/", "output.cbz")
```

## Project Structure

```
bdlib/
├── cli.py                 # Command-line interface
├── config.py              # Configuration management
├── metadata.py            # ComicMetadata dataclass
├── converters/
│   ├── jpeg_to_jxl.py    # JPEG → JXL conversion
│   └── cbz.py            # CBZ archive creation
└── metadata/
    ├── comicinfo.py       # ComicInfo.xml generation
    └── comicvine/
        └── client.py      # Comic Vine API client
```

## Configuration

On first use of Comic Vine features, the CLI prompts for an API key (free from https://comicvine.gamespot.com/api/).

Config and cache are stored in `~/.bd_library_manager/`.

## Folder Naming Convention

For batch processing, use: `Series Name/01 - Issue Title`

Example:
```
Batman/
├── 01 - The Killing Joke/
│   ├── page01.jpg
│   └── page02.jpg
└── 02 - A Death in the Family/
    └── ...
```
