"""Splitters for the governed documents. Sizes are characters.

section  split on '## ' headings, then fixed windows inside each section (the original SCInsight splitter: identical output
         for the baseline 900 / 120 configuration)
fixed    fixed windows over the whole document, ignoring headings (the heading in force is still recorded)
clause   inside each section, whole sentences are packed up to the chunk size and the overlap is made of whole trailing
         sentences, so a condition and its approval rule are not cut apart unless one sentence is longer than the chunk
"""
from __future__ import annotations

import re

from backend.scinsight.rag_tuning.config import CHARS_PER_TOKEN, RagTuningConfig

SENTENCE_END = re.compile(r"(?<=[.!?:;])\s+(?=[A-Z0-9\"(])")


def _sections(body: str) -> list[tuple[str, str]]:
    # Same parsing as the original chunk_document: '## ' starts a section, the '# ' title line is dropped.
    sections, current, lines = [], "Overview", []
    for line in body.splitlines():
        if line.startswith("## "):
            if lines:
                sections.append((current, "\n".join(lines).strip()))
            current, lines = line[3:].strip(), []
        elif not line.startswith("# "):
            lines.append(line)
    if lines:
        sections.append((current, "\n".join(lines).strip()))
    return [(s, t) for s, t in sections if t]


def _windows(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    # Fixed character windows; the next window starts `size - overlap` characters later.
    spans, start = [], 0
    while start < len(text):
        spans.append((start, min(start + size, len(text))))
        if start + size >= len(text):
            break
        start += size - overlap
    return spans


def _clauses(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    # 1. sentence boundaries (keeps "Transfers are approved by the warehouse manager." whole)
    bounds, start = [], 0
    for m in SENTENCE_END.finditer(text):
        bounds.append((start, m.start()))
        start = m.end()
    bounds.append((start, len(text)))
    # 2. a sentence longer than the chunk is windowed (the only case where a sentence is cut)
    units = []
    for a, b in bounds:
        units += [(a + x, a + y) for x, y in _windows(text[a:b], size, overlap)] if b - a > size else [(a, b)]
    # 3. pack whole units up to `size`; the overlap is the longest run of trailing units that fits in `overlap`
    spans, i = [], 0
    while i < len(units):
        j = i
        while j + 1 < len(units) and units[j + 1][1] - units[i][0] <= size:
            j += 1
        spans.append((units[i][0], units[j][1]))
        if j + 1 >= len(units):
            break
        k = j + 1
        while k - 1 > i and units[j][1] - units[k - 1][0] <= overlap:
            k -= 1
        i = k
    return spans


def chunk(title: str, body: str, cfg: RagTuningConfig, doc_id: str = "", version: str = "") -> list[dict]:
    """Chunks of one document: [{chunk_index, section, text (as indexed), content (without prefix), start, end}]."""
    if cfg.chunk_strategy == "fixed":
        text = "\n".join(line for line in body.splitlines() if not line.startswith("# ")).strip()
        heads = [(m.start(), m.group(1).strip()) for m in re.finditer(r"^## (.+)$", text, re.M)]
        pieces = [("", text, a, b) for a, b in _windows(text, cfg.chunk_size, cfg.chunk_overlap)]
        pieces = [(next((h for pos, h in reversed(heads) if pos <= a), "Overview"), t, a, b) for _, t, a, b in pieces]
    else:
        split = _clauses if cfg.chunk_strategy == "clause" else _windows
        pieces = [(section, text, a, b) for section, text in _sections(body) for a, b in split(text, cfg.chunk_size, cfg.chunk_overlap)]
    out = []
    for i, (section, text, a, b) in enumerate(pieces):
        content = text[a:b].strip() if cfg.chunk_strategy == "clause" else text[a:b]
        prefix = (f"[{doc_id} v{version}] " if cfg.preserve_source_ids and doc_id else "") + (f"{title} — {section}\n" if cfg.preserve_headings else "")
        out.append({"chunk_index": i, "section": section, "text": prefix + content, "content": content, "start": a, "end": b})
    return out


def overlap_chars(left: str, right: str) -> int:
    """Characters at the end of `left` repeated at the start of `right` (what the overlap actually duplicated)."""
    for n in range(min(len(left), len(right)), 0, -1):
        if left.endswith(right[:n]):
            return n
    return 0


def preview_document_chunks(title: str, body: str, cfg: RagTuningConfig, doc_id: str, version: str) -> dict:
    """What the configuration would index for one document (nothing is written)."""
    chunks = chunk(title, body, cfg, doc_id, version)
    for i, c in enumerate(chunks):
        c["chunk_id"] = f"{doc_id}:{version}:{i}"
        c["chars"] = len(c["text"])
        c["approx_tokens"] = max(1, round(len(c["text"]) / CHARS_PER_TOKEN))
        same_section = i > 0 and chunks[i - 1]["section"] == c["section"]
        c["overlap_with_previous"] = overlap_chars(chunks[i - 1]["content"], c["content"]) if same_section else 0
    return {"doc_id": doc_id, "version": version, "unit": "characters", "config": cfg.model_dump(), "count": len(chunks),
            "avg_chars": round(sum(c["chars"] for c in chunks) / len(chunks)) if chunks else 0, "chunks": chunks}
