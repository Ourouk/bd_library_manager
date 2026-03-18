# BD Library Manager - Developer Guide

## Installation

```bash
# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# Install with dependencies
uv pip install -e .

# Optional: CBR (RAR) support
uv pip install -e ".[cbr]"
apt install unrar  # or brew install unrar on macOS
```

## Quick Start

```python
from pathlib import Path
from bdlib.dto import ComicMetadata
from bdlib import generate_comicinfo
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.converters.archive import extract_archive, is_archive

# Process folder
jpeg_to_jxl.batch_convert("input_folder/", "output_folder/", quality=90)

# Or process archive (CBZ/CBR/CB7)
if is_archive(Path("comic.cbz")):
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = extract_archive(Path("comic.cbz"), Path(tmpdir) / "extracted")
        # ... process extracted files

# Generate ComicInfo.xml
xml = generate_comicinfo(
    title="The Killing Joke",
    series="Batman",
    number=1,
    writer="Alan Moore",
    artist="Brian Bolland",
)
with open("output/ComicInfo.xml", "w") as f:
    f.write(xml)

# Create CBZ archive
cbz.create_cbz("output/", "comic.cbz")
```

## CLI Usage

```bash
# Full batch workflow (processes folders AND archives)
bdlib ./comics

# Single folder processing
bdlib ./comics/Batman/01 --single

# Single archive processing
bdlib ./comics/Batman/01.cbz --single
bdlib ./comics/Batman/01.cbr --single
bdlib ./comics/Batman/01.cb7 --single

# With JPEG artifact removal (DeJPEG with CUDA)
bdlib ./comics --dejpeg -t 1

# With DeJPEG on CPU only
bdlib ./comics --dejpeg

# With Comic Vine enrichment
bdlib ./comics --comicvine

# Custom options
bdlib ./comics -q 85 -t 8 --lossless -o ./output
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `input` | Input folder, archive, or directory | Required |
| `-q, --quality` | JXL quality 1-100 | 90 |
| `-l, --lossless` | Use lossless compression | False |
| `-k, --keep-jxl` | Keep intermediate JXL files | False |
| `--single` | Process single folder/archive | False |
| `-o, --output-folder` | Output directory | Same as input |
| `-t, --threads` | Thread count for DeJPEG | 1 |
| `--dejpeg` | Enable JPEG artifact removal | False |
| `--dejpeg-model` | DeJPEG model to use | fbcnn_color |
| `-jt, --jxl-threads` | JXL encoding threads | 4 |
| `--comicvine` | Enrich metadata via API | False |
| `--country` | Country code (FR, US, etc.) | None |
| `--language` | Language code (en, fr, etc.) | None |

## DeJPEG (JPEG Artifact Removal)

The library supports two AI models for JPEG artifact removal:

- **FBCNN**: Fast JPEG artifact removal model
- **waifu2x**: Multiple architectures (cunet, swin_unet) optimized for anime/art or photographic content

### Requirements

- **CPU**: Works out of the box with `onnxruntime-gpu`
- **GPU (Recommended)**: NVIDIA GPU with CUDA 13.x + cuDNN 9.x

### Available Models

| Model | Type | Description |
|-------|------|-------------|
| `fbcnn_color` | JPEG artifacts | Fast quality factor prediction |
| `waifu2x_cunet_art` | Art/Anime | Classic CuNet architecture |
| `waifu2x_cunet_photo` | Photographic | Classic CuNet architecture |
| `waifu2x_swin_unet_art` | Art/Anime | Modern SwinUNet architecture |
| `waifu2x_swin_unet_photo` | Photographic | Modern SwinUNet architecture |
| `waifu2x_swin_unet_art_scan` | Scanned Art | Optimized for scanned art |

Each waifu2x model supports:
- Noise levels 0-3: `waifu2x_swin_unet_art:noise2`
- 2x upscaling: `waifu2x_swin_unet_art:noise0:scale2x`

### Performance

| Mode | Speed (1920x2492) | Notes |
|------|-------------------|-------|
| CPU (20 threads) | ~65s/image | Default fallback |
| CUDA (1 thread) | ~2s/image | **32x faster** |

**Note:** Use `-jt 1` with CUDA to avoid GPU memory exhaustion.

### Tiled Processing

waifu2x models use tiled processing with seam blending to handle large images:
- Images are split into overlapping tiles
- Each tile is processed independently
- Edges are blended using a weighted average to eliminate seams
- Edge replication padding is used to prevent border artifacts

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

# Use waifu2x model with tiled processing
dejpeg.batch_convert(
    input_dir=Path("input/"),
    output_dir=Path("output/"),
    model_string="waifu2x_swin_unet_art:noise0",
)
```

