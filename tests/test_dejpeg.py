"""Test dejpeg module."""

import numpy as np
import pytest
from PIL import Image

from bdlib.converters.dejpeg import FBCNNModel, Waifu2xModel, create_model, get_available_models, pil_image_to_jxl_array
from bdlib.converters.dejpeg.tiled import (
    blend_and_assemble,
    calculate_tiling_config,
    create_blend_filter,
    pad_image,
    pil_to_float_array,
    split_into_tiles,
    tiled_process,
)


class TestTiledProcessing:
    """Test tiled processing utilities."""

    def test_create_blend_filter(self):
        """Test blend filter creation."""
        filter_3 = create_blend_filter(blend_size=3, tile_size=256, scale=1, channels=3)
        assert filter_3.shape == (3, 256, 256)
        assert filter_3[0, 0, 0] > 0.5
        assert filter_3[0, 128, 128] == 1.0

    def test_create_blend_filter_small_blend(self):
        """Test blend filter with small blend size."""
        filter_1 = create_blend_filter(blend_size=1, tile_size=256, scale=1, channels=1)
        assert filter_1.shape == (1, 256, 256)

    def test_calculate_tiling_config(self):
        """Test tiling configuration calculation."""
        config = calculate_tiling_config(image_shape=(1000, 800), tile_size=256, offset=22, blend_size=14, scale=1)
        assert config.tile_size == 256
        assert config.offset == 22
        assert config.blend_size == 14
        assert config.scale == 1
        assert config.h_blocks >= 1
        assert config.w_blocks >= 1
        assert config.original_h == 1000
        assert config.original_w == 800

    def test_calculate_tiling_config_scale2x(self):
        """Test tiling configuration with 2x scale."""
        config = calculate_tiling_config(image_shape=(500, 400), tile_size=256, offset=22, blend_size=14, scale=2)
        assert config.scale == 2
        assert config.original_h == 500
        assert config.original_w == 400

    def test_pad_image(self):
        """Test image padding."""
        image = np.random.rand(3, 100, 100).astype(np.float32)
        padded = pad_image(image, (10, 10, 10, 10))
        assert padded.shape == (3, 120, 120)
        assert padded[0, 0, 0] == padded[0, 10, 10]

    def test_pad_image_grayscale(self):
        """Test image padding with grayscale."""
        image = np.random.rand(100, 100).astype(np.float32)
        padded = pad_image(image, (5, 5, 5, 5))
        assert padded.shape == (1, 110, 110)

    def test_split_into_tiles(self):
        """Test splitting image into tiles."""
        image = np.random.rand(3, 300, 300).astype(np.float32)
        config = calculate_tiling_config(image_shape=(300, 300), tile_size=128, offset=16, blend_size=8, scale=1)
        padded = pad_image(image, config.pad)
        tiles = split_into_tiles(
            padded,
            tile_size=config.tile_size,
            h_blocks=config.h_blocks,
            w_blocks=config.w_blocks,
            input_tile_step=config.input_tile_step,
        )
        assert len(tiles) >= 1
        for tile in tiles:
            assert tile.data.shape[1] == config.tile_size
            assert tile.data.shape[2] == config.tile_size

    def test_blend_and_assemble_identity(self):
        """Test blend_and_assemble with identity processing."""
        image = np.random.rand(3, 100, 100).astype(np.float32)
        config = calculate_tiling_config(image_shape=(100, 100), tile_size=64, offset=8, blend_size=4, scale=1)
        padded = pad_image(image, config.pad)
        tiles = split_into_tiles(
            padded,
            tile_size=config.tile_size,
            h_blocks=config.h_blocks,
            w_blocks=config.w_blocks,
            input_tile_step=config.input_tile_step,
        )

        def identity(tile):
            return tile

        processed = [identity(t.data) for t in tiles]
        result = blend_and_assemble(processed, tiles, config)
        assert result.shape == (3, 100, 100)

    def test_blend_and_assemble_with_scale(self):
        """Test blend_and_assemble with scaling."""
        image = np.random.rand(3, 100, 100).astype(np.float32)
        config = calculate_tiling_config(image_shape=(100, 100), tile_size=64, offset=8, blend_size=4, scale=2)
        padded = pad_image(image, config.pad)
        tiles = split_into_tiles(
            padded,
            tile_size=config.tile_size,
            h_blocks=config.h_blocks,
            w_blocks=config.w_blocks,
            input_tile_step=config.input_tile_step,
        )

        def scale2x(tile):
            return np.repeat(np.repeat(tile, 2, axis=1), 2, axis=2)

        processed = [scale2x(t.data) for t in tiles]
        result = blend_and_assemble(processed, tiles, config)
        assert result.shape == (3, 200, 200)

    def test_tiled_process_simple(self):
        """Test full tiled_process function."""
        image = np.random.rand(3, 200, 200).astype(np.float32)
        config = calculate_tiling_config(image_shape=(200, 200), tile_size=128, offset=16, blend_size=8, scale=1)

        def identity(tile):
            return tile

        result = tiled_process(image, identity, config)
        assert result.shape == (3, 200, 200)
        assert result.min() >= 0
        assert result.max() <= 1

    def test_tiled_process_grayscale(self):
        """Test tiled_process with grayscale input."""
        image = np.random.rand(100, 100).astype(np.float32)
        config = calculate_tiling_config(image_shape=(100, 100), tile_size=64, offset=8, blend_size=4, scale=1)

        def identity(tile):
            return tile

        result = tiled_process(image, identity, config)
        assert result.shape == (1, 100, 100)


