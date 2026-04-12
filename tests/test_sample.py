"""Test DeJPEG models (slow - loads ML models)."""

from PIL import Image

from bdlib.converters.dejpeg import FBCNNModel, Waifu2xModel, batch_convert, create_model, get_available_models


class TestDejpegModels:
    """Test DeJPEG models with sample images."""

    def test_get_available_models(self):
        """Test that available models list is populated."""
        models = get_available_models()
        assert len(models) > 0
        assert "fbcnn_color" in models
        assert any("waifu2x" in m for m in models)

    def test_create_fbcnn_model(self):
        """Test creating FBCNN model."""
        model, config = create_model("fbcnn_color")
        assert isinstance(model, FBCNNModel)
        assert model.name == "fbcnn_color"
        assert not model.supports_tiled_processing()

    def test_create_waifu2x_model(self):
        """Test creating waifu2x model."""
        model, config = create_model("waifu2x_swin_unet_art:noise0")
        assert isinstance(model, Waifu2xModel)
        assert model.name == "waifu2x_swin_unet_art"
        assert model.supports_tiled_processing()

    def test_fbcnn_convert(self, sample_image_file, tmp_path):
        """Test FBCNN conversion on sample image."""
        model, _ = create_model("fbcnn_color")

        img = Image.open(sample_image_file)
        assert img.mode == "RGB"
        assert img.size[0] > 0 and img.size[1] > 0

        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.size == img.size

    def test_waifu2x_convert(self, sample_image_file):
        """Test waifu2x conversion on sample image."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0")

        img = Image.open(sample_image_file)
        assert img.mode == "RGB"

        result = model.convert(img)
        assert result.mode == "RGB"
        assert result.size == img.size

    def test_waifu2x_tiled_processing(self, sample_image_file):
        """Test that waifu2x uses tiled processing correctly."""
        model, _ = create_model("waifu2x_swin_unet_art:noise0")

        img = Image.open(sample_image_file)
        result = model.convert(img)

        assert result.size == img.size
        assert result.mode == "RGB"

    def test_model_preserves_dimensions(self, sample_image_file):
        """Test that both models preserve image dimensions."""
        img = Image.open(sample_image_file)
        original_size = img.size

        fbcnn_model, _ = create_model("fbcnn_color")
        fbcnn_result = fbcnn_model.convert(img)
        assert fbcnn_result.size == original_size

        del fbcnn_model

        waifu2x_model, _ = create_model("waifu2x_swin_unet_art:noise0")
        waifu2x_result = waifu2x_model.convert(img)
        assert waifu2x_result.size == original_size

    def test_batch_convert_waifu2x(self, sample_folder, tmp_path):
        """Test batch conversion with waifu2x model."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        image_files = sorted(sample_folder.glob("*.jpg"))[:2]
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        for i, src in enumerate(image_files, start=1):
            dst = input_dir / f"page{i:02d}.jpg"
            dst.write_bytes(src.read_bytes())

        result = batch_convert(
            input_dir=input_dir, output_dir=output_dir, max_threads=1, model_string="waifu2x_swin_unet_art:noise0"
        )

        assert result.success
        assert result.stats["processed_pages"] == 2
        assert result.stats["failed_pages"] == 0

        for i in range(1, 3):
            assert (output_dir / f"page{i:02d}.png").exists()
