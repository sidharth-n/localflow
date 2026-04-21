# SESSION.md — current project state

> Source of truth for "where are we?". Updated at `/end` every session. Read first at `/start`.

**Last updated:** 2026-04-21
**Active milestone:** M2 — Polish LLM (done). M0.5 + M1 deferred.
**Target machine this phase:** Linux laptop (RTX 3050 4 GB, X11)

---

## Completed ✅

- [x] Research phase: Wispr Flow architecture decoded, April-2026 STT/LLM landscape surveyed
- [x] Hardware audit of both target machines (Linux 3050/4 GB, Mac M5/32 GB)
- [x] Stack decided: Moonshine v2 STT + Qwen3-4B/Gemma-4-E4B polish + clipboard-paste injection
- [x] Project scaffolded (Python package, configs, CLAUDE.md, knowledge-base/)
- [x] GitHub repo created and first commit pushed
- [x] `/start` and `/end` slash commands wired up
- [x] **M0.1 — Hotkey listener** (`localflow/core/hotkey.py`): pynput, PTT + toggle, auto-repeat guard, unit-level smoke test passes
- [x] **M0.2 — Audio capture** (`localflow/core/capture.py`): sounddevice InputStream, 16 kHz mono int16, start/stop API; verified 1 s recording yields 15,840 samples with real signal
- [x] **M0.3 — Dummy STT → clipboard paste loop** (`localflow/core/stt/dummy.py`, `localflow/core/inject/linux_x11.py`, `localflow/app.py`): full pipeline end-to-end on the 3050 laptop; verified live — real hotkey press, mic recording, dummy transcript pasted at cursor, per-stage timings logged
- [x] **M0.4 — Moonshine ONNX CPU STT** (`localflow/core/stt/moonshine_onnx.py`): `useful-moonshine-onnx` wheel, `moonshine/base` model. Measured **288 ms cold / 340 ms warm on 10 s audio** on Ryzen 9 5900HX → ~33× realtime, projects to ~100 ms per typical 3 s dictation. Live pipeline confirmed working by user.
- [x] **M2 — Polish LLM** (`localflow/core/polish/llamacpp.py`, `localflow/core/config.py`, `scripts/download_models.py`): llama-cpp-python 0.3.20 (CPU, no BLAS), Qwen3-4B-Instruct-2507 Q4_K_M (~2.4 GB) pulled from `unsloth/Qwen3-4B-Instruct-2507-GGUF`. System prompt upgraded with explicit tech-homophone fixes. Benched on 7 cases: **case 1 "i want to build a lump…" → "I want to build an LLM…"** (the exact user pain-point is fixed). Latency 1.5–5 s per polish (median ~2 s). Pipeline now: hotkey → capture → STT → polish → paste, with automatic fall-through to raw STT if polish raises.

## In progress 🔄

_(nothing)_

## Next up (priority order) 📋

1. **OpenBLAS rebuild of llama.cpp** — should cut polish latency ~1.5×. Needs `sudo apt install libopenblas-dev`, then `CMAKE_ARGS="-DGGML_BLAS=on -DGGML_BLAS_VENDOR=OpenBLAS" pip install --force-reinstall --no-cache-dir llama-cpp-python`.
2. **M1 — GPU STT.** Moonshine via `onnxruntime-gpu` CUDA EP. Probably diminishing returns given polish now dominates the budget; optional.
3. **M0.5 — Tray/daemon CLI.** Proper systray icon, graceful shutdown. Nice-to-have.
4. **Metrics log file.** `logging.metrics_file` in config is already defined but unused — write a JSONL line per dictation with per-stage timings, to make bench scripts in M5 easy.

## Milestones roadmap 🗺️

- [x] **M0 — Skeleton** (4/5 done): hotkey → mic → Moonshine CPU → clipboard paste. Works end-to-end on Linux.
- [x] **M2 — Polish LLM**: llama.cpp + Qwen3-4B-Instruct-2507 Q4_K_M on CPU. Tech-homophone-aware prompt.
- [ ] **M0.5 — Tray/daemon**: systray icon, `localflow` as proper daemon.
- [ ] **M1 — GPU STT**: Moonshine on CUDA; p50/p95 on 3050.
- [ ] **M3 — Mac port**: Moonshine via CoreML/MLX, Gemma-4-E4B via mlx-lm, AXUIElement injection, global hotkey via HotKey.
- [ ] **M4 — DX polish**: `setup.sh` does everything end-to-end. Model auto-download. Tray icon. Config reload.
- [ ] **M5 — Benchmarks**: `scripts/bench_latency.py` — p50/p95/p99 numbers in README.

## Open questions / parked decisions ❓

