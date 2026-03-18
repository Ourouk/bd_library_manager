# BD Library Manager

A Python library and CLI tool for automating comic archive preparation.

## What this project does

Process folders of comic pages (JPEG) into clean comic archives:

- Converts JPEG pages to JPEG XL (`.jxl`)
- Removes JPEG artifacts using FBCNN or waifu2x (AI-powered, CUDA-accelerated)
- Supports tiled processing with seam blending for waifu2x models
- Generates `ComicInfo.xml` metadata
- Optionally enriches metadata from Comic Vine API
- Builds `.cbz` archives ready for comic readers
- Supports batch processing for multiple folders

## Installation

```bash
# Clone and install in editable mode
pip install -e .

# Or install dependencies only
pip install requests Pillow jxlpy pylibjxl numpy onnxruntime-gpu
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
- Python packages: `requests`, `Pillow`, `jxlpy`, `pylibjxl`, `numpy`, `onnxruntime-gpu`

## Usage

### CLI

```bash
# Full batch workflow
bdlib /path/to/library_root

# With JPEG artifact removal (DeJPEG)
bdlib /path/to/comics --dejpeg

# With DeJPEG and CUDA (default with GPU)
bdlib /path/to/comics --dejpeg -t 1

# With Comic Vine enrichment
bdlib /path/to/comics --comicvine

# Process single folder
bdlib /path/to/folder --single

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
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.metadata.comicinfo import generate_comicinfo
from bdlib.metadata import extract_folder_metadata
from bdlib.config import config, set_api_key
from bdlib.models import ComicMetadata

# Extract folder-based metadata
metadata = extract_folder_metadata(Path("path/to/folder"))

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
│   ├── cbz.py              # CBZ archive creation
│   ├── jpeg_to_jxl.py     # JPEG → JXL conversion
│   └── dejpeg/             # JPEG artifact removal (AI models)
│       ├── __init__.py    # Factory and batch functions
│       ├── protocol.py    # DejpegModel interface
│       ├── tiled.py       # Tiled processing utilities
│       ├── fbcnn.py       # FBCNN model
│       └── waifu2x.py     # waifu2x model
├── metadata/
│   ├── __init__.py         # Metadata package exports
│   ├── comicinfo.py        # ComicInfo.xml generation
│   ├── folder.py           # Folder-based metadata extraction
│   └── comicvine/          # Comic Vine API integration
│       ├── __init__.py
│       └── client.py       # Comic Vine API client
└── plugins/
    ├── __init__.py
    ├── __pycache__
    ├── converter.py        # Converter plugin
    ├── general.py          # General plugin (CLI args)
    └── metadata/
        ├── __init__.py
        └── comicvine.py    # Comic Vine metadata plugin
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
