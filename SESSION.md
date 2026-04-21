# SESSION.md — current project state

> Source of truth for "where are we?". Updated at `/end` every session. Read first at `/start`.

**Last updated:** 2026-04-21
**Active milestone:** M0 — Project skeleton
**Target machine this phase:** Linux laptop (RTX 3050 4 GB, X11)

---

## Completed ✅

- [x] Research phase: Wispr Flow architecture decoded, April-2026 STT/LLM landscape surveyed
- [x] Hardware audit of both target machines (Linux 3050/4 GB, Mac M5/32 GB)
- [x] Stack decided: Moonshine v2 STT + Qwen3-4B/Gemma-4-E4B polish + clipboard-paste injection
- [x] Project scaffolded (Python package, configs, CLAUDE.md, knowledge-base/)
- [x] GitHub repo created and first commit pushed
- [x] `/start` and `/end` slash commands wired up

## In progress 🔄

_(nothing — ready to start M0 feature work next session)_

## Next up (priority order) 📋

1. **M0.1 — Hotkey listener** — `localflow/core/hotkey.py` using `pynput`, configurable key from `config/default.yaml`, toggle push-to-talk mode. Test: press-and-release prints timing to stdout.
2. **M0.2 — Audio capture** — `localflow/core/capture.py` using `sounddevice`, 16 kHz mono, PCM16, ring buffer. Test: record while hotkey held, dump WAV to /tmp.
3. **M0.3 — Dummy STT → clipboard paste loop** — fake transcript, real clipboard-paste. End-to-end smoke test that proves the hotkey → mic → paste chain works before we add ML.
4. **M0.4 — Moonshine ONNX CPU integration** — real STT, CPU only first. Replace the dummy. Measure latency.
5. **M0.5 — Basic tray/daemon** — `localflow` CLI command that runs forever with a console log line per invocation.

## Milestones roadmap 🗺️

- [ ] **M0 — Skeleton** (current): Linux, CPU-only, hotkey → mic → Moonshine CPU → clipboard paste. No polish LLM yet.
- [ ] **M1 — GPU STT**: Moonshine on CUDA (Linux); measure p50/p95 latency on 3050.
- [ ] **M2 — Polish LLM**: llama.cpp + Qwen3-4B Q4 on CPU. Configurable system prompt for disfluency removal + formatting.
- [ ] **M3 — Mac port**: Moonshine via CoreML/MLX, Gemma-4-E4B via mlx-lm, AXUIElement injection, global hotkey via HotKey.
- [ ] **M4 — DX polish**: `setup.sh` does everything end-to-end on a fresh machine. Model auto-download. Tray icon. Config reload.
- [ ] **M5 — Benchmarks**: `scripts/bench_latency.py` — p50/p95/p99 numbers in README.

## Open questions / parked decisions ❓

- Clipboard-paste default vs direct injection — confirmed clipboard-paste for v1 (simpler, more compatible).
- Wayland support — deferred until after M3. `ydotool` path known, not worth the yak-shave right now.
- Voice commands ("new paragraph", "bold this") — deferred to post-M5.

## Session log 📝

### 2026-04-21 — Project kickoff
- Researched Wispr Flow (hybrid: on-device distil-Whisper + cloud Llama polish, ~700 ms budget).
- Surveyed April-2026 STT models: Moonshine v2 (50-258 ms streaming), Parakeet-unified-en-0.6b (160 ms), Canary-Qwen-2.5B (best WER but 2.5 B params).
- Surveyed April-2026 small LLMs: Gemma 4 E4B, Qwen 3.5-4B, Qwen 3-1.7B, Phi-4-mini. Chose Qwen 3-4B for Linux (fits in 24 GB RAM Q4) and Gemma 4 E4B for M5.
- Confirmed hardware: Linux RTX 3050 is the *Laptop* variant with 4 GB VRAM (not 8), so LLM must run on CPU or be sub-2 GB.
- Scaffolded project structure, CLAUDE.md, knowledge-base/, `/start` and `/end` slash commands.
- Pushed initial commit to `github.com/sidharth-n/localflow`.
