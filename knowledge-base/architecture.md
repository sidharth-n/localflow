# Architecture

The shape of the pipeline and why it's shaped this way. Update this file when a big structural decision changes.

## Pipeline (happy path)

```
[hotkey down]
      │
      ▼
 open 16 kHz mono mic (sounddevice)
      │
      ▼
 Silero VAD gates 30 ms chunks  ──► (silence chunks dropped)
      │
      ▼
 streaming STT encoder (Moonshine) — runs concurrently with speech
      │
[hotkey up]
      │
      ▼
 STT decoder finalize  ──► raw transcript string
      │
      ▼
 polish LLM (Qwen 3-4B / Gemma 4 E4B) — ~30-word sliding prompt
      │
      ▼
 cleaned text
      │
      ▼
 clipboard write → simulated Ctrl/Cmd+V → restore clipboard after 500 ms
```

## State machine

```
IDLE ──hotkey_down──► RECORDING ──hotkey_up──► TRANSCRIBING
                        │                              │
                        └──error──► IDLE               ▼
                                                POLISHING ──► INJECTING ──► IDLE
```

States are enforced by a single `Pipeline` object in `localflow/core/pipeline.py`. Each transition emits a structured log line with timestamps — this is how we measure latency.

## Cross-platform boundary

Everything in `localflow/core/` is OS-agnostic *except* the three subpackages below, where platform-specific backends plug in:

| Subpackage | Linux backend | macOS backend |
|---|---|---|
| `core/stt/` | `moonshine_onnx.py` (CUDA EP) | `moonshine_mlx.py` or CoreML |
| `core/polish/` | `llamacpp.py` | `mlx.py` |
| `core/inject/` | `linux_x11.py` | `macos.py` |

Each backend implements a small `Base*` protocol (not an ABC — keep it light). The pipeline picks a backend based on `config/default.yaml` + OS detection.

## Why clipboard-paste, not direct insertion

Direct AX insertion on Mac and `xdotool type` on Linux both *work*, but:

- They break in some Electron / Qt apps.
- They can mess with undo history weirdly.
- They're slower for long text (key-by-key simulation).
- Unicode handling is patchy (especially ydotool on Wayland).

Clipboard + `Cmd/Ctrl+V` has none of these issues and works in every app including terminals. Downsides: it clobbers the user's clipboard for ~500 ms (we restore it), and Cmd+V isn't always the paste shortcut (e.g. terminals sometimes need `Ctrl+Shift+V`). The trade is worth it.

Direct injection stays available as an opt-in via `inject.method: direct` in config.

## Why polish LLM on CPU (Linux)

On the 4 GB RTX 3050, STT + polish LLM don't both fit on GPU. STT is *latency-critical* per-millisecond (user feels every 100 ms), polish LLM runs *once per utterance on ~30 tokens* so 200-400 ms on CPU is fine. Ryzen 9 5900HX + Qwen 3-4B Q4_K_M does ~20 tok/s, which gives us a polish step under 400 ms for typical utterances.

On M5 with 32 GB unified memory, everything lives in MLX together and there's no split.

## Latency budget (end-of-speech → typed text)

| Stage | Linux RTX 3050 | Mac M5 |
|---|---|---|
| Finalize STT | ~150 ms | ~260 ms |
| Polish LLM (~30 tokens) | ~300 ms (CPU) | ~200 ms (MLX) |
| Clipboard write + paste | ~30 ms | ~30 ms |
| Restore clipboard (async) | 0 ms (non-blocking) | 0 ms |
| **Total** | **~500 ms** | **~500 ms** |

Competitive with Wispr Flow's 700 ms cloud budget, zero network variance.

## What gets streamed vs batched

- **Audio → STT**: streamed. Moonshine's encoder caches state, so we feed 30 ms chunks live.
- **STT → LLM**: batched. Polish runs once on the final transcript. Streaming the LLM output would make mid-sentence typing visible and is usually worse UX for dictation.
- **LLM → inject**: batched. Full cleaned text copied + pasted once.

## What we're explicitly *not* doing in v1

- Voice commands ("new paragraph", "bold this"). Post-M5.
- Streaming LLM output while typing. Jittery UX.
- Multi-language auto-switching. English only until M5.
- Personal dictionary, snippets, cross-device sync. Wispr-only features; deferred indefinitely.
- Wayland support. Park until X11 version works.
