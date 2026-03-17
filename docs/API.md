# BD Library Manager - Developer Guide

## Installation

```bash
# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# Install with dependencies
uv pip install -e .

# Or install just dependencies
uv pip install requests Pillow jxlpy pylibjxl numpy onnxruntime-gpu
```

## Quick Start

```python
from bdlib import ComicMetadata, generate_comicinfo
from bdlib.converters import jpeg_to_jxl, cbz

# 1. Convert images to JXL
jpeg_to_jxl.batch_convert("input_folder/", "output_folder/", quality=90)

# 2. Generate ComicInfo.xml
xml = generate_comicinfo(
    title="The Killing Joke",
    series="Batman",
    number=1,
    writer="Alan Moore",
    artist="Brian Bolland",
)
with open("output/ComicInfo.xml", "w") as f:
    f.write(xml)

# 3. Create CBZ archive
cbz.create_cbz("output/", "comic.cbz")
```

## CLI Usage

```bash
# Full batch workflow
bdlib ./comics

# With JPEG artifact removal (DeJPEG with CUDA)
bdlib ./comics --dejpeg -t 1

# With DeJPEG on CPU only
bdlib ./comics --dejpeg

# With Comic Vine enrichment
bdlib ./comics --comicvine

# Single folder processing
bdlib ./comics/Batman/01 --single

# Custom options
bdlib ./comics -q 85 -t 8 --lossless -o ./output
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `input` | Input folder or file | Required |
| `-q, --quality` | JXL quality 1-100 | 90 |
| `-l, --lossless` | Use lossless compression | False |
| `-k, --keep-jxl` | Keep intermediate JXL files | False |
| `--single` | Process single folder | False |
| `-o, --output-folder` | Output directory | Same as input |
| `-t, --threads` | Thread count for conversion | 4 |
| `--dejpeg` | Enable JPEG artifact removal | False |
| `--dejpeg-model` | DeJPEG model to use | fbcnn_color |
| `--comicvine` | Enrich metadata via API | False |
| `--country` | Country code (FR, US, etc.) | None |
| `--language` | Language code (en, fr, etc.) | None |

## DeJPEG (JPEG Artifact Removal)

The library uses [FBCNN](https://github.com/jiaxi-jiang/FBCNN) for AI-powered JPEG artifact removal.

### Requirements

- **CPU**: Works out of the box with `onnxruntime-gpu`
- **GPU (Recommended)**: NVIDIA GPU with CUDA 13.x + cuDNN 9.x

### Performance

| Mode | Speed (1920x2492) | Notes |
|------|-------------------|-------|
| CPU (20 threads) | ~65s/image | Default fallback |
| CUDA (1 thread) | ~2s/image | **32x faster** |

**Note:** Use `-t 1` with CUDA to avoid GPU memory exhaustion.

### Python API

```python
from bdlib.converters import dejpeg
from pathlib import Path

# Convert single image
dejpeg.convert_jpeg(
    input_path=Path("page.jpg"),
    output_path=Path("page_clean.png"),
)

# Batch convert with CUDA
dejpeg.batch_convert(
    input_dir=Path("input/"),
    output_dir=Path("output/"),
    max_threads=1,  # Use 1 thread with CUDA
)

# Or use directly with ONNX session
session = dejpeg._get_ort_session(model_path)
dejpeg.convert_jpeg(input_path, output_path, model_session=session)
```

### How It Works

FBCNN predicts the JPEG quality factor and removes artifacts while preserving details:
- Quality factor input (0-1): Lower = more aggressive artifact removal
- Default: 0.5 (moderate removal)
- Model auto-detects quality if no input provided

## API Reference

### Models

#### `ComicMetadata`

Dataclass for comic metadata.

```python
from bdlib import ComicMetadata

meta = ComicMetadata(
    title="Issue #1",
    series="My Series",
    number=1,
    writer="Writer Name",
    artist="Artist Name",
    publisher="Publisher",
    year=2024,
    month=1,
    summary="A brief summary...",
)

