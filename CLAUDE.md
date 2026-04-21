# CLAUDE.md — project guide for Claude Code

This file orients Claude Code for the `localflow` project. Read this before touching code.

## What this project is

A fully-local, cross-platform (Linux + macOS) voice dictation tool. Reference implementation / clone of Wispr Flow's UX — press hotkey, speak, polished text appears at cursor — running entirely on-device.

See [`README.md`](./README.md) for the user-facing pitch and [`knowledge-base/architecture.md`](./knowledge-base/architecture.md) for the stack.

## Session protocol

This project uses a persistent `SESSION.md` file to track state across Claude Code sessions.

- **At start of session:** user types `/start` — read `SESSION.md`, brief them on current state, ask what to work on.
- **At end of session:** user types `/end` — update `SESSION.md`, commit, and push.
- Commands live at `.claude/commands/start.md` and `.claude/commands/end.md`.
- `SESSION.md` is the source of truth for "where are we?". Keep it current.

## Knowledge base

All non-trivial research — model comparisons, benchmark notes, design decisions — goes under `knowledge-base/`. One file per topic. This is the durable memory of the project; prefer adding to it over putting long prose in chat.

## Engineering principles

- **Keep it small.** No speculative abstractions. No features beyond what the current milestone needs. Three similar lines beats a premature interface.
- **No half-finished code.** Don't scaffold empty modules "for later." Create a file only when implementing it. Stubs rot fast.
- **Latency is the product.** Every optimization that shaves 50 ms off end-to-end is worth considering. Every feature that costs 50 ms needs justification.
- **Pluggable backends, not abstract kingdoms.** STT / polish / inject each have a simple base class + platform-specific impls. No registry, no DI framework.
- **Comments:** default to none. Only write a comment when the *why* is non-obvious.

## Hardware targets (read this before model selection)

Owner runs two machines:

- **Linux laptop** — Ryzen 9 5900HX, 24 GB RAM, **RTX 3050 Laptop with only 4 GB VRAM**, Ubuntu 22.04 X11. The 4 GB VRAM is the binding constraint on model choices.
- **MacBook Air M5** — 32 GB unified memory. MLX is the preferred inference framework (20–50 % faster than llama.cpp on Apple Silicon as of 2026).

Model sizing rule: STT → GPU (latency-critical), polish LLM → wherever fits. On Linux that often means STT on GPU + LLM on CPU.

## Layout

```
localflow/
├── localflow/          # Python package (source)
│   ├── core/           # pipeline, capture, vad, hotkey
│   │   ├── stt/        # STT backends (moonshine_onnx, moonshine_mlx, ...)
│   │   ├── polish/     # LLM polish backends (llamacpp, mlx)
│   │   └── inject/     # text injection (linux_x11, macos, clipboard)
│   └── app.py          # entry point
├── config/default.yaml
├── scripts/            # model download, benchmarks
├── knowledge-base/     # research + design docs (durable)
├── tests/
├── SESSION.md          # running project state
├── CLAUDE.md           # this file
└── README.md
```

## Git workflow

- Commit at the end of every session via `/end`.
- Prefer small, frequent commits over mega-commits.
- Commit messages follow Conventional Commits loosely (`feat:`, `fix:`, `docs:`, `chore:`).
- Push to `origin/main`. No PR workflow for solo development.

## Things to never do without asking

- Add a cloud dependency (defeats the whole point of the project).
- Pin a specific model's weights in the repo (> 100 MB). Use `scripts/download_models.py` instead.
- Expand scope beyond the current milestone in `SESSION.md`.
- Skip updating `SESSION.md` at `/end`.
