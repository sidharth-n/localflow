#!/usr/bin/env python3
"""Fetch model weights referenced in config/default.yaml to ~/.localflow/models/.

Moonshine STT weights are pulled automatically on first use by the ONNX runtime
cache; this script only handles the polish LLM (too big to be worth fetching
on every cold start).
"""
from __future__ import annotations

import os
import sys

from huggingface_hub import hf_hub_download

TARGET = os.path.expanduser("~/.localflow/models")

MODELS: list[dict[str, str]] = [
    {
        "purpose": "polish LLM (Qwen3-4B-Instruct-2507 Q4_K_M, ~2.4 GB)",
        "repo_id": "unsloth/Qwen3-4B-Instruct-2507-GGUF",
        "filename": "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    },
]


def main() -> int:
    os.makedirs(TARGET, exist_ok=True)
    for m in MODELS:
        target_path = os.path.join(TARGET, m["filename"])
        if os.path.exists(target_path):
            size_mb = os.path.getsize(target_path) / 1024 / 1024
            print(f"==> already present: {m['filename']} ({size_mb:.0f} MB) — skipping")
            continue
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
