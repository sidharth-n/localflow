# Polish-stage latency plan

Research dated 2026-04-21. Context: M2 polish LLM (Qwen3-4B Q4 on CPU, no BLAS) is landing 1.5–5 s on short dictations, ~15 s on long ones. Target: Wispr Flow–class end-to-end (~700 ms) on the Linux laptop (Ryzen 9 5900HX, RTX 3050 4 GB).

## The honest baseline

Wispr Flow is **cloud**. Their <700 ms p99 runs on Baseten + TensorRT-LLM with a fine-tuned Llama and a <250 ms LLM budget.[^wispr-baseten][^wispr-voibe] We can't hit that with a 4B CPU model. We *can* hit ~500 ms wall-clock and ~200 ms perceived TTFT with the right stack. Anchor latencies:

- SmolLM2-1.7B Q8 on a Ryzen **5900X**: 22.5 tok/s tg128.[^smollm-bench] The 5900HX is ~15–20 % slower → expect **~18–25 tok/s for 1.7B Q4**, **~40–60 tok/s for 0.6B Q4**.
- Superwhisper local: 1–2 s per utterance (still noticeably slow).[^superwhisper]
- Blazing Transcribe: ~530 ms end-to-end on Apple Neural Engine **by skipping the polish LLM entirely**.[^blazing] Loudest data point in the dataset: the fastest local tools avoid the polish stage, not optimize it.

To polish ~30 tokens in <250 ms on CPU we need >=120 tok/s sustained → **0.6B class or smaller**, or we don't generate tokens at all.

## Ranked plan (next-session moves)

### P1. SymSpell + homophone dict pre-polish — 40 ms, 2 h

Before the LLM, run deterministic cleanup:
- regex-strip fillers ("um", "uh", "like", "you know")
- apply a user-editable homophone map (`lump→LLM`, `jason→JSON`, `clawed→Claude`, `get hub→GitHub`)
- naive sentence-end punctuation heuristic

SymSpell gives sub-ms fuzzy correction with a custom frequency dictionary.[^symspell][^symspellpy] The homophones currently reported as failures are literally keyword substitutions — deterministic code handles them better than an LLM.

Install: `pip install symspellpy rapidfuzz`.

### P2. Skip-polish gate — 0 ms on clean cases, 1 h

After P1, if the result passes: no filler tokens left, ≤8 words, no low-confidence STT segments → commit raw and skip the LLM. Even a 30 % skip rate is a meaningful UX win.

### Trial log (2026-04-21)

