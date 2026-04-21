#!/usr/bin/env bash
# localflow setup — one-shot installer for Linux and macOS.
# Stage-0 (current): venv + base deps.
# Stage-1 (after M0): auto-detect GPU, install platform extras, download models.

set -euo pipefail

cd "$(dirname "$0")"

OS="$(uname -s)"
PY="${PYTHON:-python3}"

echo "==> localflow setup"
echo "    OS: $OS"
echo "    Python: $($PY --version)"

# --- venv ---
if [ ! -d .venv ]; then
    echo "==> creating virtualenv at .venv"
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip

# --- platform-specific deps ---
case "$OS" in
    Linux)
        if command -v nvidia-smi >/dev/null 2>&1; then
            echo "==> NVIDIA GPU detected → installing linux-gpu extras"
            EXTRA="linux-gpu"
        else
            echo "==> no NVIDIA GPU → installing linux-cpu extras"
            EXTRA="linux-cpu"
        fi
        # X11 injection deps
        if ! command -v xdotool >/dev/null 2>&1; then
            echo "==> installing xdotool (needs sudo)"
            sudo apt-get update -qq
            sudo apt-get install -y -qq xdotool libportaudio2
        fi
        ;;
    Darwin)
        echo "==> macOS detected → installing mac extras"
        EXTRA="mac"
        if ! command -v brew >/dev/null 2>&1; then
            echo "    (skip) Homebrew not found — portaudio may already be available"
        else
            brew list portaudio >/dev/null 2>&1 || brew install portaudio
        fi
        ;;
    *)
        echo "Unsupported OS: $OS" >&2
        exit 1
        ;;
esac

echo "==> installing localflow (editable) with [$EXTRA]"
pip install --quiet -e ".[$EXTRA]"

echo
echo "==> done. Next:"
echo "    source .venv/bin/activate"
echo "    localflow  # once M0 is implemented"
echo
echo "    Model auto-download lands in M4. For now, models go under ~/.localflow/models/"
