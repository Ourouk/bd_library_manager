#!/usr/bin/env python3
"""
FBCNN JPEG artifact removal model.
"""

from __future__ import annotations

import os

os.environ["ORT_LOGGING_LEVEL"] = "3"

from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

for lib_path in ["/usr/lib", "/usr/lib/x86_64-linux-gnu", "/opt/cuda/lib64"]:
    if os.path.exists(lib_path) and lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
        os.environ["LD_LIBRARY_PATH"] = lib_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")

from bdlib.log import get_logger  # noqa: E402

logger = get_logger(__name__)

MODEL_CACHE_DIR = Path.home() / ".cache" / "bdlib" / "models"

FBCNN_COLOR_URL = "https://huggingface.co/colpona/dejpeg-models/resolve/main/fbcnn/fbcnn_color_fp16.onnx"


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


def _download_model() -> Path:
    """Download and cache the FBCNN model."""
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_CACHE_DIR / "fbcnn_color_fp16.onnx"

    if model_path.exists():
        logger.debug(f"Using cached model at {model_path}")
        return model_path

    logger.info(f"Downloading FBCNN model from {FBCNN_COLOR_URL}")
    try:
        import urllib.request

        def download_progress(count: int, block_size: int, total_size: int) -> None:
            if total_size > 0:
                percent = min(100.0 * count * block_size / total_size, 100.0)
                if count % 100 == 0:
                    logger.debug(f"Download progress: {percent:.1f}%")

        urllib.request.urlretrieve(FBCNN_COLOR_URL, model_path, download_progress)
        logger.info(f"Model downloaded to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        if model_path.exists():
            model_path.unlink()
        raise


class FBCNNModel:
    """FBCNN JPEG artifact removal model."""

    NAME = "fbcnn_color"

    def __init__(self, session: ort.InferenceSession | None = None):
        self._session = session

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def session(self) -> ort.InferenceSession:
        if self._session is None:
            self._session = _get_ort_session(_download_model())
        return self._session

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """Preprocess PIL Image for FBCNN model input."""
        if image.mode != "RGB":
            image = image.convert("RGB")

        img_array = np.array(image, dtype=np.float32) / 255.0
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def run(self, input_tensor: np.ndarray, qf: float = 0.5) -> np.ndarray:
        """Run inference on input tensor."""
        input_names = [inp.name for inp in self.session.get_inputs()]
        output_names = [out.name for out in self.session.get_outputs()]

        image_input = None
        qf_input = None

        for name in input_names:
            if "image" in name.lower() or name.lower() in ("input", "x"):
                image_input = name
            elif "qf" in name.lower() or "quality" in name.lower():
                qf_input = name

        if image_input is None and input_names:
            image_input = input_names[0]
        if qf_input is None and len(input_names) > 1:
            qf_input = input_names[1]

        run_inputs = {image_input: input_tensor}
        if qf_input is not None:
            run_inputs[qf_input] = np.array([[qf]], dtype=np.float32)

        result = self.session.run([output_names[0]], run_inputs)
        return np.asarray(result[0])

    def postprocess(self, output_array: np.ndarray) -> Image.Image:
        """Postprocess model output to PIL Image."""
        output_array = np.squeeze(output_array, axis=0)
        output_array = np.clip(output_array, 0.0, 1.0)
        output_array = (output_array * 255.0).astype(np.uint8)
        output_array = np.transpose(output_array, (1, 2, 0))
        return Image.fromarray(output_array, mode="RGB")

    def supports_tiled_processing(self) -> bool:
        return False

    def convert(self, image: Image.Image) -> Image.Image:
        """Convert an image using FBCNN."""
        input_tensor = self.preprocess(image)
        output_array = self.run(input_tensor)
        return self.postprocess(output_array)


def create() -> FBCNNModel:
    """Create an FBCNN model instance."""
    return FBCNNModel()
