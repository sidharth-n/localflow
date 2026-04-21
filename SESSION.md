# SESSION.md — current project state

> Source of truth for "where are we?". Updated at `/end` every session. Read first at `/start`.

**Last updated:** 2026-04-21 (late)
**Active milestone:** M2 + latency work — GPU polish, dictionary pre-polish, skip-gate, overlay code landed. Overlay live-test pending python3-tk install.
**Target machine this phase:** Linux laptop (RTX 3050 4 GB, X11)

---

## Completed ✅

- [x] Research phase + hardware audit + stack decision (Moonshine + Qwen3-4B + clipboard paste)
- [x] Project scaffolded; GitHub repo created; `/start` + `/end` commands wired up
- [x] **M0.1 — Hotkey listener** (`localflow/core/hotkey.py`). pynput-based; now defaults to **Right-Alt** (`<alt_r>`) after Ctrl proved to clash with terminals + muscle-memory shortcuts.
- [x] **M0.2 — Audio capture** (`localflow/core/capture.py`). sounddevice, 16 kHz mono int16.
- [x] **M0.3 — End-to-end pipeline** (`localflow/core/inject/linux_x11.py`, `localflow/core/stt/dummy.py`, `localflow/app.py`). Clipboard paste via pyperclip + xdotool. Live-verified.
- [x] **M0.4 — Moonshine ONNX STT** (`localflow/core/stt/moonshine_onnx.py`). `moonshine/base` on CPU. ~100 ms per dictation.
- [x] **M2 core — Polish LLM** (`localflow/core/polish/llamacpp.py`). Qwen3-4B-Instruct-2507 Q4_K_M via llama-cpp-python. System prompt with tech-homophone table.
- [x] **P1 — Deterministic pre-polish** (`localflow/core/polish/dictionary.py`). Sub-ms regex homophone fixes: `lump→LLM`, `jason→JSON`, `clawed→Claude`, `jet p t→ChatGPT`, `mac book→MacBook`, `a p i→API`, etc., plus filler-word stripping. Commit `9420caf`.
- [x] **P2 — Skip-polish gate** (in `polish/dictionary.py::looks_clean`). If pre-polish output ends with `.!?` the LLM is skipped (saves ~0.3 s on already-clean phrases). Commit `efcfc90`.
- [x] **P5 — GPU offload polish LLM** (`polish/llamacpp.py` + config). llama-cpp-python prebuilt CUDA wheel (cu124) + NVIDIA runtime pip wheels (nvidia-cuda-runtime-cu12, nvidia-cublas-cu12) auto-preloaded via ctypes.RTLD_GLOBAL. All 36 Qwen3-4B layers on the 3050's 4 GB VRAM (~2.5 GB used), flash-attn on. **Measured: 5000 ms CPU → 305 ms GPU average — ~10× speedup, quality intact.** Commit `f2ff165`.
- [x] **Terminal paste fix** (`inject/linux_x11.py`). Ctrl+V is SIGINT/literal-next in terminals; now detects focused window's WM_CLASS (via `xdotool getwindowfocus` + `xprop`) and uses Ctrl+Shift+V in terminals, Ctrl+V elsewhere. 15 terminal-class keywords covered. Commit `6b24bd9`.
- [x] **Hotkey default → Right-Alt** (`<alt_r>`). Right-Ctrl collided with too many things; Fn is not catchable on Linux (handled in firmware). Commit `bbb6c3b`.
- [x] **Live recording overlay** (`localflow/core/overlay.py`, `app.py`). Tkinter-based dark pill bottom-center with red pulsing dot + "Recording" → amber "Processing…" → hide. Thread-safe via `after_idle`. Commit `1184dfa`. **Needs `sudo apt install python3-tk` to actually run — otherwise config `overlay.enabled: false` disables it.**

## Rejected this session 🚫

- **LFM2.5-1.2B-Instruct** — higher IFEval on paper but consistently rephrases and adds meta-commentary on minimal-edit tasks. Few-shot couldn't suppress. See `knowledge-base/polish-latency.md` trial log.
- **Qwen3-1.7B base** — `<think>…</think>` tokens eat the budget. `/no_think` suppresses thinking but model stops applying corrections (keeps "grate", leaves "json" lowercase). No Qwen3-1.7B-Instruct-2507 GGUF available yet.
- **OpenBLAS rebuild of llama.cpp** — unnecessary; llama.cpp's built-in kernels (Justine Tunney's tinyBLAS) already beat OpenBLAS on Zen.
- **Ollama instead of llama-cpp-python** — Ollama still uses GGML kernels underneath and adds ~13 % CPU overhead, ~10× prefill overhead, and lacks fine-grained `--cache-reuse`. Not worth switching.
- **Gemma 3 / 3n / 4 variants** — 3-1B slightly faster but IFEval 62.9 vs 74.9 (worse). 3n is mobile-multimodal, 4× bigger than useful. Gemma 4 E2B 5× slower than needed.

## In progress 🔄

_(overlay code landed; test next session after installing python3-tk)_

## Next up (priority order) 📋