class TestPilConversions:
    """Test PIL image conversions."""

    def test_pil_to_float_array_rgb(self):
        """Test PIL to float array conversion for RGB."""
        img = Image.new("RGB", (100, 200), color=(255, 128, 64))
        array = pil_to_float_array(img)
        assert array.shape == (3, 200, 100)
        assert array[0, 0, 0] == 1.0
        assert array[1, 0, 0] == pytest.approx(128 / 255, rel=0.01)
        assert array[2, 0, 0] == pytest.approx(64 / 255, rel=0.01)

    def test_pil_to_float_array_grayscale(self):
        """Test PIL to float array conversion for grayscale."""
        img = Image.new("L", (100, 200), color=128)
        array = pil_to_float_array(img)
        assert array.shape == (3, 200, 100)
        assert array[0, 0, 0] == pytest.approx(128 / 255, rel=0.01)


class TestModelFactory:
    """Test model factory functions."""

    def test_get_available_models(self):
        """Test getting available models list."""
        models = get_available_models()
        assert len(models) > 0
        assert "fbcnn_color" in models
        assert any("waifu2x" in m for m in models)

    def test_create_fbcnn_model(self):
        """Test creating FBCNN model."""
        model, config = create_model("fbcnn_color")
        assert isinstance(model, FBCNNModel)
        assert model.name == "fbcnn_color"
        assert config.model_name == "fbcnn_color"

    def test_create_waifu2x_models(self):
        """Test creating various waifu2x models."""
        test_models = ["waifu2x_cunet_art", "waifu2x_cunet_photo", "waifu2x_swin_unet_art", "waifu2x_swin_unet_photo"]
        for model_str in test_models:
            model, config = create_model(model_str)
            assert isinstance(model, Waifu2xModel)
            assert "waifu2x" in model.name

    def test_create_waifu2x_with_noise(self):
        """Test creating waifu2x model with noise level."""
        model, config = create_model("waifu2x_swin_unet_art:noise2")
        assert isinstance(model, Waifu2xModel)
        assert config.noise_level == 2

    def test_create_waifu2x_with_scale(self):
        """Test creating waifu2x model with scale."""
        model, config = create_model("waifu2x_cunet_art:noise0:scale2x")
        assert isinstance(model, Waifu2xModel)
        assert config.scale_factor == 2

    def test_create_invalid_model(self):
        """Test creating invalid model raises error."""
        import pytest

        with pytest.raises(ValueError):
            create_model("invalid_model")


class TestFBCNNModel:
    """Test FBCNN model."""

    def test_fbcnn_supports_tiled(self, sample_image_file):
        """Test FBCNN does not support tiled processing."""
        model, _ = create_model("fbcnn_color")
        assert not model.supports_tiled_processing()

    def test_fbcnn_preprocess(self, sample_image_file):
        """Test FBCNN preprocessing."""
        model, _ = create_model("fbcnn_color")
        img = Image.open(sample_image_file)
        tensor = model.preprocess(img)
        assert tensor.ndim == 4
        assert tensor.shape[0] == 1
        assert tensor.shape[1] == 3
        assert tensor.dtype == np.float32

    def test_fbcnn_convert(self, sample_image_file):
        """Test FBCNN conversion."""
        model, _ = create_model("fbcnn_color")
        img = Image.open(sample_image_file)
        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.size == img.size


