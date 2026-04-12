# TL;DR

Process comic folders (JPEG) or archives (CBZ/CBR/CB7) into JXL-powered CBZ files with optional AI artifact removal and metadata enrichment.

## Install

```bash
pip install -e .
# or: uv pip install -e .
```

## Quick Start

```bash
# Process a folder
bdlib ./comics

# Process single archive
bdlib ./comic.cbz --single

# Convert with AI artifact removal (requires GPU)
bdlib ./comics --dejpeg

# With metadata enrichment
bdlib ./comics --comicvine
```

## Common Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o` | Output folder | Same as input |
| `-q` | JXL quality (1-100) | 90 |
| `-l` | Lossless compression | No |
| `--dejpeg` | AI artifact removal | No |
| `--dejpeg-model` | DeJPEG model | fbcnn_color |
| `-dt` | DeJPEG threads | 1 |
| `-jt` | JXL threads | 4 |
| `--single` | Process single folder | No |

## DeJPEG Models

- `fbcnn_color` (default, best quality)
- `waifu2x_cunet_art`
- `waifu2x_swin_unet_photo`
- Add `:noise0` to `:noise3` for noise levels
- Add `scale2x` for 2x upscaling

## CLI Entry Point

```bash
bdlib  [options]
```

## Python API

```python
from bdlib.converters import jpeg_to_jxl, cbz
from bdlib.metadata import extract_folder_metadata, generate_comicinfo

# Extract metadata from folder name
meta = extract_folder_metadata(Path("folder"))

# Convert JPEG to JXL
jpeg_to_jxl.batch_convert("input/", "output/", quality=90)

# Create CBZ archive
cbz.create_cbz("images/", "output.cbz")
```

## Requirements

- Python 3.14+
- `libjxl` (cjxl in PATH)
- (Optional) NVIDIA GPU + CUDA for DeJPEG