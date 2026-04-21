"""Tiny YAML config loader. Reads `config/default.yaml` from the repo root.

User overrides (`~/.config/localflow/config.yaml`) are planned for M4.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _REPO_ROOT / "config" / "default.yaml"


def load() -> dict[str, Any]:
    with _DEFAULT_PATH.open() as f:
        return yaml.safe_load(f)
