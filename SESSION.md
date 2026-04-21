# SESSION.md — current project state

> Source of truth for "where are we?". Updated at `/end` every session. Read first at `/start`.

**Last updated:** 2026-04-21
**Active milestone:** M0 — Project skeleton (4/5 done; M0.5 pending)
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

## In progress 🔄

_(nothing — pipeline works; next session decides M2 vs M0.5 vs M1)_

## Next up (priority order) 📋

1. **M2 — Polish LLM** (jumping ahead of M1). User reported mis-hearings in live testing ("LLM" → "lump") that a GPU speed-up won't fix. Plan: llama.cpp + Qwen3-4B Q4_K_M on CPU, system prompt in `config/default.yaml` already drafted for disfluency removal + formatting. New file: `localflow/core/polish/llamacpp.py`. Budget: keep latency < 700 ms total.
2. **M0.5 — Tray/daemon CLI.** Still wanted, but lower urgency — `localflow` already runs forever with a ready log line. Real work is a proper systray icon + graceful shutdown; defer until M2 ships.
3. **M1 — GPU STT.** Moonshine on CUDA (Linux), measure p50/p95 on 3050. Deprioritized because CPU latency is already ~100 ms for typical phrases — GPU savings won't dominate the UX budget now that polish is on deck.

## Milestones roadmap 🗺️

- [x] **M0 — Skeleton** (4/5 done): hotkey → mic → Moonshine CPU → clipboard paste. Works end-to-end on Linux.
- [ ] **M2 — Polish LLM**: llama.cpp + Qwen3-4B Q4 on CPU. Configurable system prompt. **(Next)**
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