# Convert to dict (excludes None values)
data = meta.to_dict()
```

**Fields:**
- `title`, `series`, `number`, `count`, `volume`
- `alternate_series`, `alternate_number`, `alternate_count`
- `writer`, `artist`, `colorist`, `inker`, `letterer`, `cover_artist`, `editor`
- `publisher`, `imprint`, `genre`
- `summary`, `year`, `month`, `day`
- `web`, `isbn`, `notes`
- `language`, `country`, `rating`
- `format`, `black_and_white`, `manga`, `pages`

### Converters

#### `bdlib.converters.jpeg_to_jxl`

```python
from bdlib.converters import jpeg_to_jxl

# Convert single file
jpeg_to_jxl.convert_jpeg_to_jxl(
    input_path=Path("page.jpg"),
    output_path=Path("page.jxl"),
    quality=90,
    lossless=True,
)

# Batch convert
jpeg_to_jxl.batch_convert(
    input_dir=Path("input/"),
    output_dir=Path("output/"),
    quality=90,
    lossless=True,
    max_threads=4,
)

# Quality to JXL distance conversion
distance = jpeg_to_jxl.quality_to_distance(85)  # Returns ~2.25
```

#### `bdlib.converters.cbz`

```python
from bdlib.converters import cbz

# Create CBZ
cbz.create_cbz(
    input_dir=Path("images/"),
    output_path=Path("comic.cbz"),
    comic_info=Path("ComicInfo.xml"),  # Optional
)

# Output path is optional - defaults to input_dir.cbz
cbz.create_cbz(Path("images/"))  # Creates images.cbz
```

### Metadata

#### `bdlib.metadata.comicinfo`

```python
from bdlib.metadata.comicinfo import generate_comicinfo, get_image_info
from bdlib import ComicMetadata

# Generate XML from parameters
xml = generate_comicinfo(
    title="Title",
    series="Series",
    number=1,
    writer="Writer",
    artist="Artist",
    year=2024,
    month=6,
    country="FR",
    language="fr",
)

# Generate from ComicMetadata object
meta = ComicMetadata(title="X", series="Y", number=1)
xml = generate_comicinfo(metadata=meta)

# Explicit parameters override metadata object
xml = generate_comicinfo(
    title="Override Title",
    metadata=meta,  # This title won't be used
)

# Get image dimensions
info = get_image_info(Path("page.jpg"))
# Returns: {'width': 1920, 'height': 2880, 'size': 123456}
```

#### `bdlib.metadata.comicvine`

```python
from bdlib.metadata.comicvine import (
    ComicVineClient,
    map_to_comicinfo,
    find_issue_by_number,
)
from bdlib import ComicMetadata

# Initialize client
client = ComicVineClient(api_key="your-api-key")

# Search for series
results = client.search_series("Batman", limit=10)
# Returns: [{'id': 123, 'name': 'Batman', 'publisher': 'DC Comics', ...}]

# Get volume details
volume = client.get_volume(123)

# Get all issues in a volume
issues = client.get_volume_issues(123)
# Returns: [{'id': 456, 'issue_number': '1', 'name': '...'}, ...]

# Get detailed issue info
issue = client.get_issue(456)

# Map Comic Vine data to ComicMetadata
metadata = map_to_comicinfo(issue, volume)

# Find specific issue by number
issue = find_issue_by_number(issues, "1")
```

### Configuration

#### `bdlib.config`

```python
from bdlib import config

# Get/Set API key
key = config.get_api_key()
config.set_api_key("new-key")

# Series caching
cached = config.get_cached_series()
config.cache_series_info("Series Name", {"id": 123, "issues": []})
info = config.get_cached_series_info("Series Name")

# Low-level config access
cfg = config.load_config()
config.save_config({"comicvine_api_key": "key", "cached_series": {}})
```

Config is stored in `~/.bd_library_manager/config.json`.

## Folder Structure

For batch processing, expected structure:

```
comics/
├── Series Name/
│   ├── 01 - Issue Title/
│   │   ├── 01.jpg
│   │   └── 02.jpg
│   └── 02 - Another Title/
│       └── ...
```

The CLI extracts:
- **Series**: Parent folder name (`Series Name`)
- **Number**: First number in folder name (`01`)
- **Title**: Text after dash (`Issue Title`)

## Error Handling

```python
from pathlib import Path
from bdlib.converters import cbz

try:
    cbz.create_cbz(Path("images/"), Path("output.cbz"))
except Exception as e:
    print(f"Failed to create CBZ: {e}")
```
