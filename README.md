# localflow

**Fully-local, cross-platform AI voice dictation.** Hold a hotkey, speak, and polished text appears at your cursor — with no cloud calls, no telemetry, and no subscription.

An open-source clone of Wispr Flow, running entirely on-device. Typical end-to-end latency is **~460 ms** on a laptop NVIDIA RTX 3050.

## What it does

1. You hold **Right-Alt** — a small waveform pill appears at the bottom of your screen and reacts to your voice.
2. You speak.
3. You release the key — the pill flips to amber ("processing") while an LLM cleans up the transcript (removes "um"s, fixes homophones like *jason → JSON*, adds punctuation).
4. The polished text is pasted at your cursor via clipboard. The pill hides.

Everything — STT, LLM polish, text injection — runs on your machine.

## Status

| | |
|---|---|
| Linux end-to-end | ✅ working on X11 with RTX 3050 (4 GB VRAM) |
| macOS end-to-end | 🚧 planned (M3) |
| Wayland | 🚧 deferred — needs `ydotool` instead of `xdotool` |
| Dev stage | early-alpha, breaking changes possible |

See [`SESSION.md`](./SESSION.md) for the current working state.

## Latency, measured

On a Ryzen 9 5900HX + RTX 3050 laptop (4 GB VRAM), Ubuntu 22.04 X11:

| Stage | Time |
|---|---|
| Mic capture drain | ~10 ms |
| Moonshine STT (CPU) | ~100 ms |
| Dictionary pre-polish | ~1 ms |
| Qwen3-4B polish (GPU) | ~305 ms (0 ms if skip-gate fires) |
| Clipboard paste | ~50 ms |
| **Total** | **~460 ms** |

Already-clean transcripts skip the LLM entirely via a heuristic gate.

## Hardware requirements

### Linux

| | Minimum (CPU polish) | Recommended (GPU polish) |
|---|---|---|
| CPU | any x86_64 | any modern x86_64 |
| RAM | 8 GB | 16 GB |
| GPU | — | NVIDIA with ≥ 4 GB VRAM, CUDA ≥ 12 |
| Disk | ~3 GB for models | ~3 GB for models |
| Display | X11 | X11 |

**GPU polish VRAM budget**: the Qwen3-4B Q4_K_M model + context uses ~2.5 GB of VRAM and stays resident while `localflow` is running. On a 4 GB card you can still run a small desktop environment alongside; a second GPU-hungry app (game, Blender, another LLM) will run you out of VRAM. Quit `localflow` first in that case — it auto-cleans stale instances on restart.

**CPU polish fallback**: set `polish.n_gpu_layers: 0` in `config/default.yaml`. Polish latency goes up to ~2–5 s but VRAM stays free. Fine for short dictations; bad for anything fast-paced.

### macOS (planned)

| | Minimum | Recommended |
|---|---|---|
| Chip | Apple Silicon (M1+) | M2+ |
| Unified memory | 16 GB | 16 GB+ |

Model runs via MLX (unified memory, no VRAM/RAM split).

## Install

### One-command setup (Linux + macOS)

```bash
git clone https://github.com/sidharth-n/localflow.git
cd localflow
./setup.sh
```

That's it. `setup.sh` is idempotent and handles everything:

- Installs `xdotool`, `xclip`, `x11-utils`, `libportaudio2`, `python3-tk`, `python3-dev` via apt (Linux) or `portaudio` via brew (macOS). You'll be prompted once for your sudo password on Linux.
- Creates a `.venv` and installs the Python package.
- On Linux with an NVIDIA GPU: installs the prebuilt CUDA wheel of `llama-cpp-python` (cu124) and the `nvidia-cuda-runtime-cu12` / `nvidia-cublas-cu12` pip shims that `localflow` dlopen()s at import. On CPU-only machines: skips this step.
- Downloads the Qwen3-4B-Instruct-2507 Q4_K_M GGUF (~2.4 GB) to `~/.localflow/models/`.

Then start it:

```bash
source .venv/bin/activate
localflow
```

Hold **Right-Alt** and speak. Release to see the polished transcript appear at your cursor.

### Manual steps (if you prefer)

