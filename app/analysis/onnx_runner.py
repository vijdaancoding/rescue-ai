"""
ONNX inference for spam detection.
Model: XLM-RoBERTa (binary sequence classification)
Labels: 0 → not_spam, 1 → spam

Loaded once at FastAPI startup via load() to avoid per-call cold start.
Inference runs in a ThreadPoolExecutor so CPU work never blocks the event loop.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "onnx_model"
LABELS = {0: "not_spam", 1: "spam"}

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="onnx-spam")
_session: ort.InferenceSession | None = None
_tokenizer = None
_input_names: set[str] = set()


def load() -> None:
    """Load model and tokenizer into memory. Call once at application startup.
    If the model files are not present (e.g. volume not yet populated), logs a
    warning and continues — analysis will skip the ONNX step until the model
    is available and the service is restarted."""
    global _session, _tokenizer, _input_names
    model_file = MODEL_DIR / "model.onnx"
    if not model_file.exists():
        logger.warning(
            "ONNX model not found at %s — spam detection disabled. "
            "Upload the model to the Railway volume and redeploy.",
            MODEL_DIR,
        )
        return
    logger.info("Loading ONNX spam detection model from %s", MODEL_DIR)
    _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    _session = ort.InferenceSession(
        str(MODEL_DIR / "model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    _input_names = {inp.name for inp in _session.get_inputs()}
    logger.info("ONNX model loaded. Inputs: %s", _input_names)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


def _infer(text: str) -> dict:
    """Blocking inference — run inside ThreadPoolExecutor."""
    enc = _tokenizer(
        text,
        return_tensors="np",
        truncation=True,
        max_length=512,
        padding="max_length",
    )
    feed = {k: v for k, v in enc.items() if k in _input_names}
    logits = _session.run(None, feed)[0][0]  # shape: (2,)
    probs = _softmax(logits)
    label_id = int(np.argmax(probs))
    return {
        "spam_label": LABELS[label_id],
        "spam_score": round(float(probs[1]), 4),  # probability of class 1 (spam)
    }


async def predict(text: str) -> dict:
    """Non-blocking async wrapper. Runs ONNX inference in thread pool."""
    if _session is None:
        raise RuntimeError("ONNX model not loaded. Call onnx_runner.load() at startup.")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _infer, text)
