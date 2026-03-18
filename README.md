# BD Library Manager

A Python library and CLI tool for automating comic archive preparation.

## What this project does

Process folders of comic pages (JPEG) or comic archives (CBZ/CBR/CB7) into clean JXL-based archives:

- **Input formats:** Folders with JPEG images, or CBZ/CBR/CB7 archives
- Converts JPEG pages to JPEG XL (`.jxl`)
- Removes JPEG artifacts using FBCNN or waifu2x (AI-powered, CUDA-accelerated)
- Supports tiled processing with seam blending for waifu2x models
- Generates `ComicInfo.xml` metadata
- Optionally enriches metadata from Comic Vine API
- Builds `.cbz` archives ready for comic readers
- Supports batch processing for multiple folders/archives

## Installation

```bash
# Clone and install in editable mode
pip install -e .

# Or install dependencies only
pip install requests Pillow jxlpy pylibjxl numpy onnxruntime-gpu py7zr

# Optional: CBR (RAR) support (requires unrar system package)
pip install -e ".[cbr]"
apt install unrar  # or brew install unrar on macOS
```

### Shell Script (Recommended)

A convenient shell script is provided for easy CLI usage:

```bash
# Make executable (already done in git)
chmod +x bdlib.sh

# Show help
./bdlib.sh help

# Show available models
./bdlib.sh info

# Process comics
./bdlib.sh --input ./comics
./bdlib.sh -i ./folder --dejpeg
./bdlib.sh -i ./folder --dejpeg --dejpeg-model waifu2x_swin_unet_art:noise0
```

### CUDA Support

For GPU acceleration (recommended for DeJPEG):
- Requires NVIDIA GPU with CUDA 13.x support
- Requires cuDNN 9.x
- Automatically uses CUDA when available, falls back to CPU

**Note:** ONNX Runtime may emit `ScatterND` warnings when using CUDA. These are harmless internal messages.

## Requirements

- Python 3.10+
- `cjxl` (from libjxl) in PATH for some operations
- Python packages: `requests`, `Pillow`, `jxlpy`, `pylibjxl`, `numpy`, `onnxruntime-gpu`, `py7zr`
- Optional: `rarfile` + `unrar` for CBR support

## Usage

### CLI

```bash
# Full batch workflow (process folders and archives in directory)
bdlib /path/to/library_root

# Process single folder
bdlib /path/to/folder --single

# Process single archive
bdlib /path/to/comic.cbz --single
bdlib /path/to/comic.cbr --single
bdlib /path/to/comic.cb7 --single

# With JPEG artifact removal (DeJPEG)
bdlib /path/to/comics --dejpeg

# With DeJPEG and CUDA (default with GPU)
bdlib /path/to/comics --dejpeg -t 1

# With Comic Vine enrichment
bdlib /path/to/comics --comicvine

# Custom quality and threads
bdlib /path/to/comics -q 85 -t 8
```

### DeJPEG Options

| Flag | Description | Default |
|------|-------------|---------|
| `--dejpeg` | Enable JPEG artifact removal | Disabled |
| `--dejpeg-model` | Model to use | fbcnn_color |

**Available models:** `fbcnn_color`, `waifu2x_cunet_art`, `waifu2x_cunet_photo`, `waifu2x_swin_unet_art`, `waifu2x_swin_unet_photo`, `waifu2x_swin_unet_art_scan`

Each waifu2x model supports noise levels 0-3 (e.g., `waifu2x_swin_unet_art:noise2`) and optional 2x upscaling (`scale2x`).

**Note:** Use `-jt 1` with CUDA to avoid GPU memory exhaustion.

### Python API

```python
from pathlib import Path
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.converters.archive import extract_archive, is_archive
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata import extract_folder_metadata
from bdlib.config import config, set_api_key
from bdlib.models import ComicMetadata

# Extract folder-based metadata
metadata = extract_folder_metadata(Path("path/to/folder"))

# Extract archive to temporary folder
if is_archive(Path("comic.cbz")):
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_dir = extract_archive(Path("comic.cbz"), Path(tmpdir) / "extracted")
        metadata = extract_folder_metadata(extract_dir, archive_path=Path("comic.cbz"))

# Convert images
jpeg_to_jxl.batch_convert("input/", "output/", quality=90)

# Generate metadata
xml = generate_comicinfo(metadata)

# Create CBZ
cbz.create_cbz("images/", "output.cbz")
```

## Project Structure

```
bdlib/
├── cli/
│   ├── __init__.py         # Plugin interface definitions
│   ├── dto.py              # Data transfer objects
│   └── main.py             # Command-line interface
├── config.py               # Configuration management
├── log.py                  # Logging configuration
├── models.py               # ComicMetadata dataclass
├── converters/
│   ├── __init__.py
│   ├── archive/            # Archive extraction
│   │   ├── __init__.py    # Factory functions
│   │   ├── base.py        # ArchiveExtractor interface
│   │   ├── cbz.py         # CBZ extraction (zipfile)
│   │   ├── cbr.py         # CBR extraction (rarfile, optional)
│   │   └── cb7.py          # CB7 extraction (py7zr)
│   ├── cbz.py              # CBZ archive creation
│   ├── jpeg_to_jxl.py      # JPEG → JXL conversion
│   └── dejpeg/             # JPEG artifact removal (AI models)
│       ├── __init__.py    # Factory and batch functions
│       ├── protocol.py    # DejpegModel interface
│       ├── tiled.py       # Tiled processing utilities
│       ├── fbcnn.py       # FBCNN model
│       └── waifu2x.py     # waifu2x model
├── metadata/
│   ├── __init__.py         # Metadata package exports
│   ├── comicinfo.py        # ComicInfo.xml generation
│   ├── path.py           # Path-based metadata extraction
│   └── comicvine/          # Comic Vine API integration
│       ├── __init__.py
│       └── client.py       # Comic Vine API client
└── plugins/
    ├── __init__.py
    ├── converter.py        # Converter plugin
    ├── general.py          # General plugin (CLI args)
    └── metadata/
        ├── __init__.py
        └── comicvine.py    # Comic Vine metadata plugin
```

## Configuration

On first use of Comic Vine features, the CLI prompts for an API key (free from https://comicvine.gamespot.com/api/).

Config and cache are stored in `~/.bd_library_manager/`.

## Naming Convention

For batch processing, use the following naming patterns:

### Folders
```
Series Name/01 - Issue Title/
    ├── page01.jpg
    └── page02.jpg
```

### Archives
```
Series Name/01 - Issue Title.cbz
Series Name/01.cbz
Series Name/Vol. 01.cbz
Series Name/Tome 01.cbz
```

### Supported Patterns

| Pattern | Number | Title |
|---------|--------|-------|
| `01 - Issue Title` | 1 | "Issue Title" |
| `01` | 1 | None |
| `Vol. 01` | 1 | None |
| `Tome 01` | 1 | None |
| `Volume 01` | 1 | None |

Example:
```
Batman/
├── 01 - The Killing Joke/
│   ├── page01.jpg
│   └── page02.jpg
├── 02 - A Death in the Family/
│   └── ...
├── 03.cbz
└── 04 - Knightfall.cbz
```
