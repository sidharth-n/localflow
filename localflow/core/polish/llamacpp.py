"""Polish LLM via llama.cpp.

Cleans up raw STT: fills punctuation, fixes misheard terms from context,
strips filler words. Runs on CPU. Default model: Qwen3-4B-Instruct-2507 Q4_K_M.
"""
from __future__ import annotations

import logging
import os
import time

log = logging.getLogger(__name__)


class QwenPolish:
    def __init__(
        self,
        model_path: str,
        system_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        n_ctx: int = 4096,
        n_threads: int | None = None,
    ) -> None:
        from llama_cpp import Llama

        model_path = os.path.expanduser(model_path)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"polish model not found: {model_path} — "
                "run `python scripts/download_models.py` to fetch"
            )
        self._system = system_prompt
        self._max_tokens = max_tokens
        self._temperature = temperature

        t0 = time.monotonic()
        self._llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )
        log.info(
            "polish model loaded in %.2f s: %s",
            time.monotonic() - t0,
            os.path.basename(model_path),
        )

    def polish(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        resp = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self._system},
                {"role": "user", "content": text},
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        out = resp["choices"][0]["message"]["content"].strip()
        # Some models wrap the answer in quotes despite "no quotes" instruction.
        if len(out) >= 2 and out[0] == out[-1] and out[0] in "\"'":
            out = out[1:-1].strip()
        return out