- Clipboard-paste default vs direct injection — confirmed clipboard-paste for v1 (simpler, more compatible).
- Wayland support — deferred until after M3. `ydotool` path known, not worth the yak-shave right now.
- Voice commands ("new paragraph", "bold this") — deferred to post-M5.
- Moonshine Small/Medium unavailable in `useful-moonshine-onnx` wheel (only `tiny`/`base` ship). Watch upstream; swap in Small once published, or package the upstream repo weights manually.
- System deps for Linux: `python3-dev`, `libportaudio2`, `xdotool`, `xclip`. Add to `setup.sh` in M4.

## Session log 📝

### 2026-04-21 — Project kickoff
- Researched Wispr Flow (hybrid: on-device distil-Whisper + cloud Llama polish, ~700 ms budget).
- Surveyed April-2026 STT models: Moonshine v2 (50-258 ms streaming), Parakeet-unified-en-0.6b (160 ms), Canary-Qwen-2.5B (best WER but 2.5 B params).
- Surveyed April-2026 small LLMs: Gemma 4 E4B, Qwen 3.5-4B, Qwen 3-1.7B, Phi-4-mini. Chose Qwen 3-4B for Linux (fits in 24 GB RAM Q4) and Gemma 4 E4B for M5.
- Confirmed hardware: Linux RTX 3050 is the *Laptop* variant with 4 GB VRAM (not 8), so LLM must run on CPU or be sub-2 GB.
- Scaffolded project structure, CLAUDE.md, knowledge-base/, `/start` and `/end` slash commands.
- Pushed initial commit to `github.com/sidharth-n/localflow`.

### 2026-04-21 — M0.1–M0.4 in one session
- Wrote `core/hotkey.py` (pynput). Found and fixed a subtle bug: `HotKey.parse("<ctrl_r>")` returns a bare `KeyCode` whose `_symbol` is None, while the Listener delivers `Key.ctrl_r` whose `_symbol` is `"Control_R"` — they compare unequal. Promoted the parsed KeyCode to the matching `Key` enum member by `vk`+`char`.
- Wrote `core/capture.py` (sounddevice). 16 kHz mono int16, 30 ms blocksize. start()/stop() with list-of-arrays accumulator.
- Wrote `core/stt/dummy.py` and `core/inject/linux_x11.py` (pyperclip + `xdotool key ctrl+v` + prior-clipboard restore). Wired into `app.py`.
- Live-verified M0.3 end-to-end: Right-Ctrl press/release → dummy transcript pasted at cursor. Log showed capture-drain 10 ms, stt 0 ms, paste 557 ms (mostly the deliberate 500 ms clipboard restore).
- Installed `useful-moonshine-onnx` (v20251121). Package only ships `tiny`/`base`. Wrote `core/stt/moonshine_onnx.py` against `moonshine/base`, swapped it into `app.py`.
- Benched on Ryzen 9 5900HX CPU, 10 s clip: **288 ms cold / 340 ms warm / 313 ms int16 path** — all produced identical transcript. User-tested live; accuracy is usable but mis-hears terms like "LLM" → "lump", confirming the polish LLM is the right next step.
- System deps required along the way (all installed this session): `python3-dev`, `libportaudio2`, `xdotool`, `xclip`.

### 2026-04-21 — M2 polish LLM live
- Installed `llama-cpp-python` 0.3.20 (first attempt with `-DGGML_BLAS=on -DGGML_BLAS_VENDOR=OpenBLAS` failed — no `libopenblas-dev` on system; fell back to plain CPU build, which works).
- Pulled `unsloth/Qwen3-4B-Instruct-2507-GGUF` / `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (~2.4 GB, ~38 min on this connection) to `~/.localflow/models/`. Added `scripts/download_models.py` so future machines can re-fetch deterministically.
- Added `localflow/core/config.py` — tiny YAML loader for `config/default.yaml`. All components now config-driven instead of hardcoded.
- Wrote `localflow/core/polish/llamacpp.py` (`QwenPolish` class). Uses `create_chat_completion` with system prompt + user turn.
- Rewrote `localflow/app.py`: config-loaded pipeline, polish stage between STT and paste, per-stage timing logged, polish errors silently fall back to raw STT (so a bad LLM can't kill dictation).
- First prompt version failed the user's reported test case — "lump" stayed "lump". Rewrote the system prompt with explicit tech-homophone table (lump→LLM, jason→JSON, a-p-i→API, clawed→Claude, jet-p-t→ChatGPT, get-hub→GitHub, mackbook→MacBook). 7/7 benchmark cases now pass, including the live pain-point.
- Latency: 1.5–5 s polish per dictation, median ~2 s. Slower than hoped — no BLAS is the bottleneck. OpenBLAS rebuild queued as first follow-up.
