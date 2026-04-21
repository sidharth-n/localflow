"""Stub STT. Returns a canned transcript so the full pipeline can be exercised
before real ML lands in M0.4."""
from __future__ import annotations

import numpy as np


class DummySTT:
    def __init__(self, text: str = "this is a test transcript from the dummy stt") -> None:
        self.text = text

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:  # noqa: ARG002
        return self.text