1. **Overlay live test.** `sudo apt install -y python3-tk`, restart `localflow`, verify pill appears bottom-center on Right-Alt hold, flips to amber on release, hides after paste.
2. **P4 — Token streaming.** Emit polished output token-by-token via xdotool type (word-boundary flush) instead of one clipboard paste. Perceived-latency win (~60 %) even though wall-clock is already good. Needs `llama-server` subprocess + SSE. ~3 h.
3. **M3 — Mac port.** Mac M5 has 32 GB unified memory; MLX (`mlx-lm`) for polish and `moonshine_mlx` for STT. AXUIElement for paste, HotKey framework for global hotkey. Overlay code already uses tkinter so it should port directly. Big milestone — plan before touching code.
4. **Benchmarks** — write `scripts/bench_latency.py` that generates p50/p95/p99 over a test suite so we can quantify regressions.

## Milestones roadmap 🗺️

- [x] **M0 — Linux skeleton**: hotkey → mic → Moonshine CPU → clipboard paste.
- [x] **M2 — Polish LLM**: llama.cpp + Qwen3-4B Q4 **on GPU** (was planned CPU). Latency goal met.
- [ ] **Overlay UX** (1 h remaining — just install + test).
- [ ] **P4 — Token streaming** (perceived latency).
- [ ] **M1 — GPU STT** (probably skip; polish is the budget dominator).
- [ ] **M3 — Mac port.**
- [ ] **M4 — DX polish** (setup.sh, auto-download, config reload, NVIDIA pip wheels pinned in pyproject.toml).
- [ ] **M5 — Benchmarks** (p50/p95/p99 in README).

## Open questions / parked decisions ❓

- Mac hotkey: fn (Wispr-style) works on macOS because OS sees it as a modifier; we can use `<cmd>` or `<alt_r>` on Mac, decide in M3.
- Wayland support — deferred until after M3. Both `xdotool` and `xprop` need XWayland; `ydotool` path known.
- NVIDIA pip wheels aren't in `pyproject.toml` yet — installed ad-hoc this session. Fold into `setup.sh` as part of M4.
- `config/default.yaml` vs `~/.config/localflow/config.yaml` user override — loader currently only reads the default. Add user-override merge in M4.

## Session log 📝

### 2026-04-21 — Project kickoff (morning)
- Researched Wispr Flow; surveyed April-2026 STT/LLM landscape; chose Moonshine + Qwen3-4B/Gemma-4-E4B.
- Scaffolded repo, CLAUDE.md, knowledge-base/, `/start` and `/end` slash commands.

### 2026-04-21 — M0.1–M0.4 (afternoon)
- Hotkey + capture + clipboard-paste + Moonshine STT all shipped and live-tested. Commits `36fa2d0`, `757c61f`, `7f14c19`.

### 2026-04-21 — M2 + latency overhaul (evening)
- **P1 dict pre-polish** — hand-maintained homophone table runs in <1 ms before the LLM. Commit `9420caf`.
- **Research — runtime + model**: Three agent passes documented in `knowledge-base/polish-latency.md`:
  - Ollama vs llama.cpp → llama.cpp wins (~13 % faster, better caching).
  - LFM2.5-1.2B promised 1.64× decode + higher IFEval — rejected in practice (rephrases).
  - Qwen3-1.7B base — thinking-mode kills quality even with `/no_think`.
  - No Gemma variant wins on both axes.
- **P2 skip-gate** — 0 ms on clean cases. Commit `efcfc90`.
- **P5 GPU offload** — the decisive win. Installed llama-cpp-python cu124 wheel + `nvidia-cuda-runtime-cu12` + `nvidia-cublas-cu12`; preload `.so`s via ctypes.RTLD_GLOBAL at import. All 36 Qwen3-4B layers onto the 3050. **Polish 5000 ms → 305 ms.** Commit `f2ff165`.
- **Terminal paste fix** — WM_CLASS detection → Ctrl+Shift+V in terminals. Commit `6b24bd9`.
- **Hotkey → Right-Alt.** Right-Ctrl collided with too much. Confirmed Fn isn't catchable on Linux — firmware-level key. Commit `bbb6c3b`.
- **Overlay code landed.** Tkinter pill at bottom-center, pulsing red → amber → hide. Commit `1184dfa`. Needs `python3-tk` apt install next session.

### System deps accumulated on the Linux laptop this session
- `python3-dev`, `libportaudio2`, `xdotool`, `xclip`, `x11-utils` (xprop), and next: `python3-tk`
- pip: `llama-cpp-python` (cu124 CUDA wheel), `nvidia-cuda-runtime-cu12`, `nvidia-cublas-cu12`, `symspellpy`, `rapidfuzz`, `huggingface_hub`, `useful-moonshine-onnx`

### End-to-end latency budget, measured
| Stage | CPU baseline (M2 initial) | After GPU + dict + skip-gate |
|---|---|---|
| Mic capture drain | ~10 ms | ~10 ms |
| Moonshine STT (CPU) | ~100 ms | ~100 ms |
| Pre-polish (regex) | — | ~1 ms |
| Polish LLM | 1 500 – 5 000 ms | **~305 ms** (or 0 ms on skip) |
| Paste | ~50 ms | ~50 ms |
| **Total typical** | **~2 s (up to 15 s)** | **~460 ms** |
