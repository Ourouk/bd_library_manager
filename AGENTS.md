# BD Library Manager - Project Context

## Overview

A Python library and CLI tool for automating comic archive preparation. Process folders of comic pages (JPEG) or comic archives (CBZ/CBR/CB7) into clean JXL-based archives with JPEG XL conversion, AI-powered artifact removal, ComicInfo.xml metadata generation, and CBZ archive creation.

## Input Formats

- **Folders**: Directories containing JPEG images
- **Archives**: CBZ, CBR, CB7 comic archives (automatically extracted for processing)

## Project Structure

```
bdlib/
├── cli/
│   ├── __init__.py         # CliPlugin protocol definition
│   ├── dto.py              # Data transfer objects (ProcessingConfig, etc.)
│   └── main.py             # CLI entry point
├── config.py               # Configuration management
├── log.py                  # Logging configuration
├── models.py               # ComicMetadata dataclass
├── converters/             # Image format conversion
│   ├── __init__.py         # Public API exports
│   ├── archive/            # Archive extraction
│   │   ├── __init__.py    # Factory: is_archive(), extract_archive()
│   │   ├── base.py        # ArchiveExtractor interface
│   │   ├── cbz.py         # CBZ extraction (stdlib zipfile)
│   │   ├── cbr.py         # CBR extraction (rarfile, optional)
│   │   └── cb7.py          # CB7 extraction (py7zr)
│   ├── cbz.py             # CBZ archive creation
│   ├── jpeg_to_jxl.py     # JPEG → JXL conversion
│   └── dejpeg/            # JPEG artifact removal (AI models)
│       ├── __init__.py    # Factory and batch functions
│       ├── protocol.py    # DejpegModel interface
│       ├── tiled.py       # Tiled processing utilities
│       ├── fbcnn.py       # FBCNN model implementation
│       └── waifu2x.py     # waifu2x model implementation
├── metadata/              # Metadata handling
│   ├── __init__.py         # Public API exports
│   ├── comicinfo.py        # ComicInfo.xml generation
│   ├── path.py             # Path-based metadata extraction
│   └── comicvine/          # Comic Vine API integration
│       ├── __init__.py
│       └── client.py
└── plugins/              # CLI plugin system
    ├── __init__.py         # Plugin discovery via entry_points
    ├── converter.py        # Converter plugin (--dejpeg)
    ├── general.py          # General plugin (input/output args)
    └── metadata/
        ├── __init__.py
        └── comicvine.py    # Comic Vine metadata plugin
```

## Python Environment

This project uses `uv` and `virtualenv` for dependency management:

- **Setup**: `virtualenv .venv && source .venv/bin/activate && uv pip install -e ".[dev]"`
- **Dev deps**: `uv pip install pytest ruff mypy`
- **CBR support**: `uv pip install -e ".[cbr]"` (requires unrar system package)
- **Testing**: `pytest` or `python -m pytest`
- **Linting**: `ruff check .`
- **Typecheck**: `mypy bdlib`

## Naming Conventions

### Supported Patterns

The metadata extractor (`path.py`) recognizes these naming patterns:

| Pattern | Number | Title |
|---------|--------|-------|
| `01 - Issue Title` | 1 | "Issue Title" |
| `01` | 1 | None |
| `Vol. 01` | 1 | None |
| `Tome 01` | 1 | None |
| `Volume 01` | 1 | None |

### Customizing Patterns

Regex patterns can be customized via module-level constants or function argument:

```python
# Method 1: Override module-level constants
from bdlib.metadata import path
path.PATTERN_WITH_TITLE = r"(\d+)\s*#\s*(.+)"
path.PATTERN_NUMBER_ONLY = r"#(\d+)"

# Method 2: Pass patterns tuple to function
from bdlib.metadata import extract_folder_metadata
meta = extract_folder_metadata(
    folder,
    archive_path=archive,
    patterns=(r"(\d+)#(.+)", r"#(\d+)", r"T(\d+)")
)
```

