# BD Library Manager - Project Context

## Overview

A Python library and CLI tool for automating comic archive preparation. Process folders of comic pages (JPEG) into clean comic archives with JPEG XL conversion, AI-powered artifact removal, ComicInfo.xml metadata generation, and CBZ archive creation.

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
│   ├── folder.py           # Folder-based metadata extraction
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

- **Setup**: `virtualenv .venv && source .venv/bin/activate && uv pip install -r requirements.txt`
- **Dev deps**: `uv pip install pytest ruff mypy`
- **Testing**: `pytest` or `python -m pytest`
- **Linting**: `ruff check .`
- **Typecheck**: `mypy bdlib`

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

### 2. Data Models

`ComicMetadata` is a `@dataclass` in `models.py`. All fields are Optional with sensible defaults. Includes `to_dict()` and `merge()` methods.

### 3. Converters Pattern

Converters are organized in `bdlib/converters/` with a public `__init__.py` that exports the API:

```python
# bdlib/converters/__init__.py
from bdlib.converters.my_converter import my_function

__all__ = ["my_function"]
```

### 4. Metadata Pattern

Metadata modules follow the same pattern as converters - organized subpackage with `__init__.py` exports.

### 5. Tests

- Location: `tests/` directory
- Fixtures: `tests/conftest.py`
- Sample data: `tests/sample/`
- Run: `pytest` (with venv activated)

## How to Extend the Project

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
