#!/usr/bin/env python3
"""
JPEG artifact removal using FBCNN model.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime as ort
from PIL import Image

for lib_path in ["/usr/lib", "/usr/lib/x86_64-linux-gnu", "/opt/cuda/lib64"]:
    if os.path.exists(lib_path) and lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
        os.environ["LD_LIBRARY_PATH"] = lib_path + ":" + os.environ.get("LD_LIBRARY_PATH", "")

from bdlib.log import get_logger

logger = get_logger(__name__)

# FBCNN Color model URL
FBCNN_COLOR_URL = (
    "https://huggingface.co/colpona/dejpeg-models/resolve/main/fbcnn/fbcnn_color_fp16.onnx"
)

# Expected SHA256 for the FBCNN Color model (this should be verified)
# For now, we'll skip hash verification but note the expected size
MODEL_CACHE_DIR = Path.home() / ".cache" / "bdlib" / "models"
MODEL_FILENAME = "fbcnn_color_fp16.onnx"

_use_cuda = False


def _check_cuda_available() -> bool:
    """Check if CUDA is available for ONNX Runtime."""
    global _use_cuda
    try:
        available = "CUDAExecutionProvider" in ort.get_available_providers()
        if available:
            logger.info("CUDA is available for ONNX Runtime")
            _use_cuda = True
        else:
            logger.info("CUDA not available, using CPU")
            _use_cuda = False
        return available
    except Exception:
        _use_cuda = False
        return False


def _download_model() -> Path:
    """Download and cache the FBCNN model."""
    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_CACHE_DIR / MODEL_FILENAME

    if model_path.exists():
        logger.debug(f"Using cached model at {model_path}")
        return model_path

    logger.info(f"Downloading FBCNN model from {FBCNN_COLOR_URL}")
    try:
        import urllib.request

        # Download with progress indication
        def download_progress(count, block_size, total_size):
            if total_size > 0:
                percent = min(100.0 * count * block_size / total_size, 100.0)
                if count % 100 == 0:  # Log every 100 blocks
                    logger.debug(f"Download progress: {percent:.1f}%")

        urllib.request.urlretrieve(FBCNN_COLOR_URL, model_path, download_progress)
        logger.info(f"Model downloaded to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        if model_path.exists():
            model_path.unlink()  # Remove partial download
        raise


def _get_ort_session(model_path: Path) -> ort.InferenceSession:
    """Create ONNX Runtime inference session."""
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    if _check_cuda_available():
        sess_options.intra_op_num_threads = 1
        sess_options.inter_op_num_threads = 1
        providers = [
            ("CUDAExecutionProvider", {"device_id": 0, "cudnn_conv_algo_search": "EXHAUSTIVE"})
        ]
        providers.append("CPUExecutionProvider")
    else:
        sess_options.intra_op_num_threads = 20
        sess_options.inter_op_num_threads = 20
        providers = ["CPUExecutionProvider"]

    try:
        session = ort.InferenceSession(str(model_path), sess_options, providers=providers)
        input_names = [inp.name for inp in session.get_inputs()]
        output_names = [out.name for out in session.get_outputs()]
        logger.debug(f"Model inputs: {input_names}")
        logger.debug(f"Model outputs: {output_names}")
        logger.debug(f"Using providers: {session.get_providers()}")
        logger.debug("ONNX Runtime session created successfully")
        return session
    except Exception as e:
        logger.error(f"Failed to create ONNX Runtime session: {e}")
        raise


def _preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess PIL Image for FBCNN model input."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    img_array = np.array(image, dtype=np.float32) / 255.0

    img_array = np.transpose(img_array, (2, 0, 1))
    img_array = np.expand_dims(img_array, axis=0)

    return img_array


def _get_model_io_names(session: ort.InferenceSession) -> tuple:
    """Get input and output names from ONNX session."""
    input_names = [inp.name for inp in session.get_inputs()]
    output_names = [out.name for out in session.get_outputs()]

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

    image_output = output_names[0] if output_names else "output"

    return image_input, qf_input, image_output


def _postprocess_image(output_array: np.ndarray) -> Image.Image:
    """Postprocess model output to PIL Image."""
    # Remove batch dimension: NCHW -> CHW
    output_array = np.squeeze(output_array, axis=0)

    # Clip to [0, 1] and convert to [0, 255]
    output_array = np.clip(output_array, 0.0, 1.0)
    output_array = (output_array * 255.0).astype(np.uint8)

    # Convert from CHW to HWC format for PIL
    output_array = np.transpose(output_array, (1, 2, 0))  # CHW to HWC

    # Convert to PIL Image
    image = Image.fromarray(output_array, mode="RGB")
    return image


def convert_jpeg(
    input_path: Path, output_path: Path, model_session: Optional[ort.InferenceSession] = None
) -> bool:
    """
    Remove JPEG artifacts from a single image using FBCNN model.

    Args:
        input_path: Path to input JPEG image
        output_path: Path to save processed image
        model_session: Optional pre-loaded ONNX session

    Returns:
        True if successful, False otherwise
    """
    # Load model session if not provided
    session_to_use = model_session
    if session_to_use is None:
        model_path = _download_model()
        session_to_use = _get_ort_session(model_path)

    # Assert that we have a valid session (helps with type checking)
    assert session_to_use is not None

    try:
        with Image.open(input_path) as img:
            if img.mode != "RGB":
                logger.debug(f"Converting {input_path} from {img.mode} to RGB for processing")
                img_for_processing = img.convert("RGB")
            else:
                img_for_processing = img

            input_tensor = _preprocess_image(img_for_processing)

        input_name, qf_input_name, output_name = _get_model_io_names(session_to_use)

        logger.debug(f"Model inputs: '{input_name}', '{qf_input_name}' -> output: '{output_name}'")

        run_inputs = {input_name: input_tensor}

        if qf_input_name is not None:
            qf_input = np.array([[0.5]], dtype=np.float32)
            run_inputs[qf_input_name] = qf_input

        result = session_to_use.run([output_name], run_inputs)

        # Postprocess and save
        output_array = result[0]
        processed_img = _postprocess_image(output_array)

        # Save as PNG to avoid additional JPEG compression artifacts
        # TODO: Consider saving as lossless format or high-quality JPEG
        processed_img.save(output_path, format="PNG", compress_level=6)

        logger.debug(f"Processed {input_path.name} -> {output_path.name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        return False


def process_file(
    jpeg_file: Path, output_dir: Path, model_session: Optional[ort.InferenceSession] = None
) -> bool:
    """
    Process a single JPEG file for dejpeg conversion.

    Args:
        jpeg_file: Path to input JPEG file
        output_dir: Directory to save processed file
        model_session: Optional pre-loaded ONNX session

    Returns:
        True if successful, False otherwise
    """
    # Save as PNG to avoid double JPEG compression
    output_file = output_dir / (jpeg_file.stem + ".png")

    if convert_jpeg(jpeg_file, output_file, model_session):
        logger.info(f"DeJPEG processed {jpeg_file.name} -> {output_file.name} ... OK")
        return True
    else:
        logger.error(f"DeJPEG processed {jpeg_file.name} -> {output_file.name} ... FAILED")
        return False


def batch_convert(
    input_dir: Path,
    output_dir: Path,
    max_threads: int = 4,
):
    """
    Convert all JPEG images in a directory using FBCNN model with multiple threads.

    Args:
        input_dir: Path to input directory
        output_dir: Path to output directory
        max_threads: Maximum number of threads to use
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find JPEG files
    jpeg_extensions = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]
    jpeg_files = [file for ext in jpeg_extensions for file in input_dir.glob(ext)]

    if not jpeg_files:
        logger.warning(f"No JPEG files found in {input_dir}")
        return

    logger.info(
        f"Found {len(jpeg_files)} JPEG files to process with FBCNN (using up to {max_threads} threads)"
    )

    # Load model once for all threads
    try:
        model_path = _download_model()
        model_session = _get_ort_session(model_path)
        logger.debug("FBCNN model loaded successfully for batch processing")
    except Exception as e:
        logger.error(f"Failed to load FBCNN model: {e}")
        return

    # Process files
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_file, jpeg_file, output_dir, model_session): jpeg_file
            for jpeg_file in jpeg_files
        }

        # Process results as they complete
        for future in as_completed(future_to_file):
            jpeg_file = future_to_file[future]
            try:
                future.result()  # This will raise any exceptions that occurred
            except Exception as e:
                logger.error(f"Error processing {jpeg_file.name}: {e}")

    logger.info("DeJPEG batch processing completed")
