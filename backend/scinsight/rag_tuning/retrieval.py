"""Ranking stage shared by live search and the tuning console (one implementation, so a preview equals production).

semantic  cosine similarity of the query and chunk embeddings (pgvector computes it in SQL when available)
keyword   share of the query's content words found in the chunk (deterministic, no index needed)
hybrid    alpha * semantic + (1 - alpha) * keyword
rerank    lexical: re-orders candidates by keyword overlap, ties broken by the first-stage score (no model download)
"""
from __future__ import annotations

import json
import re

from backend.scinsight.rag_tuning.config import RagTuningConfig

STOP = {"the", "a", "an", "of", "to", "and", "or", "is", "are", "be", "for", "in", "on", "at", "by", "with", "what", "who", "which", "when",
        "how", "must", "can", "may", "do", "does", "it", "this", "that", "we", "our", "from", "without", "any", "should"}


def terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9-]*", text.lower()) if t not in STOP and len(t) > 1}


def keyword_score(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    words = terms(text)
    # prefix match so "approve" finds "approved" / "approval"
    hit = sum(1 for q in query_terms if q in words or any(w.startswith(q[:6]) for w in words if len(q) >= 5))
    return hit / len(query_terms)


def rank(rows: list[dict], qvec: list[float], query: str, cfg: RagTuningConfig) -> list[dict]:
    """Score and order chunk rows; returns copies with semantic / keyword / rerank / score fields, best first."""
    q = terms(query)
    out = []
    for r in rows:
        r = dict(r)
        if r.get("score") is None or cfg.retrieval_mode != "semantic":  # SQL already computed the cosine for pgvector rows
            vec = json.loads(r["embedding"]) if isinstance(r["embedding"], str) else r["embedding"]
            r["score"] = sum(a * b for a, b in zip(qvec, vec, strict=True)) if len(vec) == len(qvec) else -1.0
        r["semantic"] = float(r["score"])
        r["keyword"] = keyword_score(q, r["text"])
        r["score"] = {"semantic": r["semantic"], "keyword": r["keyword"],
                      "hybrid": cfg.hybrid_alpha * r["semantic"] + (1 - cfg.hybrid_alpha) * r["keyword"]}[cfg.retrieval_mode]
        r["rerank"] = None
        out.append(r)
    out.sort(key=lambda r: -r["score"])
    if cfg.rerank == "lexical":
        head, tail = out[:cfg.candidate_k], out[cfg.candidate_k:]
        for r in head:
            r["rerank"] = r["keyword"]
        head.sort(key=lambda r: (-r["rerank"], -r["score"]))
        out = head + tail
    return out