```bash
# system deps (Ubuntu/Debian)
sudo apt install -y xdotool xclip x11-utils libportaudio2 python3-tk python3-dev

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e ".[linux-gpu]"   # or .[linux-cpu] on a CPU-only machine

# CUDA-enabled llama-cpp-python (Linux + NVIDIA only)
pip install --force-reinstall --no-deps llama-cpp-python \
    --extra-index-url=https://abetlen.github.io/llama-cpp-python/whl/cu124/
pip install nvidia-cuda-runtime-cu12 nvidia-cublas-cu12

# fetch the polish model
python scripts/download_models.py
```

## Architecture

```
hotkey (pynput)
    │ Right-Alt held
    ▼
audio capture (sounddevice, 16 kHz mono, 30 ms chunks)
    │ release
    ▼
Moonshine STT (useful-moonshine-onnx, CPU)
    │ raw transcript
    ▼
dictionary pre-polish (regex: lump→LLM, jason→JSON, clawed→Claude, …)
    │
    ▼
skip-gate (ends in .!? → bypass the LLM)
    │
    ▼
Qwen3-4B-Instruct-2507 Q4_K_M (llama-cpp-python, all layers on GPU)
    │ cleaned transcript
    ▼
clipboard paste via xdotool Ctrl-V (or Ctrl-Shift-V in terminals)
```

Per-topic design notes live under [`knowledge-base/`](./knowledge-base/):
- [`architecture.md`](./knowledge-base/architecture.md) — overall stack
- [`model-choices.md`](./knowledge-base/model-choices.md) — why these models
- [`polish-latency.md`](./knowledge-base/polish-latency.md) — runtime + model trial log

## Configuration

Edit [`config/default.yaml`](./config/default.yaml). Knobs you'll actually touch:

- `hotkey.key` — `<alt_r>` (default), `<ctrl_r>`, `<f9>`, `<caps_lock>`, …
- `hotkey.mode` — `push_to_talk` (hold) or `toggle` (tap on / tap off)
- `polish.enabled` — false = paste the raw Moonshine transcript
- `polish.n_gpu_layers` — `-1` (all on GPU), `0` (all on CPU), or a specific number to split
- `overlay.enabled` — false hides the waveform pill

A user-override at `~/.config/localflow/config.yaml` is planned (M4) — for now, edit the default in-place.

## Troubleshooting

**`ValueError: Failed to load model from file: …Qwen3-4B-Instruct-2507-Q4_K_M.gguf`**
VRAM is full. `nvidia-smi` will show what's holding it. Usually a stale `localflow` process — but starting fresh should auto-kill it. If another app is the culprit, quit it or set `polish.n_gpu_layers: 0` for CPU fallback.

**`ModuleNotFoundError: No module named 'tkinter'`**
`sudo apt install -y python3-tk`. Or set `overlay.enabled: false` in config.

**`Warning: You are sending unauthenticated requests to the HF Hub`**
Harmless — Hugging Face hints you're downloading models anonymously. To silence it, get a read-only token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and `export HF_TOKEN=…`.

**Hotkey doesn't trigger**
Some distros/desktops consume Right-Alt for AltGr / IME switching. Try `<f9>` or `<caps_lock>` in `config/default.yaml`.

**Text doesn't paste into my terminal**
Terminals re-bind Ctrl-V. `localflow` detects terminals via `xprop WM_CLASS` and uses Ctrl-Shift-V there. If your terminal emulator isn't in the built-in list (`localflow/core/inject/linux_x11.py`), add its class name and open a PR.

## Roadmap

- [x] M0 Linux skeleton (hotkey → mic → STT → paste)
- [x] M2 Polish LLM (Qwen3-4B Q4_K_M on GPU, ~305 ms)
- [x] Overlay UX (reactive waveform, rounded pill)
- [ ] P4 Token streaming (word-boundary xdotool type via `llama-server`)
- [ ] Idle-unload VRAM (opt-in; free weights after N s of inactivity)
- [ ] M3 macOS port (MLX polish + `moonshine_mlx` + AXUIElement paste)
- [ ] M4 Auto-update config + user-override merge
- [ ] M5 Benchmark harness (p50/p95/p99)

## Contributing

PRs welcome. The repo is small and opinionated — see [`CLAUDE.md`](./CLAUDE.md) for the engineering principles. Short version: keep it small, no speculative abstractions, latency is the product.

## License

Apache-2.0 — see [`LICENSE`](./LICENSE).

Model licenses: Moonshine (Apache-2.0) · Qwen3-4B-Instruct-2507 (Apache-2.0). Neither is bundled in this repo; `setup.sh` fetches them from Hugging Face on first run.
