# localflow

Fully-local, cross-platform (Linux + macOS) AI voice dictation. Press a hotkey, speak, and polished text appears at your cursor. An open-source local clone of Wispr Flow — no cloud calls, no subscription, no telemetry.

**Status:** 🚧 Pre-alpha. M0 scaffold only. See [`SESSION.md`](./SESSION.md) for current progress.

## Why

Wispr Flow is great, but it sends your voice to the cloud and costs money. With April-2026 models, the same UX is achievable on modest local hardware:

- **Moonshine v2** gives sub-300 ms streaming STT, Apache 2.0.
- **Gemma 4 E4B** / **Qwen 3-4B** polish transcripts (fix disfluencies, format) in ~200-400 ms locally.
- Total end-of-speech → typed-text latency: ~500 ms on both an RTX 3050 laptop and an M5 MacBook Air.

## Targets

| | Linux | macOS |
|---|---|---|
| Minimum | x86_64, 8 GB RAM, any recent CPU (CPU-only fallback) | Apple Silicon (M1+), 16 GB unified |
| Recommended | NVIDIA GPU ≥ 4 GB VRAM, 16 GB RAM, X11 session | M2+, 16 GB+ unified |
| Display server | X11 (Wayland support planned via `ydotool`) | native AXUIElement |

## Planned stack

- **Audio capture** — `sounddevice` (16 kHz mono)
- **VAD** — Silero VAD (ONNX)
- **STT** — Moonshine v2 (ONNX + CUDA EP on Linux / CoreML or MLX on Mac)
- **Polish LLM** — `llama.cpp` on Linux / `mlx-lm` on Mac; Qwen 3-4B or Gemma 4 E4B
- **Text injection** — clipboard + simulated paste (default), direct AX/xdotool (opt-in)
- **Hotkey** — `pynput` (cross-platform)

Architecture details: [`knowledge-base/architecture.md`](./knowledge-base/architecture.md)
Model reasoning: [`knowledge-base/model-choices.md`](./knowledge-base/model-choices.md)

## Quickstart (Linux, pre-alpha)

```bash
git clone git@github.com:sidharth-n/localflow.git
cd localflow
./setup.sh            # creates venv, installs deps, downloads models
source .venv/bin/activate
localflow             # start the daemon; press Right-Ctrl to dictate
```

macOS support coming after M1. Model auto-download coming after M2.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
