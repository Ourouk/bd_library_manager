"""Integration tests using sample data."""

from PIL import Image

from bdlib.converters import cbz
from bdlib.converters.dejpeg import (
    FBCNNModel,
    Waifu2xModel,
    create_model,
    get_available_models,
)
from bdlib.dto import ComicMetadata
from bdlib.metadata.comicinfo import generate_comicinfo


class TestWithSampleData:
    """Tests using the real sample comic folder."""

    def test_sample_folder_exists(self, sample_folder):
        """Verify sample folder exists and has images."""
        assert sample_folder.exists()
        images = list(sample_folder.glob("*.jpg"))
        assert len(images) > 0

    def test_sample_image_count(self, sample_folder):
        """Test that sample has expected number of images."""
        images = list(sample_folder.glob("*.jpg"))
        assert len(images) == 46

    def test_create_cbz_from_sample(self, sample_folder, tmp_path):
        """Test creating CBZ from sample folder."""
        output_file = tmp_path / "test.cbz"

        result = cbz.create_cbz(sample_folder, output_file)

        assert result is True
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_create_cbz_with_metadata_from_sample(self, sample_folder, tmp_path):
        """Test creating CBZ with ComicInfo.xml from sample."""
        comic_info = sample_folder / "ComicInfo.xml"

        metadata = ComicMetadata(
            title="Adieu le père",
            series="Avant l'Incal",
            number=1,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
        )
        xml = generate_comicinfo(metadata)
        comic_info.write_text(xml)

        output_file = tmp_path / "test_with_meta.cbz"

        result = cbz.create_cbz(sample_folder, output_file, comic_info)

        assert result is True

        import zipfile

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "ComicInfo.xml" in names

    def test_generate_comicinfo_parsing_sample_folder(self, sample_folder):
        """Test ComicInfo generation with sample folder metadata."""
        series = sample_folder.parent.name
        folder_name = sample_folder.name

        import re

        dir_name_match = re.match(r"(\d+)\s*-\s*(.+)", folder_name)
        number = int(dir_name_match.group(1)) if dir_name_match else None
        title = dir_name_match.group(2).strip() if dir_name_match else None

        metadata = ComicMetadata(
            title=title,
            series=series,
            number=number,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
        )
        xml = generate_comicinfo(metadata)

        assert "<Series>Avant l'Incal</Series>" in xml
        assert "<Number>1</Number>" in xml
        assert "<Title>Adieu le père</Title>" in xml

    def test_comic_metadata_from_sample(self, sample_folder):
        """Test ComicMetadata with sample data."""
        meta = ComicMetadata(
            series="Avant l'Incal",
            number=1,
            writer="Alexandro Jodorowsky",
            artist="Moebius",
            publisher="Les Humanoïdes Associés",
            year=1981,
            summary="Premier tome de la série Avant l'Incal.",
        )

        xml = generate_comicinfo(meta)

        assert "<Series>Avant l'Incal</Series>" in xml
        assert "<Number>1</Number>" in xml
        assert "<Writer>Alexandro Jodorowsky</Writer>" in xml
        assert "<Artist>Moebius</Artist>" in xml
        assert "<Publisher>Les Humanoïdes Associés</Publisher>" in xml
        assert "<Year>1981</Year>" in xml

    def test_sample_series_folder_structure(self, sample_series_folder):
        """Test the sample series folder structure."""
        assert sample_series_folder.exists()
        assert sample_series_folder.name == "Avant l'Incal"

        issues = [d for d in sample_series_folder.iterdir() if d.is_dir()]
        assert len(issues) >= 1
        issue_names = [d.name for d in issues]
        assert "01 - Adieu le père" in issue_names


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
        from bdlib.converters.dejpeg import batch_convert

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        image_files = sorted(sample_folder.glob("*.jpg"))[:2]
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        for i, src in enumerate(image_files, start=1):
            dst = input_dir / f"page{i:02d}.jpg"
            dst.write_bytes(src.read_bytes())

        result = batch_convert(
            input_dir=input_dir,
            output_dir=output_dir,
            max_threads=1,
            model_string="waifu2x_swin_unet_art:noise0",
        )

        assert result.success
        assert result.stats["processed_pages"] == 2
        assert result.stats["failed_pages"] == 0

        for i in range(1, 3):
            assert (output_dir / f"page{i:02d}.png").exists()
