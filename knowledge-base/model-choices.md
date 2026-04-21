# Model choices

Exact models, per machine, per role, with the reasoning. Update when a choice changes.

## Summary

| | **Linux (RTX 3050, 4 GB VRAM)** | **MacBook M5 (32 GB unified)** |
|---|---|---|
| STT | **Moonshine v2 Small** (ONNX, CUDA EP) | **Moonshine v2 Medium** (MLX / CoreML) |
| VAD | **Silero VAD** (ONNX CPU) | **Silero VAD** (ONNX CPU) |
| Polish LLM | **Qwen 3-4B Instruct Q4_K_M** (llama.cpp, **CPU**) | **Gemma 4 E4B Instruct** (mlx-lm) |

## STT

### Linux: Moonshine v2 Small
- 148 ms streaming latency, ~190 M params, Apache 2.0.
- Fits comfortably in 4 GB VRAM alongside Silero VAD.
- CUDA Execution Provider via `onnxruntime-gpu`.
- English-only — matches v1 scope.
- Upgrade path: Moonshine Medium if Small proves inaccurate; Parakeet-unified if we want best-in-class English WER.

### Mac: Moonshine v2 Medium
- 258 ms streaming latency, 245 M params, matches Whisper Large v3 accuracy.
- 32 GB unified means size is free.
- MLX or CoreML execution — benchmark both before committing.

### Why not Whisper for dictation
- Not natively streaming (needs overlap hack).
- Turbo-large is 300+ ms even with tricks, 3× Moonshine Medium.
- Only wins on multilingual, which v1 doesn't need.

### Why not Parakeet
- Accuracy-best for English, but more complex deployment (NeMo / parakeet.cpp), and the leaderboard win over Moonshine Medium is small. Revisit in M4 if accuracy turns out to be a real problem.

### Why not Canary-Qwen-2.5B
- Top of Open ASR leaderboard, but 2.5 B params is heavy — won't fit alongside anything else on 4 GB VRAM, and offline-only mode means we lose streaming UX.

## VAD

### Silero VAD (both machines)
- < 1 ms per 30 ms chunk on CPU thread.
- ONNX-only runtime — no PyTorch dep.
- Already the industry default, way better than webrtcvad.

## Polish LLM

### Linux: Qwen 3-4B Instruct Q4_K_M on CPU
- ~2.5 GB on disk, runs on 24 GB system RAM with plenty of headroom.
- ~20 tok/s on Ryzen 9 5900HX (Zen 3, 16 threads) via llama.cpp.
- Strong instruction-following per IFEval; excellent at "clean up this text" prompts.
- Why not on GPU: 4 GB VRAM is already committed to Moonshine. STT latency wins that fight.
- Why not Qwen 3-1.7B on GPU instead: 1.7B isn't quite strong enough to catch subtle transcription errors (e.g., homophones) from context. 4B is meaningfully better at that per community reports.

### Mac: Gemma 4 E4B Instruct via mlx-lm
- 8 B raw params but 4 B memory footprint (MoE-like routing), ~3 GB Q4.
- First sub-10B to break 1300 LMArena — best quality-per-VRAM of April 2026.
- Apache 2.0, Google's edge-tuned line.
- MLX + M5 Neural Accelerators give sub-200 ms for a 30-token polish.

### Why not Phi-4-mini
- Top benchmarks but 46.7 % compliance rate on structured output — unreliable for a pipeline that just needs clean text back. Not worth the quality variance.

### Why not Llama 3.2 3B
- Decent baseline but outclassed by Qwen 3 / Gemma 4 on instruction-following at the same size. Kept as fallback if Qwen has license concerns.

## Quantization

- **Q4_K_M** is the sweet spot: 4-bit with k-means grouping, ~98 % of FP16 quality at 25 % of the size.
- Q5_K_M is 15-20 % larger for marginal quality — not worth it at the 4 GB budget.
- Q3 is a step too far for instruction-following tasks; avoid.

## Model storage layout

All weights go under `~/.localflow/models/`, never in the repo. `.gitignore` blocks `*.gguf`, `*.onnx`, `*.safetensors`, `*.mlpackage`.

```
~/.localflow/models/
├── moonshine-small/        # onnx + tokenizer
├── moonshine-medium/
├── silero-vad.onnx
├── qwen3-4b-instruct.Q4_K_M.gguf
└── gemma-4-e4b/            # mlx safetensors
```

`scripts/download_models.py` (M4) fetches these based on detected OS + GPU.
