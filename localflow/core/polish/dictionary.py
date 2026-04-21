"""Deterministic pre-polish: homophone map + filler-word stripping.

Runs before the LLM. Fast (<10 ms), reliable, and reviewable. Handles the
STT errors that an LLM can only guess at from context (e.g. "lump" -> "LLM")
with a user-editable dictionary instead.
"""
from __future__ import annotations

import re

# Case-insensitive match; canonical-case replacement.
# Order within this dict doesn't matter — no overlapping patterns.
_HOMOPHONES: dict[str, str] = {
    # LLM / AI tools
    r"\blump\b": "LLM",
    r"\bjason\b": "JSON",
    r"\ba\s*p\s*i\b": "API",
    r"\bu\s*r\s*l\b": "URL",
    r"\bs\s*d\s*k\b": "SDK",
    r"\bclawed\b": "Claude",
    r"\bclod\b": "Claude",
    r"\bchat\s*g\s*p\s*(t|d)\b": "ChatGPT",
    r"\bjet\s*p\s*t\b": "ChatGPT",
    r"\bget\s*hub\b": "GitHub",
    # Products / proper nouns
    r"\bmac\s*book\b": "MacBook",
    r"\bmack\s*book\b": "MacBook",
    r"\bvs\s*code\b": "VS Code",
    # Programming languages (lowercase as spoken -> canonical)
    r"\bpython\b": "Python",
    r"\bjavascript\b": "JavaScript",
    r"\btypescript\b": "TypeScript",
    r"\bnode\s*js\b": "Node.js",
    r"\breact\s*js\b": "React",
}

# Literal filler phrases. Multi-word first (so "like you know" goes before "like").
_FILLERS: list[str] = [
    r"\blike\s+you\s+know\b",
    r"\byou\s+know\b",
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bahm+\b",
]


def pre_polish(text: str) -> str:
    out = text
    for pattern, replacement in _HOMOPHONES.items():
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    for pattern in _FILLERS:
        out = re.sub(pattern, "", out, flags=re.IGNORECASE)
    # collapse whitespace + strip
    out = re.sub(r"\s+", " ", out).strip()
    # lift sentence-initial capitalization if STT produced lowercase
    if out and out[0].isalpha() and not out[0].isupper():
        out = out[0].upper() + out[1:]
    return out
