#!/usr/bin/env python3
"""
DeJPEG package for JPEG artifact removal using AI models.

Supports multiple models:
- FBCNN: Fast JPEG artifact removal
- waifu2x: Neural network upscaling with tiled processing

Example usage:
    from bdlib.converters.dejpeg import create_model, batch_convert

    model, config = create_model("fbcnn_color")
    model, config = create_model("waifu2x_swin_unet_art:noise0")

    batch_convert(input_dir, output_dir, model_string="waifu2x_swin_unet_art:noise0")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np
from PIL import Image

from bdlib.models import PageInfo

from .fbcnn import FBCNNModel
from .fbcnn import create as create_fbcnn
from .protocol import DejpegModel
from .tiled import TilingConfig, float_array_to_pil, pil_to_float_array  # noqa: F401
from .waifu2x import (
    AVAILABLE_MODELS,
    Waifu2xConfig,
    Waifu2xModel,
)
from .waifu2x import (
    create as create_waifu2x,
)

__all__ = [
    "DejpegModel",
    "FBCNNModel",
    "Waifu2xModel",
    "Waifu2xConfig",
    "TilingConfig",
    "create_model",
    "batch_convert",
    "convert_jpeg",
    "pil_to_float_array",
    "float_array_to_pil",
    "AVAILABLE_MODELS",
]


class ModelType(Enum):
    """Enum for supported model types."""

    FBCNN = "fbcnn_color"
    WAIFU2X = "waifu2x"


@dataclass
class DejpegResult:
    """Result of a batch conversion."""

    success: bool
    model_name: str
    model_type: str
    config: dict
    stats: dict
    pages: list[PageInfo]


def get_model_info(model_string: str) -> dict:
    """Get human-readable info about a model."""
    config = _parse_model_string(model_string)

    if config.model_name == "fbcnn_color":
        return {
            "name": "FBCNN Color",
            "type": "jpeg_artifacts",
            "description": "Fast JPEG artifact removal",
        }

    if config.model_name.startswith("waifu2x_"):
        parts = config.model_name.replace("waifu2x_", "").split("_")
        arch = parts[0] if parts else "unknown"
        model_type = "_".join(parts[1:]) if len(parts) > 1 else "unknown"

        type_display = {
            "art": "Anime/Art",
            "photo": "Photographic",
            "art_scan": "Scanned Art",
        }.get(model_type, model_type)

        arch_display = {
            "cunet": "CuNet (Classic)",
            "swin_unet": "SwinUNet (Modern)",
        }.get(arch, arch)

        return {
            "name": f"waifu2x {arch_display}",
            "type": f"waifu2x_{model_type}",
            "noise_level": config.noise_level,
            "scale_factor": config.scale_factor,
            "description": f"{type_display} - Noise Level {config.noise_level}, Scale {config.scale_factor}x",
        }

    return {"name": config.model_name, "type": "unknown", "description": ""}


@dataclass
class _ParsedModelConfig:
    """Internal model configuration parsed from string."""

    model_name: str
    noise_level: int = 0
    scale_factor: int = 1


def _parse_model_string(model_string: str) -> _ParsedModelConfig:
    """Parse model string safely, returning config object."""
    noise_level = 0
    scale_factor = 1

    parts = model_string.split(":")
    model_name = parts[0]

    for part in parts[1:]:
        if part.startswith("noise"):
            noise_level = int(part[5:])
        elif part.startswith("scale"):
            scale_str = part[5:]
            if scale_str.endswith("x"):
                scale_factor = int(scale_str[:-1])
            else:
                scale_factor = int(scale_str)

    return _ParsedModelConfig(
        model_name=model_name, noise_level=noise_level, scale_factor=scale_factor
    )


def create_model(model_string: str) -> tuple:
    """
    Create a model instance from a model string.

    Supports format: waifu2x_<arch>_<type>[:noise<N>[:scale<N>x]]
    Examples:
        fbcnn_color -> FBCNNModel
        waifu2x_swin_unet_art:noise0 -> Waifu2xModel
        waifu2x_cunet_photo:noise1:scale2x -> Waifu2xModel

    Returns:
        tuple: (model_instance, _ParsedModelConfig)
    """
    config = _parse_model_string(model_string)

    if config.model_name == "fbcnn_color":
        return create_fbcnn(), config

    if config.model_name.startswith("waifu2x_"):
        return create_waifu2x(model_string), config

    raise ValueError(f"Unknown model: {model_string}")


def pil_image_to_jxl_array(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to numpy array suitable for pylibjxl.encode.

    pylibjxl.encode expects: (H, W, C) uint8

    Args:
        image: PIL Image (RGB)

    Returns:
        uint8 numpy array of shape (height, width, channels)
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.array(image, dtype=np.uint8)


def convert_jpeg(
    input_path: Path,
    output_path: Path,
    model_instance: DejpegModel,
    output_jxl: bool = False,
    jxl_quality: int = 90,
    jxl_lossless: bool = False,
) -> PageInfo | None:
    """
    Remove JPEG artifacts from a single image.

    Args:
        input_path: Path to input JPEG image
        output_path: Path to save processed image
        model_instance: Model instance (DejpegModel protocol)
        output_jxl: If True, output as JXL instead of PNG
        jxl_quality: JXL quality (1-100)
        jxl_lossless: Use lossless JXL encoding

    Returns:
        PageInfo if successful, None otherwise
    """
    from bdlib.log import get_logger

    logger = get_logger(__name__)

    try:
        with Image.open(input_path) as img:
            if img.mode != "RGB":
                logger.debug(f"Converting {input_path} from {img.mode} to RGB for processing")
                img_for_processing = img.convert("RGB")
            else:
                img_for_processing = img

            processed_img = model_instance.convert(img_for_processing)

        if output_jxl:
            import pylibjxl

            distance = (100 - jxl_quality) / 100 * 15.0 if not jxl_lossless else 0.0
            distance = max(0.1, distance)
            data = pil_image_to_jxl_array(processed_img)
            jxl_bytes = pylibjxl.encode(data, effort=7, distance=distance, lossless=jxl_lossless)
            output_path.write_bytes(jxl_bytes)
            size = output_path.stat().st_size
        else:
            processed_img.save(output_path, format="PNG", compress_level=6)
            size = output_path.stat().st_size

        logger.debug(f"Processed {input_path.name} -> {output_path.name}")
        return PageInfo(
            filename=output_path.name,
            width=processed_img.width,
            height=processed_img.height,
            size=size,
        )

    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        return None


def process_file(
    jpeg_file: Path,
    output_dir: Path,
    model_instance: DejpegModel,
    output_jxl: bool = False,
    jxl_quality: int = 90,
    jxl_lossless: bool = False,
) -> PageInfo | None:
    """
    Process a single JPEG file for dejpeg conversion.

    Args:
        jpeg_file: Path to input JPEG file
        output_dir: Directory to save processed file
        model_instance: Model instance (DejpegModel protocol)
        output_jxl: If True, output as JXL instead of PNG
        jxl_quality: JXL quality (1-100)
        jxl_lossless: Use lossless JXL encoding

    Returns:
        PageInfo if successful, None otherwise
    """
    from bdlib.log import get_logger

    logger = get_logger(__name__)

    if output_jxl:
        output_file = output_dir / (jpeg_file.stem + ".jxl")
    else:
        output_file = output_dir / (jpeg_file.stem + ".png")

    page_info = convert_jpeg(
        jpeg_file, output_file, model_instance, output_jxl, jxl_quality, jxl_lossless
    )
    if page_info:
        logger.info(f"DeJPEG processed {jpeg_file.name} -> {output_file.name} ... OK")
    else:
        logger.error(f"DeJPEG processed {jpeg_file.name} -> {output_file.name} ... FAILED")

    return page_info


def batch_convert(
    input_dir: Path,
    output_dir: Path,
    max_threads: int = 4,
    model_string: str = "fbcnn_color",
    output_jxl: bool = False,
    jxl_quality: int = 90,
    jxl_lossless: bool = False,
) -> DejpegResult:
    """
    Convert all JPEG images in a directory using specified model with multiple threads.

    Args:
        input_dir: Path to input directory
        output_dir: Path to output directory
        max_threads: Maximum number of threads to use
        model_string: Model string (e.g., "fbcnn_color" or "waifu2x_swin_unet_art:noise1")
        output_jxl: If True, output as JXL instead of PNG
        jxl_quality: JXL quality (1-100)
        jxl_lossless: Use lossless JXL encoding

    Returns:
        DejpegResult with processing stats
    """
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from bdlib.log import get_logger

    logger = get_logger(__name__)

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jpeg_extensions = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]
    jpeg_files = [file for ext in jpeg_extensions for file in input_dir.glob(ext)]

    if not jpeg_files:
        logger.warning(f"No JPEG files found in {input_dir}")
        return DejpegResult(
            success=False,
            model_name="",
            model_type="",
            config={},
            stats={"error": "No JPEG files found"},
            pages=[],
        )

    model_info = get_model_info(model_string)
    logger.info(
        f"DeJPEG model: {model_info['name']} - {model_info.get('description', model_info['type'])}"
    )

    model_instance, config = create_model(model_string)
    logger.debug(f"Model config: {config}")

    start_time = time.time()
    processed_count = 0
    failed_count = 0
    page_infos: list[PageInfo] = []

    def process_one(jpeg_file):
        nonlocal processed_count, failed_count
        file_start = time.time()
        page_info = process_file(
            jpeg_file, output_dir, model_instance, output_jxl, jxl_quality, jxl_lossless
        )
        file_duration = time.time() - file_start

        if page_info:
            processed_count += 1
            page_infos.append(page_info)
        else:
            failed_count += 1

        logger.info(
            f"DeJPEG processing: {jpeg_file.name} [{processed_count}/{len(jpeg_files)}] ({file_duration * 1000:.0f}ms)"
        )

    logger.info(f"Found {len(jpeg_files)} JPEG files to process with DeJPEG")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        future_to_file = {
            executor.submit(process_one, jpeg_file): jpeg_file for jpeg_file in jpeg_files
        }

        for future in as_completed(future_to_file):
            jpeg_file = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing {jpeg_file.name}: {e}")
                failed_count += 1

    total_duration = time.time() - start_time
    avg_duration = (total_duration / processed_count * 1000) if processed_count > 0 else 0

    result = DejpegResult(
        success=True,
        model_name=model_info["name"],
        model_type=model_info["type"],
        config={
            "model_name": config.model_name,
            "noise_level": config.noise_level,
            "scale_factor": config.scale_factor,
        },
        stats={
            "total_pages": len(jpeg_files),
            "processed_pages": processed_count,
            "failed_pages": failed_count,
            "total_duration_ms": int(total_duration * 1000),
            "average_duration_ms": int(avg_duration),
        },
        pages=page_infos,
    )

    logger.info(
        f"DeJPEG batch processing completed: {processed_count}/{len(jpeg_files)} pages processed ({total_duration:.1f}s)"
    )
    return result


def get_available_models() -> list:
    """Return list of available model strings."""
    models = ["fbcnn_color"]
    for base_model in AVAILABLE_MODELS:
        for noise in range(4):
            models.append(f"{base_model}:noise{noise}")
        for noise in range(4):
            models.append(f"{base_model}:noise{noise}:scale2x")
    return models