class TestWaifu2xModel:
    """Test waifu2x model."""

    def test_waifu2x_supports_tiled(self):
        """Test waifu2x supports tiled processing."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0")
        assert model.supports_tiled_processing()

    def test_waifu2x_preprocess(self, sample_image_file):
        """Test waifu2x preprocessing."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0")
        img = Image.open(sample_image_file)
        tensor = model.preprocess(img)
        assert tensor.ndim == 3
        assert tensor.shape[0] == 3

    def test_waifu2x_convert(self, sample_image_file):
        """Test waifu2x conversion."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0")
        img = Image.open(sample_image_file)
        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.size == img.size

    def test_waifu2x_cunet_convert(self, sample_image_file):
        """Test waifu2x Cunet conversion."""
        model, _ = create_model("waifu2x_cunet_art:noise0")
        img = Image.open(sample_image_file)
        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.size == img.size

    def test_waifu2x_scale2x(self, sample_image_file):
        """Test waifu2x with 2x scale produces larger output."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0:scale2x")
        img = Image.open(sample_image_file)
        original_w, original_h = img.size
        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.width == original_w * 2
        assert result.height == original_h * 2


class TestDejpegBatch:
    """Test batch conversion functions."""

    def test_batch_convert_fbcnn(self, sample_folder, tmp_path):
        """Test batch conversion with FBCNN."""
        from bdlib.converters.dejpeg import batch_convert

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        image_files = sorted(sample_folder.glob("*.jpg"))[:2]
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        for i, src in enumerate(image_files, start=1):
            dst = input_dir / f"page{i:02d}.jpg"
            dst.write_bytes(src.read_bytes())

        result = batch_convert(input_dir=input_dir, output_dir=output_dir, max_threads=1, model_string="fbcnn_color")

        assert result.success
        assert result.stats["processed_pages"] == 2
        assert result.stats["failed_pages"] == 0
        for i in range(1, 3):
            assert (output_dir / f"page{i:02d}.png").exists()

    def test_batch_convert_empty_dir(self, tmp_path):
        """Test batch conversion with empty directory."""
        from bdlib.converters.dejpeg import batch_convert

        input_dir = tmp_path / "empty"
        input_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = batch_convert(input_dir=input_dir, output_dir=output_dir, model_string="fbcnn_color")

        assert not result.success


class TestModelJxlOutput:
    """Test that all models produce valid output for JXL conversion."""

    @pytest.fixture
    def sample_img(self, sample_image_file):
        """Load sample image once."""
        return Image.open(sample_image_file)

    @pytest.mark.parametrize("model_string", ["fbcnn_color"])
    def test_fbcnn_jxl_output(self, sample_img, model_string, tmp_path):
        """Test FBCNN model produces valid JXL-convertible output."""
        import pylibjxl

        model, _ = create_model(model_string)
        result = model.convert(sample_img)

        jxl_data = pil_image_to_jxl_array(result)
        assert jxl_data.shape == (*reversed(sample_img.size), 3)
        assert jxl_data.dtype == np.uint8

        output_file = tmp_path / "output.jxl"
        jxl_bytes = pylibjxl.encode(jxl_data, effort=7, distance=1.0)
        output_file.write_bytes(jxl_bytes)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    @pytest.mark.parametrize(
        "model_string",
        ["waifu2x_cunet_art:noise0", "waifu2x_swin_unet_art:noise0", "waifu2x_swin_unet_art_scan:noise0"],
    )
    def test_waifu2x_jxl_output(self, sample_img, model_string, tmp_path):
        """Test waifu2x models produce valid JXL-convertible output."""
        import pylibjxl

        model, _ = create_model(model_string)
        result = model.convert(sample_img)

        jxl_data = pil_image_to_jxl_array(result)
        assert jxl_data.dtype == np.uint8
        assert jxl_data.shape[2] == 3

        output_file = tmp_path / f"output_{model_string.replace(':', '_').replace('-', '_')}.jxl"
        jxl_bytes = pylibjxl.encode(jxl_data, effort=7, distance=1.0)
        output_file.write_bytes(jxl_bytes)

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    @pytest.mark.parametrize("model_string", ["waifu2x_swin_unet_art:noise0:scale2x"])
    def test_waifu2x_scale2x_jxl_output(self, sample_img, model_string, tmp_path):
        """Test waifu2x with scale2x produces valid JXL output."""
        import pylibjxl

        model, _ = create_model(model_string)
        result = model.convert(sample_img)

        assert result.width == sample_img.width * 2
        assert result.height == sample_img.height * 2

        jxl_data = pil_image_to_jxl_array(result)
        assert jxl_data.dtype == np.uint8
        assert jxl_data.shape[2] == 3

        output_file = tmp_path / "output_scale2x.jxl"
        jxl_bytes = pylibjxl.encode(jxl_data, effort=7, distance=1.0)
        output_file.write_bytes(jxl_bytes)

        assert output_file.exists()
        assert output_file.stat().st_size > 0
