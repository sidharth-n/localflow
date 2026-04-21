# Research kickoff — 2026-04-21

Snapshot of the research that decided the initial stack. Preserved as a dated file because future research may obsolete parts of it.

## What Wispr Flow actually is

Not a single model — a **pipeline**:

1. **On-device STT** — a distilled Whisper variant runs locally for the raw transcript.
2. **Cloud LLM polish** — a fine-tuned Llama (hosted on Baseten) removes fillers, fixes Whisper errors, applies context-aware formatting, handles voice commands ("new paragraph", "delete that").
3. **Text injection** — result typed into the focused app.

Published latency budget: **≤ 700 ms end-of-speech → typed text**, split roughly 200 ms ASR + 200 ms LLM + 200 ms network. So Wispr Flow is *already* hybrid — not "fully cloud."

Sources: [Technical challenges behind Flow](https://wisprflow.ai/post/technical-challenges), [Wispr on Baseten](https://www.baseten.co/resources/customers/wispr-flow/).

## April-2026 STT landscape

| Model | Size | Streaming latency | English WER | Notes |
|---|---|---|---|---|
| **Moonshine v2 Tiny** | ~27 M | **50 ms** | ≈ Whisper Tiny | Apache-2.0, native streaming (encoder cache — no overlap hack) |
| **Moonshine v2 Small** | ~190 M | **148 ms** | ≈ Whisper Small | Sweet spot for 4 GB VRAM |
| **Moonshine v2 Medium** | 245 M | **258 ms** | matches / beats Whisper Large v3 | 43.7× faster than Whisper Large v3 |
| **Parakeet-unified-en-0.6b** | 600 M | **160 ms** streaming / batch | best English on Open ASR | Released April 2026; unified streaming + offline + punctuation |
| **Canary-Qwen-2.5B** | 2.5 B | offline only | **5.63 %** (leaderboard #1) | Too heavy for 4 GB; fine on M5 |
| **Whisper-large-v3-turbo** | 809 M | ~300 ms (pseudo-stream) | strong, 100+ languages | Only worth it if multilingual matters |

**Takeaway:** Moonshine beats Whisper for dictation on both speed and streaming ergonomics. Parakeet-unified is the English accuracy king. Whisper-turbo is a multilingual fallback.

Sources: [Moonshine vs Whisper benchmark 2026](https://modelslab.com/blog/audio-generation/moonshine-vs-whisper-asr-real-time-speech-2026), [Moonshine v2 arXiv](https://arxiv.org/html/2602.12241v1), [Best open-source STT 2026 — Northflank](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks), [Canary-Qwen-2.5B](https://huggingface.co/nvidia/canary-qwen-2.5b).

## April-2026 small LLM landscape

| Model | Q4 size | Fits Linux 4 GB GPU? | Notes |
|---|---|---|---|
| **Gemma 4 E4B** | ~3 GB | ❌ tight w/ STT | First sub-10B > 1300 LMArena; best quality-per-VRAM; Apache 2.0 |
| **Qwen 3.5-4B** | ~2.5 GB | ❌ tight w/ STT | 262 K ctx, strong multilingual |
| **Qwen 3-4B** | ~2.5 GB | CPU | Excellent for dictation cleanup |
| **Qwen 3-1.7B** | ~1.1 GB | ✅ | Surprisingly strong for text cleanup |
| **Gemma 3n E2B** | ~1.5 GB | ✅ | Built for edge |
| **Phi-4-mini** (3.8B) | ~2.4 GB | CPU | Top reasoning benchmarks; weak compliance (46.7 %) |
| **Llama 3.2 3B** | ~2 GB | ✅ tight | Proven baseline |

Sources: [Best small LLMs with Ollama 2026](https://localaimaster.com/blog/small-language-models-guide-2026), [Gemma 4 vs Qwen 3.5 vs Llama 4](https://ai.rs/ai-developer/gemma-4-vs-qwen-3-5-vs-llama-4-compared), [Gemma 4 on latent.space](https://www.latent.space/p/ainews-gemma-4-the-best-small-multimodal), [Qwen 3.5 vs Gemma 4 benchmarks](https://www.maniac.ai/blog/qwen-3-5-vs-gemma-4-benchmarks-by-size).

## Hardware notes

- **Linux laptop** — Ryzen 9 5900HX, 24 GB RAM, **RTX 3050 Laptop w/ 4 GB VRAM**, Ubuntu 22.04 X11. **4 GB VRAM is the binding constraint.**
- **MacBook Air M5** — 32 GB unified. MLX preferred (Ollama adopted MLX March 2026, 20–50 % faster than llama.cpp). M5 Neural Accelerators give 4× TTFT speedup vs M4.

Sources: [Apple MLX + M5](https://machinelearning.apple.com/research/exploring-llms-mlx-m5), [Ollama adopts MLX](https://9to5mac.com/2026/03/31/ollama-adopts-mlx-for-faster-ai-performance-on-apple-silicon-macs/), [RTX 3050 4 GB + LLMs](https://www.sitepoint.com/optimizing-local-llms-low-end-hardware-8gb/).

## Text injection

- **macOS**: AXUIElement `kAXSelectedTextAttribute` via Carbon HotKey APIs. Simpler via clipboard + simulated `Cmd+V`.
- **Linux X11**: `xdotool type`. Or clipboard + `Ctrl+V`.
- **Linux Wayland** (future): `ydotool` via `/dev/uinput`. Needs extra setup. Parking this until after M3.

Sources: [ydotool](https://github.com/ReimuNotMoe/ydotool), [AXUIElement insert text](https://levelup.gitconnected.com/swift-macos-insert-text-to-other-active-applications-two-ways-9e2d712ae293).

## VAD

**Silero VAD** — pre-trained, < 1 ms per 30 ms chunk on CPU, runs via ONNX so no PyTorch dep needed. Strictly better than webrtcvad for this use case.

Source: [Silero VAD](https://github.com/snakers4/silero-vad).

## Prior art (to learn from, not reinvent)

- **OpenWhispr** — cross-platform (macOS/Win/Linux), Parakeet or Whisper, BYOK cloud fallback. Closest match to what we're building.
- **VoiceTypr** — macOS/Windows, similar idea, polished.
- **VoiceInk** — Mac-only, Whisper, no LLM layer.
- **FreeFlow** — uses Groq API (not fully local).
- **sebsto/wispr** — Mac on-device Whisper.
