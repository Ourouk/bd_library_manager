#!/usr/bin/env python3
"""
Base interface for DeJPEG models.
"""

from typing import Protocol, runtime_checkable

from PIL import Image


@runtime_checkable
class DejpegModel(Protocol):
    """Protocol for DeJPEG model implementations."""

    @property
    def name(self) -> str:
        """Model name."""
        ...

    def preprocess(self, image: Image.Image) -> bytes:
        """Preprocess PIL Image to model input format."""
        ...

    def run(self, input_data: bytes) -> bytes:
        """Run inference on preprocessed input."""
        ...

    def postprocess(self, output_data: bytes) -> Image.Image:
        """Convert model output to PIL Image."""
        ...

    def convert(self, image: Image.Image) -> Image.Image:
        """Convert a single image."""
        ...

    def supports_tiled_processing(self) -> bool:
        """Whether this model supports tiled processing."""
        ...
