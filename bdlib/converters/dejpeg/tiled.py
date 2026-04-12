#!/usr/bin/env python3
"""
Tiled image processing utilities for DeJPEG models.

Provides seam blending functionality that can be used by any model
that supports tiled inference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Protocol, Tuple, TypeVar

import numpy as np
from PIL import Image

T = TypeVar("T")


class TileProcessor(Protocol[T]):
    """Protocol for tile processing functions."""

    def __call__(self, tile: np.ndarray) -> T: ...


@dataclass
class TileInfo:
    """Information about a tile extracted from an image."""

    data: np.ndarray
    h_start: int
    h_end: int
    w_start: int
    w_end: int


@dataclass
class TilingConfig:
    """Configuration for tiled processing."""

    tile_size: int
    offset: int
    blend_size: int
    scale: int
    h_blocks: int
    w_blocks: int
    output_tile_step: int
    input_tile_step: int
    pad: Tuple[int, int, int, int]
    output_buffer_h: int
    output_buffer_w: int
    input_offset: int
    original_h: int
    original_w: int


def create_blend_filter(blend_size: int, tile_size: int, scale: int, channels: int) -> np.ndarray:
    """
    Create a weight filter for blending overlapping tile edges.

    Args:
        blend_size: Size of the blending region on each edge
        tile_size: Size of the output tile
        scale: Upscaling factor
        channels: Number of image channels

    Returns:
        Weight array of shape (channels, tile_size, tile_size) where:
        - Center: weight = 1.0 (use new tile fully)
        - Edges: weight = 0.0 (blend with accumulated)
    """
    model_output_size = tile_size * scale
    inner_tile_size = model_output_size - blend_size * 2

    if inner_tile_size <= 0:
        inner_tile_size = 1

    weight = np.ones((channels, inner_tile_size, inner_tile_size), dtype=np.float32)

    for i in range(blend_size):
        value = (1 / (blend_size + 1)) * (i + 1)
        weight = np.pad(weight, ((0, 0), (1, 1), (1, 1)), mode="constant", constant_values=value)

    return weight.astype(np.float32)


def calculate_tiling_config(
    image_shape: Tuple[int, int], tile_size: int, offset: int, blend_size: int, scale: int
) -> TilingConfig:
    """
    Calculate tiling configuration for an image.

    Args:
        image_shape: (height, width) of the image
        tile_size: Size of each tile
        offset: Padding around each tile (reduces effective output by 2*offset)
        blend_size: Size of blending region
        scale: Upscaling factor

    Returns:
        TilingConfig with calculated values
    """
    h, w = image_shape

    input_offset = int(math.ceil(offset / scale))

    effective_tile_output = tile_size - 2 * input_offset

    tile_step = effective_tile_output - 2 * blend_size
    if tile_step <= 0:
        tile_step = max(1, effective_tile_output // 2)

    h_blocks = max(1, (h + tile_step - 1) // tile_step + 1)
    w_blocks = max(1, (w + tile_step - 1) // tile_step + 1)

    input_h = h_blocks * tile_step + 2 * input_offset + 2 * blend_size
    input_w = w_blocks * tile_step + 2 * input_offset + 2 * blend_size

    output_tile_step = tile_step * scale
    output_h = input_h * scale
    output_w = input_w * scale

    pad_left = input_offset + blend_size
    pad_right = input_w - (w + input_offset + blend_size)
    pad_top = input_offset + blend_size
    pad_bottom = input_h - (h + input_offset + blend_size)

    return TilingConfig(
        tile_size=tile_size,
        offset=offset,
        blend_size=blend_size,
        scale=scale,
        h_blocks=h_blocks,
        w_blocks=w_blocks,
        output_tile_step=output_tile_step,
        input_tile_step=tile_step,
        pad=(pad_left, pad_right, pad_top, pad_bottom),
        output_buffer_h=output_h,
        output_buffer_w=output_w,
        input_offset=input_offset,
        original_h=h,
        original_w=w,
    )


def pad_image(image: np.ndarray, pad: Tuple[int, int, int, int]) -> np.ndarray:
    """
    Pad an image with edge replication.

    Args:
        image: Image array of shape (C, H, W)
        pad: (left, right, top, bottom) padding values

    Returns:
        Padded image array
    """
    if len(image.shape) == 2:
        image = np.expand_dims(image, axis=0)

    left, right, top, bottom = pad

    padded = np.pad(image, ((0, 0), (top, bottom), (left, right)), mode="edge")

    return padded


def split_into_tiles(
    padded_image: np.ndarray, tile_size: int, h_blocks: int, w_blocks: int, input_tile_step: int
) -> List[TileInfo]:
    """
    Split a padded image into overlapping tiles.

    Args:
        padded_image: Padded image array of shape (C, H, W)
        tile_size: Size of each tile
        h_blocks: Number of horizontal blocks
        w_blocks: Number of vertical blocks
        input_tile_step: Step size between tiles

    Returns:
        List of TileInfo
    """
    tiles = []
    channels = padded_image.shape[0]

    for h_i in range(h_blocks):
        for w_i in range(w_blocks):
            h_start = h_i * input_tile_step
            w_start = w_i * input_tile_step

            h_end = h_start + tile_size
            w_end = w_start + tile_size

            if h_end > padded_image.shape[1]:
                h_end = padded_image.shape[1]
                h_start = h_end - tile_size
            if w_end > padded_image.shape[2]:
                w_end = padded_image.shape[2]
                w_start = w_end - tile_size

            tile = padded_image[:, h_start:h_end, w_start:w_end]

            if tile.shape[1] < tile_size or tile.shape[2] < tile_size:
                new_tile = np.zeros((channels, tile_size, tile_size), dtype=tile.dtype)
                new_tile[:, : tile.shape[1], : tile.shape[2]] = tile
                tile = new_tile

            tiles.append(TileInfo(tile, h_start, h_end, w_start, w_end))

    return tiles


def blend_and_assemble(
    processed_tiles: List[np.ndarray], tile_infos: List[TileInfo], config: TilingConfig
) -> np.ndarray:
    """
    Blend processed tiles back into a single image using seam blending.

    Args:
        processed_tiles: List of processed tile arrays
        tile_infos: List of TileInfo for each tile
        config: Tiling configuration

    Returns:
        Reconstructed image array
    """
    channels = processed_tiles[0].shape[0] if len(processed_tiles) > 0 else 3
    output_buffer_h = config.output_buffer_h
    output_buffer_w = config.output_buffer_w

    pixels = np.zeros((channels, output_buffer_h, output_buffer_w), dtype=np.float32)
    weights = np.zeros((channels, output_buffer_h, output_buffer_w), dtype=np.float32)

    blend_filter = None
    if config.blend_size > 0:
        processed_tile_size = processed_tiles[0].shape[2]
        blend_filter = create_blend_filter(config.blend_size, processed_tile_size, config.scale, channels)

    for tile_data, tile_info in zip(processed_tiles, tile_infos):
        h_out_start = tile_info.h_start * config.scale
        w_out_start = tile_info.w_start * config.scale

        out_h = tile_data.shape[1]
        out_w = tile_data.shape[2]

        h_out_end = min(h_out_start + out_h, output_buffer_h)
        w_out_end = min(w_out_start + out_w, output_buffer_w)

        clipped_h = h_out_end - h_out_start
        clipped_w = w_out_end - w_out_start

        if clipped_h <= 0 or clipped_w <= 0:
            continue

        h_slice = slice(h_out_start, h_out_end)
        w_slice = slice(w_out_start, w_out_end)

        region_weights = weights[:, h_slice, w_slice]

        if blend_filter is not None:
            tile_weights = np.clip(blend_filter[:, :clipped_h, :clipped_w], 0, 1)
            tile_weights = np.maximum(tile_weights, 1e-6)

            new_pixel_sum = (
                pixels[:, h_slice, w_slice] * weights[:, h_slice, w_slice]
                + tile_data[:, :clipped_h, :clipped_w] * tile_weights
            )
            new_weight_sum = region_weights + tile_weights

            pixels[:, h_slice, w_slice] = new_pixel_sum / new_weight_sum
            weights[:, h_slice, w_slice] = new_weight_sum
        else:
            pixels[:, h_slice, w_slice] = tile_data[:, :clipped_h, :clipped_w]

    result_h = config.original_h * config.scale
    result_w = config.original_w * config.scale

    result = pixels[:, :result_h, :result_w]

    return np.clip(result, 0, 1)


def tiled_process(
    image: np.ndarray, process_fn: Callable[[np.ndarray], np.ndarray], config: TilingConfig
) -> np.ndarray:
    """
    Process an image using tiled inference with seam blending.

    Args:
        image: Input image array of shape (C, H, W) or (H, W)
        process_fn: Function to process each tile, takes (tile_array) returns processed tile
        config: Tiling configuration

    Returns:
        Processed image array
    """
    if len(image.shape) == 2:
        image = np.expand_dims(image, axis=0)

    padded_image = pad_image(image, config.pad)

    tiles = split_into_tiles(
        padded_image,
        tile_size=config.tile_size,
        h_blocks=config.h_blocks,
        w_blocks=config.w_blocks,
        input_tile_step=config.input_tile_step,
    )

    processed_tiles = []
    for tile_info in tiles:
        processed = process_fn(tile_info.data)
        if processed.ndim == 4:
            processed = np.squeeze(processed, axis=0)
        processed_tiles.append(processed)

    result = blend_and_assemble(processed_tiles, tiles, config)

    return result


def pil_to_float_array(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to float array in [0, 1] range."""
    if image.mode != "RGB":
        image = image.convert("RGB")
    img_array = np.array(image, dtype=np.float32) / 255.0
    img_array = np.transpose(img_array, (2, 0, 1))
    return img_array


def float_array_to_pil(array: np.ndarray) -> Image.Image:
    """Convert float array back to PIL Image."""
    array = (array * 255.0).astype(np.uint8)
    array = np.transpose(array, (1, 2, 0))
    return Image.fromarray(array, mode="RGB")
