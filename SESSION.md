# SESSION.md — current project state

> Source of truth for "where are we?". Updated at `/end` every session. Read first at `/start`.

**Last updated:** 2026-04-22
**Active milestone:** Overlay UX polished and live — reactive waveform, true rounded pill, auto-kill of stale instances. Ready to move on to P4 token streaming or M3 Mac port.
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
- [x] **Live recording overlay** (`localflow/core/overlay.py`, `app.py`). Tkinter-based dark pill bottom-center with red pulsing dot + "Recording" → amber "Processing…" → hide. Thread-safe via `after_idle`. Commit `1184dfa`. Required `sudo apt install python3-tk` (installed 2026-04-22).
- [x] **Overlay v2 — reactive waveform + true rounded pill** (`localflow/core/overlay.py`, `localflow/core/capture.py`, `localflow/app.py`). 11 vertical bars in a 140×40 pill. Recording: red bars respond to live mic amplitude (peak RMS read from `Capture.level`, updated every 30 ms audio chunk) with bell-shape weighting + jitter + idle breathe. Processing: amber bars run a travelling sine wave. Real rounded corners via X11 Shape extension (python-xlib) — window is actually clipped, not just painted. Graceful fallback to rectangular if Xlib unavailable.
- [x] **Auto-kill previous localflow instance on startup** (`localflow/app.py::_kill_previous_instances`). Scans `/proc` for own-uid processes whose cmdline ends in `/bin/localflow` and SIGTERMs them (SIGKILL after 3 s). Fixes the recurring VRAM-pinned-by-stale-process failure where only 404 MiB free on the 3050 blocked the Qwen model from loading. Zero new deps — pure stdlib `/proc` scan.

## Rejected this session 🚫

- **LFM2.5-1.2B-Instruct** — higher IFEval on paper but consistently rephrases and adds meta-commentary on minimal-edit tasks. Few-shot couldn't suppress. See `knowledge-base/polish-latency.md` trial log.
- **Qwen3-1.7B base** — `<think>…</think>` tokens eat the budget. `/no_think` suppresses thinking but model stops applying corrections (keeps "grate", leaves "json" lowercase). No Qwen3-1.7B-Instruct-2507 GGUF available yet.
- **OpenBLAS rebuild of llama.cpp** — unnecessary; llama.cpp's built-in kernels (Justine Tunney's tinyBLAS) already beat OpenBLAS on Zen.
- **Ollama instead of llama-cpp-python** — Ollama still uses GGML kernels underneath and adds ~13 % CPU overhead, ~10× prefill overhead, and lacks fine-grained `--cache-reuse`. Not worth switching.
- **Gemma 3 / 3n / 4 variants** — 3-1B slightly faster but IFEval 62.9 vs 74.9 (worse). 3n is mobile-multimodal, 4× bigger than useful. Gemma 4 E2B 5× slower than needed.

## In progress 🔄

_(nothing — overlay + auto-kill landed this session)_

## Next up (priority order) 📋

1. **P4 — Token streaming.** Emit polished output token-by-token via xdotool type (word-boundary flush) instead of one clipboard paste. Perceived-latency win (~60 %) even though wall-clock is already good. Needs `llama-server` subprocess + SSE. ~3 h.
2. **Idle-unload VRAM** (deferred this session; user said "do it later"). Config knob `polish.unload_after_idle_s` — if set, free the Qwen weights from VRAM after N seconds of no dictation; first dictation after idle pays +3 s reload. Useful on 4 GB VRAM laptop when also gaming or running other GPU workloads. Default off.
3. **M3 — Mac port.** Mac M5 has 32 GB unified memory; MLX (`mlx-lm`) for polish and `moonshine_mlx` for STT. AXUIElement for paste, HotKey framework for global hotkey. Overlay code uses tkinter + (now) X11 Shape — need a macOS fallback for the shape call (the existing try/except already handles it, window just stays rectangular). Big milestone — plan before touching code.
4. **Benchmarks** — write `scripts/bench_latency.py` that generates p50/p95/p99 over a test suite so we can quantify regressions.

## Milestones roadmap 🗺️

- [x] **M0 — Linux skeleton**: hotkey → mic → Moonshine CPU → clipboard paste.
- [x] **M2 — Polish LLM**: llama.cpp + Qwen3-4B Q4 **on GPU** (was planned CPU). Latency goal met.
- [x] **Overlay UX** — reactive waveform, true rounded pill, compact 140×40.
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

### 2026-04-22 — Overlay v2 + auto-kill
- Installed `python3-tk` (apt) — unblocked the overlay that landed last session.
- **Overlay redesigned for a demo**: replaced text-label + pulsing dot with 11 reactive bars in a pill. Recording state reads `Capture.level` (peak amplitude updated every audio chunk in `capture.py::_callback`) and drives bar heights with bell-shape weighting + per-bar sine jitter + fast-attack/slow-decay smoothing + gentle idle breathe. Processing state: same bars in amber running a travelling sine wave.
- **True rounded corners**: used python-xlib (already installed) to apply an X11 Shape bounding mask — window is physically clipped to a pill shape, not just painted. Graceful try/except so non-X11 platforms fall back to rectangular.
- **Compact sizing**: 260×50 → 140×40, 13 → 11 bars, tighter padding.
- **Auto-kill stale instances** (`app.py::_kill_previous_instances`): recurring crash this session was a prior localflow (PID 16930) pinning 3.3 GB of the 3050's 4 GB VRAM, leaving only 404 MiB — model load failed. Added a `/proc` scan at startup that SIGTERMs (then SIGKILL after 3 s) any own-uid process whose cmdline ends in `/bin/localflow`. Pure stdlib, no new deps.
- Discussed VRAM-on-idle with user: model stays loaded for the lifetime of the process (3 s reload is too slow per-keypress). Idle-unload-after-N-seconds deferred to next session per user request.

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