### How It Works

- **FBCNN**: Predicts JPEG quality factor and removes artifacts while preserving details
- **waifu2x**: Neural network upscaling with tiled processing for artifact-free results

### Creating Models

```python
from bdlib.converters.dejpeg import create_model, DejpegConfig

# FBCNN model
model, config = create_model("fbcnn_color")

# waifu2x model with specific noise level
model, config = create_model("waifu2x_swin_unet_art:noise2")

# waifu2x with 2x upscaling
model, config = create_model("waifu2x_cunet_photo:noise0:scale2x")
```

## API Reference

### Models

#### `ComicMetadata`

Dataclass for comic metadata.

```python
from bdlib.dto import ComicMetadata

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

#### `bdlib.converters.archive`

```python
from bdlib.converters.archive import (
    extract_archive,
    is_archive,
    get_extractor,
    SUPPORTED_EXTENSIONS,
)

# Check if a file is a supported archive
if is_archive(Path("comic.cbz")):
    print("Is archive")

# Get the appropriate extractor for an archive
extractor = get_extractor(Path("comic.cbz"))
# extractor.extract(archive_path, output_dir)

# Supported extensions
print(SUPPORTED_EXTENSIONS)
# ['.cbz', '.CBZ', '.cbr', '.CBR', '.cb7', '.CB7']

# Extract archive to directory
extract_archive(
    archive_path=Path("comic.cbz"),
    output_dir=Path("./extracted/"),
)
```

**Supported formats:**
- **CBZ**: ZIP archive (uses stdlib `zipfile`)
- **CBR**: RAR archive (requires `rarfile` + `unrar`)
- **CB7**: 7z archive (uses `py7zr`)

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
from bdlib.dto import ComicMetadata

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

#### `bdlib.metadata.path`

```python
from bdlib.metadata import extract_folder_metadata
from pathlib import Path

# Extract from folder
meta = extract_folder_metadata(Path("comics/Batman/01 - Knightfall"))

# Extract from archive (after extraction)
meta = extract_folder_metadata(
    extracted_folder=Path("/tmp/extracted/"),
    archive_path=Path("comics/Batman/01 - Knightfall.cbz"),
)
# Series will be "Batman" (from archive's parent)
# Number and title parsed from archive stem

# Custom regex patterns
meta = extract_folder_metadata(
    Path("folder"),
    patterns=(
        r"(\d+)\s*#\s*(.+)",  # with title pattern
        r"#(\d+)",            # number only pattern
        r"T(\d+)",            # volume/tome pattern
    )
)
```

#### `bdlib.metadata.comicvine`

```python
from bdlib.metadata.comicvine import (
    ComicVineClient,
    map_to_comicinfo,
    find_issue_by_number,
)
from bdlib.dto import ComicMetadata

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

For batch processing, expected structure (folders and archives mixed):

```
comics/
├── Series Name/
│   ├── 01 - Issue Title/
│   │   ├── 01.jpg
│   │   └── 02.jpg
│   ├── 02 - Another Title.cbz
│   ├── 03.cbz
│   └── 04 - Knightfall.cbz
```

### Supported Patterns

| Pattern | Number | Title |
|---------|--------|-------|
| `01 - Issue Title` | 1 | "Issue Title" |
| `01` | 1 | None |
| `Vol. 01` | 1 | None |
| `Tome 01` | 1 | None |
| `Volume 01` | 1 | None |

The CLI extracts:
- **Series**: Parent folder name
- **Number**: Parsed from folder/archive name
- **Title**: Parsed from folder/archive name (if present)

### Customizing Patterns

```python
from bdlib.metadata import path

# Override module-level patterns
path.PATTERN_WITH_TITLE = r"(\d+)\s*#\s*(.+)"
path.PATTERN_NUMBER_ONLY = r"#(\d+)"

# Or pass custom patterns to the function
from bdlib.metadata import extract_folder_metadata
meta = extract_folder_metadata(
    folder,
    patterns=(r"(\d+)#(.+)", r"#(\d+)", r"T(\d+)")
)
```

## Error Handling

```python
from pathlib import Path
from bdlib.converters import cbz

try:
    cbz.create_cbz(Path("images/"), Path("output.cbz"))
except Exception as e:
    print(f"Failed to create CBZ: {e}")
```
