#!/usr/bin/env python3
"""
waifu2x model for artifact removal and upscaling.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from PIL import Image

for lib_path in ["/usr/lib", "/usr/lib/x86_64-linux-gnu", "/opt/cuda/lib64"]:
    if os.path.exists(lib_path) and lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
        os.environ["LD_LIBRARY_PATH"] = lib_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")

os.environ["CUDA_MODULE_LOADING"] = "LAZY"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["ONNXIFI_DBG_MASK"] = "0"

from bdlib.log import get_logger  # noqa: E402

from .tiled import (  # noqa: E402
    calculate_tiling_config,
    float_array_to_pil,
    pil_to_float_array,
    tiled_process,
)

logger = get_logger(__name__)

MODEL_CACHE_DIR = Path.home() / ".cache" / "bdlib" / "models"

WAIFU2X_BASE_URL = "https://huggingface.co/deepghs/waifu2x_onnx/resolve/main/20241017/onnx_models"


@dataclass
class Waifu2xArchParams:
    """Architecture-specific parameters."""

    tile_size: int
    offset: int
    blend_size: int


WAIFU2X_ARCH_PARAMS = {
    "cunet": Waifu2xArchParams(tile_size=256, offset=14, blend_size=14),
    "swin_unet": Waifu2xArchParams(tile_size=256, offset=22, blend_size=14),
}


@dataclass
class Waifu2xConfig:
    """Configuration for waifu2x model."""

    arch: str
    model_type: str
    noise_level: int = 0
    scale_factor: int = 1


AVAILABLE_MODELS = [
    "waifu2x_cunet_art",
    "waifu2x_cunet_photo",
    "waifu2x_swin_unet_art",
    "waifu2x_swin_unet_art_scan",
    "waifu2x_swin_unet_photo",
]


def parse_model_string(model_string: str) -> Waifu2xConfig:
    """
    Parse model string with optional embedded parameters.

    Examples:
        "waifu2x_cunet_art" -> Waifu2xConfig(arch="cunet", model_type="art")
        "waifu2x_swin_unet_art:noise2" -> Waifu2xConfig(arch="swin_unet", model_type="art", noise_level=2)
        "waifu2x_swin_unet_art:noise2:scale2x" -> Waifu2xConfig(arch="swin_unet", model_type="art", noise_level=2, scale_factor=2)
    """
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

    if not model_name.startswith("waifu2x_"):
        raise ValueError(f"Invalid waifu2x model name: {model_name}")

    model_part = model_name.replace("waifu2x_", "")

    known_architectures = ["cunet", "swin_unet"]
    arch = None
    type_part = None

    for known_arch in known_architectures:
        if model_part.startswith(known_arch + "_"):
            arch = known_arch
            type_part = model_part[len(known_arch) + 1 :]
            break

    if arch is None or type_part is None:
        parts_split = model_part.split("_", 1)
        arch = parts_split[0] if parts_split else "swin_unet"
        type_part = parts_split[1] if len(parts_split) > 1 else "art"

    return Waifu2xConfig(arch=arch, model_type=type_part, noise_level=noise_level, scale_factor=scale_factor)


def _check_cuda_available() -> bool:
    """Check if CUDA is available for ONNX Runtime."""
    try:
        available = "CUDAExecutionProvider" in ort.get_available_providers()
        if available:
            logger.info("CUDA is available for ONNX Runtime")
        else:
            logger.info("CUDA not available, using CPU")
        return available
    except Exception:
        return False


def _get_ort_session(model_path: Path) -> ort.InferenceSession:
    """Create ONNX Runtime inference session."""
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.log_severity_level = 3

    use_cuda = _check_cuda_available()

    if use_cuda:
        sess_options.intra_op_num_threads = 1
        sess_options.inter_op_num_threads = 1
        providers: list = [("CUDAExecutionProvider", {"device_id": 0, "cudnn_conv_algo_search": "EXHAUSTIVE"})]
        providers.append("CPUExecutionProvider")
    else:
        sess_options.intra_op_num_threads = 20
        sess_options.inter_op_num_threads = 20
        providers = ["CPUExecutionProvider"]

    try:
        session = ort.InferenceSession(str(model_path), sess_options, providers=providers)
        logger.debug(f"Model inputs: {[inp.name for inp in session.get_inputs()]}")
        logger.debug(f"Model outputs: {[out.name for out in session.get_outputs()]}")
        logger.debug(f"Using providers: {session.get_providers()}")
        return session
    except Exception as e:
        logger.error(f"Failed to create ONNX Runtime session: {e}")
        raise


class Waifu2xModel:
    """waifu2x ONNX model with tiled processing support."""

    def __init__(
        self,
        arch: str = "swin_unet",
        model_type: str = "art",
        noise_level: int = 0,
        scale_factor: int = 1,
        session: Optional[ort.InferenceSession] = None,
    ):
        self.config = Waifu2xConfig(
            arch=arch, model_type=model_type, noise_level=noise_level, scale_factor=scale_factor
        )

        params = WAIFU2X_ARCH_PARAMS.get(arch, WAIFU2X_ARCH_PARAMS["swin_unet"])
        self.tile_size = params.tile_size
        self.offset = params.offset
        self.blend_size = params.blend_size

        self._session = session
        self._model_filename: Optional[str] = None

    @property
    def name(self) -> str:
        return f"waifu2x_{self.config.arch}_{self.config.model_type}"

    @property
    def model_filename(self) -> str:
        if self._model_filename is None:
            self._model_filename = (
                f"{self.config.arch}_{self.config.model_type}"
                f"_n{self.config.noise_level}_s{self.config.scale_factor}.onnx"
            )
        return self._model_filename

    @property
    def model_path(self) -> Path:
        return MODEL_CACHE_DIR / "waifu2x" / self.model_filename

    @property
    def session(self) -> ort.InferenceSession:
        if self._session is None:
            self._session = _get_ort_session(self._download_model())
        return self._session

    def _download_model(self) -> Path:
        """Download the waifu2x model."""
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        waifu2x_dir = MODEL_CACHE_DIR / "waifu2x"
        waifu2x_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.model_path

        if model_path.exists():
            logger.debug(f"Using cached waifu2x model: {model_path}")
            return model_path

        model_url = f"{WAIFU2X_BASE_URL}/{self.config.arch}/{self.config.model_type}/noise{self.config.noise_level}"
        if self.config.scale_factor > 1:
            model_url += f"_scale{self.config.scale_factor}x"
        model_url += ".onnx"

        logger.info(f"Downloading waifu2x model: {model_url}")
        try:
            import urllib.request

            def download_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = min(100.0 * count * block_size / total_size, 100.0)
                    if count % 100 == 0:
                        logger.debug(f"Download progress: {percent:.1f}%")

            urllib.request.urlretrieve(model_url, model_path, download_progress)
            logger.info(f"Model downloaded to {model_path}")
            return model_path
        except Exception as e:
            logger.error(f"Failed to download waifu2x model: {e}")
            if model_path.exists():
                model_path.unlink()
            raise

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """Preprocess PIL Image for waifu2x model input."""
        return pil_to_float_array(image)

    def run(self, input_tensor: np.ndarray) -> np.ndarray:
        """Run inference on input tensor."""
        input_names = [inp.name for inp in self.session.get_inputs()]
        output_names = [out.name for out in self.session.get_outputs()]

        run_inputs = {input_names[0]: input_tensor}
        result = self.session.run([output_names[0]], run_inputs)
        return np.asarray(result[0])

    def postprocess(self, output_array: np.ndarray) -> Image.Image:
        """Postprocess model output to PIL Image."""
        return float_array_to_pil(np.squeeze(output_array, axis=0))

    def supports_tiled_processing(self) -> bool:
        return True

    def _process_tile(self, tile: np.ndarray) -> np.ndarray:
        """Process a single tile."""
        if tile.ndim == 3:
            tile = np.expand_dims(tile, axis=0)
        output = self.run(tile)
        return np.asarray(output)

    def _tiled_convert(self, image: Image.Image) -> Image.Image:
        """Convert an image using tiled processing with seam blending."""
        img_array = pil_to_float_array(image)
        original_h, original_w = img_array.shape[1], img_array.shape[2]

        tiled_config = calculate_tiling_config(
            image_shape=(original_h, original_w),
            tile_size=self.tile_size,
            offset=self.offset,
            blend_size=self.blend_size,
            scale=self.config.scale_factor,
        )

        def process_fn(tile):
            return self._process_tile(tile)

        result = tiled_process(img_array, process_fn, tiled_config)

        return float_array_to_pil(result)

    def convert(self, image: Image.Image) -> Image.Image:
        """Convert an image using tiled processing."""
        return self._tiled_convert(image)


def create(config: Waifu2xConfig | str) -> Waifu2xModel:
    """
    Create a waifu2x model instance.

    Args:
        config: Waifu2xConfig object or model string like "waifu2x_swin_unet_art:noise2:scale2x"

    Returns:
        Waifu2xModel instance
    """
    if isinstance(config, str):
        config = parse_model_string(config)

    return Waifu2xModel(
        arch=config.arch, model_type=config.model_type, noise_level=config.noise_level, scale_factor=config.scale_factor
    )
