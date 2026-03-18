#!/usr/bin/env python3
"""
Placeholder module for backward compatibility.

All classes have been moved to bdlib.dto package:
- ComicMetadata, PageInfo, ConversionResult -> bdlib.dto
- ConverterConfig, MetadataConfig, ProcessingConfig -> bdlib.dto.cli

Import from the new locations:
    from bdlib.dto import ComicMetadata
    from bdlib.dto.cli import ProcessingConfig
"""

__all__ = []
