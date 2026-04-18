"""
ONNX inference for spam detection.
Model: XLM-RoBERTa (binary sequence classification)
Labels: 0 → not_spam, 1 → spam

Model weights live at `behram7cr/spam_detection` on HuggingFace Hub (public).
On startup `load()` pulls the snapshot to the container's HF cache, then sets up
the ONNX Runtime session for fast local CPU inference — no per-request network
round-trip, no Railway volume needed. First cold start adds ~60–90s for the
~1.1 GB download; subsequent calls within the same container reuse the cache.

Inference runs in a ThreadPoolExecutor so CPU work never blocks the event loop.
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

# HF repo override via env if you ever fork or fine-tune a new version.
HF_REPO_ID = os.getenv("SPAM_MODEL_REPO", "behram7cr/spam_detection")
LABELS = {0: "not_spam", 1: "spam"}

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="onnx-spam")
_session: ort.InferenceSession | None = None
_tokenizer = None
_input_names: set[str] = set()


def load() -> None:
    """Pull the ONNX model + tokenizer from HuggingFace Hub and set up the
    ONNX Runtime session. Called once at FastAPI startup.

    If the download fails (network flake, HF outage, repo renamed) we log and
    continue — analysis will skip the ONNX step and return a safe default so
    the voice pipeline keeps working. Rejoin on next restart once the cause
    is resolved.
    """
    global _session, _tokenizer, _input_names
    logger.info("Downloading spam detection model from HuggingFace: %s", HF_REPO_ID)
    try:
        local_dir = snapshot_download(
            repo_id=HF_REPO_ID,
            # Only pull the files inference actually needs — skips README/license.
            allow_patterns=[
                "model.onnx",
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
            ],
        )
    except Exception as exc:
        logger.warning(
            "HF snapshot_download failed for %s: %s — spam detection disabled",
            HF_REPO_ID, exc,
        )
        return

    model_file = Path(local_dir) / "model.onnx"
    if not model_file.exists():
        logger.warning(
            "Download succeeded but model.onnx missing in %s — spam detection disabled",
            local_dir,
        )
        return

    logger.info("Loading ONNX session from %s", local_dir)
    _tokenizer = AutoTokenizer.from_pretrained(local_dir)
    _session = ort.InferenceSession(
        str(model_file),
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