- **LFM2.5-1.2B-Instruct Q4_K_M — REJECTED on quality, despite higher IFEval.** Downloaded and benched on our 7-case suite. Results: consistent rephrasing / meta-commentary bias that a "no preamble, no commentary" system prompt and a 4-shot in-context format demo couldn't suppress. Representative failures: `"hello world"` → `"Clearly, the speaker meant to say 'Hello world.'"`; `"um so like you know i was thinking..."` → `"Certainly, let's refine the speech for clarity. The speaker seems..."`; `"i want to build a lump..."` → `"Build a system that creates text..."` (even summarized-away the homophone the dictionary had already fixed). Latency 800–3000 ms — no speed win big enough to compensate. **Lesson: IFEval at the aggregate level doesn't predict "minimal-edit" fidelity on tasks below 2B params.** Worth retrying if Liquid ships a larger variant or a text-edit fine-tune.
- **Qwen3-1.7B Q4_K_M (base, `unsloth/Qwen3-1.7B-GGUF`) — REJECTED.** The base Qwen3-1.7B is the hybrid-thinking variant. Default benchmark was ~16 s per case because `<think>…</think>` tokens ate the budget. Adding `/no_think` to the system prompt cuts that to ~1.2 s median (vs Qwen3-4B's ~2 s) but output still carries an empty `<think></think>` prefix AND the model stops applying our corrections ("grate" stays "grate", "json" stays lowercase, "Claude code" not capitalized). **Instruction-following at 1.7B on our minimal-edit task is insufficient.** A proper Qwen3-1.7B-Instruct-2507 GGUF would likely fix this, but none is published yet.
- **Verdict after all three trials:** stay on Qwen3-4B-Instruct-2507 for quality. The big remaining latency lever is **P2 (skip-polish gate)**, not the model swap.

### P3. Qwen3-4B → **Qwen3-1.7B** Q4_K_M + `llama-server` — ~500 ms polish, 2 h

**Updated 2026-04-21 after runtime/model deep-dive.** Originally planned Qwen3-1.7B. Published Liquid AI benchmarks on a Ryzen HX 370 laptop CPU (very close to our 5900HX) flip the choice:[^lfm2-report]

| | Qwen3-1.7B | **LFM2-1.2B** |
|---|---|---|
| Decode tok/s (Q4_0, 1K ctx, llama.cpp) | 60.8 | **99.7** (1.64×) |
| Prefill tok/s | 2,019 | **2,784** (1.38×) |
| IFEval | 73.98 % | **74.89 %** |
| Q4_K_M size | ~1 GB | ~760 MB |

Faster **and** slightly better at instruction-following. For a ~50-token polish, that's ~500 ms generation instead of ~820 ms.

Runtime move: drop `llama-cpp-python` (Python-side tokenization dominates on short prompts)[^llama-cpp-python-2073] in favor of a persistent **`llama-server`** subprocess on localhost with:
- `--flash-attn` (`-fa`) — flash attention on CPU
- `--cache-reuse 256` — system prompt prefilled once per session[^cache-13606][^cache-20574]
- `-ctk q8_0 -ctv q8_0` — quantized KV cache (required for `-fa`; ~2.5 % slower but halves KV footprint)[^kv-5932]
- `-t 8` — physical cores on 5900HX
- Prime the system prompt at startup so first real request hits prefill cache.

Do NOT go below Q4_K_M on a ≤2B model — Q2/IQ2/Q3 break instruction-following at tiny scale.[^quant-overview]

Fallback model to keep behind a config flag: **LFM2-700M-Instruct Q4_K_M** (~430 MB, ~150 tok/s expected) if 1.2B still isn't fast enough. Keep **Qwen3-1.7B** as the regression-check baseline.

Install:
```
huggingface-cli download LiquidAI/LFM2.5-1.2B-Instruct-GGUF \
  LFM2.5-1.2B-Instruct-Q4_K_M.gguf --local-dir ~/.localflow/models/
# also the llama-server binary from llama.cpp (not bundled with llama-cpp-python)
```

### P4. Stream tokens into xdotool as they generate — perceived latency −60 %, 3 h

Instead of one clipboard paste at the end, emit polished output token-by-token through `xdotool type --delay 0` (or `ydotool` on Wayland). First character visible ~50 ms after the model starts. This is the VOXD pattern.[^voxd] With P3 and this together, **perceived TTFT drops under 200 ms** even if wall-clock is ~500 ms.

Buffer and flush on whitespace for word-level atomicity; keep clipboard-paste as fallback behind a config flag.

### P5 (shelf). Speculative decoding — 2 h, uncertain CPU gain

llama.cpp speculative decoding gives 1.5–2.5× **on GPU** for predictable outputs.[^spec-docs][^spec-10466] On CPU with a 1.7B target the draft-model overhead usually eats the win. Revisit only after we free the 4 GB VRAM (M1 CUDA STT).

## Rejected / unpromising

| Idea | Why not |
|---|---|
| **Alternative runtimes (MLC-LLM, OpenVINO, KTransformers, PowerInfer, ExLlamaV2-CPU)** | No published Zen 3 numbers beating llama.cpp for <3 B. OpenVINO targets Intel AVX-VNNI/AMX. KTransformers targets Sapphire Rapids + MoE. PowerInfer needs ≥8 GB VRAM. Stay on llama.cpp.[^tunney][^openvino] |
| **Ollama** | Ollama's new-engine (2025) still uses GGML for CPU kernels, so same math as llama.cpp — but **~13 % slower decode, ~10× slower prefill**, no fine-grained `--cache-reuse`, and auto-unload defeats our low-TTFT goal. Use `llama-server` directly.[^ollama-morph][^ollama-mitkox][^ollama-nullmirror][^ollama-newengine] |
| **Gemma 3 1B** | On the *same* Ryzen CPU as the LFM2 benchmark, Gemma 3 1B actually edges LFM2-1.2B on decode (99.3 vs 89.0 tok/s). But IFEval **62.90 vs 74.89** — a 12-point gap in instruction-following that matters when the system prompt carries a homophone-correction table. Reject on quality, not speed.[^lfm2-report] |
| **Gemma 3n (E2B/E4B)** | Mobile-multimodal design, Q4_K_M ≈ 4–6 GB RAM (4–8× LFM2.5). No public IFEval for text-only polish tasks. Wrong tool.[^gemma-3n] |
| **Gemma 4 (E2B/E4B, 2026-04-02)** | E2B ~2.3 B effective / 5.1 B raw, Q4_K_M ~3.1 GB on disk. CPU decode ~10–20 tok/s on laptop Zen → ~5× slower than LFM2.5. Google hasn't published IFEval, so the quality case is unproven. Revisit only if both IFEval ≥80 % and a ≥60 tok/s Zen 3 benchmark appear.[^gemma-4-gguf][^gemma-4-blog][^small-2026] |
| **ik_llama.cpp** (ikawrakow fork) | Real CPU wins (+10–25 % on Zen 3 with AVX2, up to +60 % on AVX-512 hardware).[^ik-llama] Worth a side-experiment benchmark **after** P1–P4 ship. Not a blocker. |
| **OpenBLAS rebuild** | llama.cpp already uses Justine Tunney's hand-tuned kernels (up to 2.8× over OpenBLAS on Zen4).[^tunney] Matters only for prompt-eval on very long prompts. *(Earlier plan had this as a win; research corrects that.)* |
| **FlashAttention on CPU** | Helps prompt processing only, no decode win.[^flash-7209] |
| **CoEdIT / flan-T5-grammar-large** | 780 M params, encoder-decoder — no CPU speed advantage over LFM2-1.2B and worse at domain-word substitution.[^coedit] |
| **Gemma 3 270M** | 51 % IFEval; too weak to follow a homophone table. Viable only if P1's dictionary does the heavy lifting.[^gemma-270m] |
| **Phi-4-mini (3.8 B)** | 2× the params of LFM2-1.2B — wrong direction for latency. |
| **Qwen3-0.6B, Granite 3.3 2B, Nemotron Nano 2, OLMoE, SmolLM3** | No sub-2B CPU numbers beating LFM2 in 2026 benchmarks. OLMoE's sparse activations don't help llama.cpp CPU paths. |
| **Dictation-specific cleanup models** | Searched HF for "transcript cleaning / STT cleanup / dictation correction" at sub-2 B — nothing credible. A system-prompted general instruct model remains the right tool. |
| **Distill our own 500M model** | Right long-term move (KD-LoRA retains ~98 % teacher on GLUE[^kd-lora]) but 20+ h of data curation + training. Revisit once the stack stabilizes. |

## Projected budget after P1–P4

| Stage | Current | After |
|---|---|---|
| STT (Moonshine ONNX CPU) | ~100 ms | ~100 ms |
| Pre-polish (SymSpell + dict) | — | ~30 ms |
| Polish LLM (LFM2-1.2B Q4, `llama-server`, cache warm, 50 tok @ ~100 tok/s) | 1500–5000 ms | **~500 ms** |
| Skip-polish fast path | 1500+ ms | ~0 ms |
| Paste / inject (streamed) | 50 ms | **perceived 0 ms** |
| **End-to-end wall clock** | ~2 s | **~630 ms** |
| **Perceived TTFT** | ~2 s | **~200 ms** |

Hits the <700 ms target on typical 3-sec dictations while keeping (arguably improving) homophone-correction quality via the explicit dictionary.

## Touch list for next session

- `localflow/core/polish/dictionary.py` (new) — P1
- `localflow/core/polish/llamacpp.py` — rewrite to `llama-server` HTTP + streaming — P3, P4
- `localflow/core/inject/linux_x11.py` — add streaming-type mode — P4
- `localflow/app.py` — gate `skip_if_clean`, streaming flag — P2
- `config/default.yaml` — `polish.skip_if_clean`, `polish.dictionary_path`, `inject.stream`
- `scripts/download_models.py` — add Qwen3-1.7B entry

## Sources

[^wispr-baseten]: [Wispr Flow on Baseten — <700 ms p99, <250 ms LLM](https://www.baseten.co/resources/customers/wispr-flow/)
[^wispr-voibe]: [Wispr Flow review — cloud-only](https://www.getvoibe.com/resources/wispr-flow-review/)
[^smollm-bench]: [SmolLM2-1.7B Q8 on Ryzen 5900X: 22.5 tok/s](https://openbenchmarking.org/test/pts/llama-cpp)
[^superwhisper]: [Superwhisper vs Wispr Flow review](https://willowvoice.com/blog/super-whisper-vs-wispr-flow-comparison-reviews-and-alternatives-in-2025)
[^blazing]: [Blazing Transcribe — ~530 ms, no polish LLM](https://www.blazingfasttranscription.com/blog/superwhisper-vs-wispr-flow)
[^cache-13606]: [llama.cpp KV cache-reuse tutorial #13606](https://github.com/ggml-org/llama.cpp/discussions/13606)
[^cache-20574]: [llama.cpp host-memory prompt caching #20574](https://github.com/ggml-org/llama.cpp/discussions/20574)
[^quant-overview]: [GGUF quant quality overview (Artefact2)](https://gist.github.com/Artefact2/b5f810600771265fc1e39442288e8ec9)
[^voxd]: [VOXD — streaming-type dictation for Linux](https://github.com/rdoiron/voxd-plus)
[^spec-docs]: [llama.cpp speculative decoding docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
[^spec-10466]: [Speculative decoding benchmarks discussion #10466](https://github.com/ggml-org/llama.cpp/discussions/10466)
[^tunney]: [Justine Tunney's CPU matmul speedups](https://justine.lol/matmul/)
[^flash-7209]: [FlashAttention on CPU — no text-gen win #7209](https://github.com/ggml-org/llama.cpp/discussions/7209)
[^coedit]: [flan-t5-large-grammar-synthesis](https://huggingface.co/pszemraj/flan-t5-large-grammar-synthesis)
[^kd-lora]: [KD-LoRA paper — 98 % teacher retention](https://arxiv.org/abs/2410.20777)
[^symspell]: [SymSpell — sub-ms fuzzy correction](https://github.com/wolfgarbe/SymSpell)
[^symspellpy]: [symspellpy](https://github.com/mammothb/symspellpy)
[^lfm2-report]: [LFM2 tech report (arXiv 2511.23404) — Ryzen HX 370 benchmarks](https://arxiv.org/html/2511.23404v1)
[^llama-cpp-python-2073]: [llama-cpp-python discussion #2073 — Python-side tokenization cost on short prompts](https://github.com/abetlen/llama-cpp-python/discussions/2073)
[^kv-5932]: [llama.cpp discussion #5932 — KV cache quantization tradeoffs](https://github.com/ggml-org/llama.cpp/discussions/5932)
[^openvino]: [llama.cpp OpenVINO backend — Intel-targeted](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENVINO.md)
[^ik-llama]: [ik_llama.cpp CPU perf discussion #164](https://github.com/ikawrakow/ik_llama.cpp/discussions/164)
[^gemma-270m]: [Gemma 3 270M launch](https://developers.googleblog.com/en/introducing-gemma-3-270m/)
[^gemma-3n]: [Gemma 3n docs (Unsloth)](https://docs.unsloth.ai/models/gemma-3-how-to-run-and-fine-tune/gemma-3n-how-to-run-and-fine-tune)
[^gemma-4-gguf]: [unsloth/gemma-4-E2B-it-GGUF](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF)
[^gemma-4-blog]: [Welcome Gemma 4 — HF blog](https://huggingface.co/blog/gemma4)
[^small-2026]: [Small LLM CPU benchmarks 2026](https://localaimaster.com/blog/small-language-models-guide-2026)
[^ollama-morph]: [llama.cpp vs Ollama comparison — Morph](https://www.morphllm.com/comparisons/llama-cpp-vs-ollama)
[^ollama-mitkox]: [DeepSeek-R1-Distill-1.5B llama.cpp vs Ollama benchmark](https://huggingface.co/posts/mitkox/389008233017077)
[^ollama-nullmirror]: [Switching from Ollama to llama.cpp (Nov 2025)](https://nullmirror.com/en/blog/2025-11-02-switching-our-inference-backend-from-ollama-to-llama.cpp/)
[^ollama-newengine]: [Ollama new engine — issue #9959](https://github.com/ollama/ollama/issues/9959)
