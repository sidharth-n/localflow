"""Moonshine ONNX STT backend.

Wraps the `useful-moonshine-onnx` package. CPU-only for M0.4; CUDA EP lands in M1.
Published package (v20251121) ships `moonshine/tiny` and `moonshine/base` only —
`small`/`medium` are planned per upstream but not yet available in this wheel.
"""
from __future__ import annotations

import logging
import time

import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
MIN_SECS = 0.1   # moonshine rejects clips shorter than this
MAX_SECS = 64.0  # moonshine rejects clips longer than this


class MoonshineSTT:
    def __init__(self, model: str = "moonshine/base") -> None:
        from moonshine_onnx import MoonshineOnnxModel, load_tokenizer

        t0 = time.monotonic()
        self._model = MoonshineOnnxModel(model_name=model)
        self._tokenizer = load_tokenizer()
        log.info("moonshine %s loaded in %.2f s", model, time.monotonic() - t0)

    def transcribe(self, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
        if sample_rate != SAMPLE_RATE:
            raise ValueError(
                f"moonshine expects {SAMPLE_RATE} Hz audio, got {sample_rate}"
            )
        if audio.size == 0:
            return ""

        secs = audio.size / SAMPLE_RATE
        if secs < MIN_SECS:
            log.info("skipping transcription: %.2f s clip below %.1f s minimum", secs, MIN_SECS)
            return ""
        if secs > MAX_SECS:
            log.warning("clip %.1f s exceeds %.0f s max, truncating", secs, MAX_SECS)
            audio = audio[: int(MAX_SECS * SAMPLE_RATE)]

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32) / 32768.0
        tokens = self._model.generate(audio[None, :])
        return self._tokenizer.decode_batch(tokens)[0].strip()