## Key Patterns

### 1. Entry Points (Plugin System)

Plugins are discovered via setuptools entry points in `pyproject.toml`:

```toml
[project.entry-points."bdlib.plugins"]
general = "bdlib.plugins.general:GeneralPlugin"
converter = "bdlib.plugins.converter:ConverterPlugin"
```

The `CliPlugin` protocol requires two methods:
```python
from bdlib.cli import CliPlugin

class MyPlugin(CliPlugin):
    def register_arguments(self, parser: ArgumentParser) -> None: ...
    def handle_arguments(self, args: Namespace) -> dict: ...
```

### 2. Archive Extractors

Archive extraction uses a factory pattern with individual extractors per format:

```python
from bdlib.converters.archive import is_archive, extract_archive, get_extractor

# Check if path is an archive
if is_archive(path):
    extractor = get_extractor(path)
    extractor.extract(path, output_dir)
```

Each extractor follows the `ArchiveExtractor` interface in `base.py`.

### 3. Data Models

`ComicMetadata` is a `@dataclass` in `models.py`. All fields are Optional with sensible defaults. Includes `to_dict()` and `merge()` methods.

### 4. Converters Pattern

Converters are organized in `bdlib/converters/` with a public `__init__.py` that exports the API:

```python
# bdlib/converters/__init__.py
from bdlib.converters.my_converter import my_function

__all__ = ["my_function"]
```

### 5. Metadata Pattern

Metadata modules follow the same pattern as converters - organized subpackage with `__init__.py` exports.

### 6. Tests

- Location: `tests/` directory
- Fixtures: `tests/conftest.py`
- Sample data: `tests/sample/`
- Run: `pytest` (with venv activated)

## How to Extend the Project

### Adding a New Archive Format

1. Create `bdlib/converters/archive/my_format.py`
2. Implement `ArchiveExtractor` interface:

```python
from pathlib import Path
from bdlib.converters.archive.base import ArchiveExtractor

class MyExtractor(ArchiveExtractor):
    @property
    def extensions(self) -> list[str]:
        return [".myfmt", ".MYFMT"]

    def extract(self, archive_path: Path, output_dir: Path) -> Path:
        # Extraction logic
        return output_dir
```

3. Register in `bdlib/converters/archive/__init__.py`

### Adding a New Converter

1. Create `bdlib/converters/my_format.py`
2. Implement your conversion logic
3. Export in `bdlib/converters/__init__.py`:

```python
from bdlib.converters.my_format import convert_foo

__all__ = [
    # ... existing exports ...
    "convert_foo",
]
```

### Adding a New Metadata Source

1. Create `bdlib/metadata/my_source.py`
2. Implement metadata extraction logic
3. Export in `bdlib/metadata/__init__.py`

### Adding a New CLI Plugin

1. Create `bdlib/plugins/my_plugin.py`
2. Implement `CliPlugin` protocol:

```python
from argparse import ArgumentParser, Namespace
from bdlib.cli import CliPlugin

class MyPlugin(CliPlugin):
    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--my-flag", action="store_true", help="My feature")
    
    def handle_arguments(self, args: Namespace) -> dict:
        return {"my_feature": args.my_flag}
```

3. Register in `pyproject.toml`:

```toml
[project.entry-points."bdlib.plugins"]
my_plugin = "bdlib.plugins.my_plugin:MyPlugin"
```

### Adding a New Model

Extend `ComicMetadata` in `bdlib/models.py` by adding new fields as `@dataclass` attributes:

```python
@dataclass
class ComicMetadata:
    # ... existing fields ...
    my_new_field: Optional[str] = None
```

## Important Conventions

- **Python version**: 3.10+ (configured in pyproject.toml)
- **Line length**: 100 characters (ruff)
- **Use ruff** for linting before committing
- **Type hints**: Optional but encouraged
- **Entry points**: Must be registered in `pyproject.toml` to be discovered
- **Public API**: Expose via `__all__` in package `__init__.py` files
