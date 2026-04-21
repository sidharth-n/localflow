#!/usr/bin/env python3
"""Fetch model weights referenced in config/default.yaml to ~/.localflow/models/.

Moonshine STT weights are pulled automatically on first use by `moonshine_onnx`;
this script only handles weights big enough to be worth pre-fetching.
"""
from __future__ import annotations

import os
import sys

from huggingface_hub import hf_hub_download

TARGET = os.path.expanduser("~/.localflow/models")

MODELS: list[dict[str, str]] = [
    {
        "purpose": "polish LLM (primary, fast)",
        "repo_id": "LiquidAI/LFM2.5-1.2B-Instruct-GGUF",
        "filename": "LFM2.5-1.2B-Instruct-Q4_K_M.gguf",
    },
    {
        "purpose": "polish LLM (fallback, higher quality)",
        "repo_id": "unsloth/Qwen3-4B-Instruct-2507-GGUF",
        "filename": "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    },
]


def main() -> int:
    os.makedirs(TARGET, exist_ok=True)
    for m in MODELS:
        print(f"==> {m['purpose']}: {m['repo_id']} / {m['filename']}")
        path = hf_hub_download(
            repo_id=m["repo_id"],
            filename=m["filename"],
            local_dir=TARGET,
        )
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"    -> {path} ({size_mb:.0f} MB)")
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
