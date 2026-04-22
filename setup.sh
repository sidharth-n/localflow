#!/usr/bin/env bash
# localflow one-shot installer for Linux and macOS.
#
# After this script finishes, the next thing you need to run is:
#   source .venv/bin/activate
#   localflow
#
# Re-running is safe — apt, pip, and the model downloader are all idempotent.

set -euo pipefail

cd "$(dirname "$0")"

OS="$(uname -s)"
PY="${PYTHON:-python3}"

echo "==> localflow setup"
echo "    OS: $OS"
echo "    Python: $($PY --version)"

# ---------- system packages ----------
if [ "$OS" = "Linux" ]; then
    APT_PKGS=()
    command -v xdotool >/dev/null 2>&1 || APT_PKGS+=(xdotool)
    command -v xclip    >/dev/null 2>&1 || APT_PKGS+=(xclip)
    command -v xprop    >/dev/null 2>&1 || APT_PKGS+=(x11-utils)
    dpkg -s libportaudio2 >/dev/null 2>&1 || APT_PKGS+=(libportaudio2)
    dpkg -s python3-tk    >/dev/null 2>&1 || APT_PKGS+=(python3-tk)
    dpkg -s python3-dev   >/dev/null 2>&1 || APT_PKGS+=(python3-dev)
    if [ ${#APT_PKGS[@]} -gt 0 ]; then
        echo "==> installing apt packages (needs sudo): ${APT_PKGS[*]}"
        sudo apt-get update -qq
        sudo apt-get install -y -qq "${APT_PKGS[@]}"
    fi
elif [ "$OS" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        brew list portaudio >/dev/null 2>&1 || brew install portaudio
    else
        echo "!!  Homebrew not found — install portaudio manually if sounddevice fails to import."
    fi
else
    echo "!! unsupported OS: $OS" >&2
    exit 1
fi

# ---------- venv ----------
if [ ! -d .venv ]; then
    echo "==> creating virtualenv at .venv"
    "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip wheel

# ---------- python deps ----------
case "$OS" in
    Linux)
        if command -v nvidia-smi >/dev/null 2>&1; then
            echo "==> NVIDIA GPU detected — installing GPU stack"
            pip install --quiet -e ".[linux-gpu]"
            # Replace the PyPI CPU wheel of llama-cpp-python with the prebuilt
            # CUDA wheel (~100x less trouble than compiling from source).
            echo "==> installing CUDA-enabled llama-cpp-python (cu124 prebuilt wheel)"
            pip install --quiet --force-reinstall --no-deps \
                llama-cpp-python \
                --extra-index-url=https://abetlen.github.io/llama-cpp-python/whl/cu124/
            echo "==> installing NVIDIA runtime wheels (for llama-cpp-python CUDA calls)"
            pip install --quiet nvidia-cuda-runtime-cu12 nvidia-cublas-cu12
        else
            echo "==> no NVIDIA GPU detected — installing CPU-only stack"
            pip install --quiet -e ".[linux-cpu]"
        fi
        # Rounded overlay shape (python-xlib, pure Python).
        pip install --quiet python-xlib
        ;;
    Darwin)
        pip install --quiet -e ".[mac]"
        ;;
esac

# ---------- model weights ----------
echo "==> fetching model weights to ~/.localflow/models (~2.5 GB — one-time)"
python scripts/download_models.py

echo
echo "==> done. Run:"
echo "    source .venv/bin/activate"
echo "    localflow"
echo
echo "    Hold Right-Alt to dictate. A small waveform pill appears at the"
echo "    bottom of your screen while recording. Ctrl-C in the terminal to quit."
