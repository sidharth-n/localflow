"""Polish LLM via llama.cpp.

Cleans up raw STT: fills punctuation, fixes misheard terms from context,
strips filler words. Default model: Qwen3-4B-Instruct-2507 Q4_K_M.
CUDA-capable when llama-cpp-python's CUDA wheel is installed.
"""
from __future__ import annotations

import ctypes
import logging
import os
import site
import time

log = logging.getLogger(__name__)


def _preload_cuda_runtime() -> None:
    """Pre-load NVIDIA CUDA runtime .so files from the pip-installed wheels.

    llama-cpp-python's CUDA build wants libcudart.so.12 / libcublas.so.12 at
    import time; the NVIDIA pip wheels (nvidia-cuda-runtime-cu12 etc.) ship
    these but don't register them with the system linker. We dlopen them
    explicitly into the global namespace before llama_cpp imports so its
    own CDLL call resolves them.
    """
    candidates = [
        ("nvidia/cuda_runtime/lib", "libcudart.so.12"),
        ("nvidia/cublas/lib", "libcublas.so.12"),
        ("nvidia/cublas/lib", "libcublasLt.so.12"),
        ("nvidia/cuda_nvrtc/lib", "libnvrtc.so.12"),
    ]
    for sp in site.getsitepackages():
        for rel, name in candidates:
            p = os.path.join(sp, rel, name)
            if os.path.exists(p):
                try:
                    ctypes.CDLL(p, mode=ctypes.RTLD_GLOBAL)
                except OSError as e:
                    log.debug("skip preload %s: %s", p, e)


_preload_cuda_runtime()


class QwenPolish:
    def __init__(
        self,
        model_path: str,
        system_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        n_ctx: int = 4096,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
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
            n_gpu_layers=n_gpu_layers,
            flash_attn=n_gpu_layers != 0,
            verbose=False,
        )
        log.info(
            "polish model loaded in %.2f s: %s (gpu_layers=%d)",
            time.monotonic() - t0,
            os.path.basename(model_path),
            n_gpu_layers,
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
