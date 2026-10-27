"""The tunable RAG configuration: one validated object per configuration version.

Units are explicit: chunk sizes are CHARACTERS (the splitters cut text, they do not tokenize); token counts shown in the
console are approximations (characters / 4). The similarity score is the cosine similarity of L2-normalised embeddings
(-1..1, higher = closer); it is model specific and is not a confidence or a probability.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CHUNK_UNIT = "characters"
SCORE_METRIC = "cosine similarity of normalised embeddings (-1..1); model specific, not a probability"
CHARS_PER_TOKEN = 4  # rough rule of thumb for English text; only used for the approximate token counts shown

# Which settings take effect at query time (hot) and which need a new index (cold).
HOT_FIELDS = ("top_k", "similarity_threshold", "retrieval_mode", "hybrid_alpha", "rerank", "candidate_k", "max_context_tokens", "category_filter")
COLD_FIELDS = ("chunk_strategy", "chunk_size", "chunk_overlap", "preserve_headings", "preserve_source_ids", "embedding_model")

PRESETS = {"small": {"chunk_size": 300, "chunk_overlap": 50}, "medium": {"chunk_size": 600, "chunk_overlap": 100},
           "large": {"chunk_size": 1000, "chunk_overlap": 150}}
TOP_K_PRESETS = (3, 5, 8)


class RagTuningConfig(BaseModel):
    """One RAG configuration version. Cold fields define the index; hot fields only change how it is queried."""
    model_config = ConfigDict(extra="forbid")

    # ---- index-building (cold): changing any of these needs a new index version
    chunk_strategy: Literal["section", "fixed", "clause"] = "section"  # section = split on '## ' headings, then windows
    chunk_size: int = Field(default=900, ge=50, le=4000)                # characters per chunk (window)
    chunk_overlap: int = Field(default=120, ge=0, le=2000)              # characters repeated between neighbouring windows
    preserve_headings: bool = True                                     # prefix each chunk with "title — section"
    preserve_source_ids: bool = False                                  # prefix each chunk with "[doc_id vX]"
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", min_length=3, max_length=120)

    # ---- query-time (hot): take effect without re-indexing
    top_k: int = Field(default=4, ge=1, le=10)                         # passages returned to the agent
    similarity_threshold: float | None = Field(default=None, ge=-1.0, le=1.0)  # None = no threshold (current behaviour)
    retrieval_mode: Literal["semantic", "keyword", "hybrid"] = "semantic"
    hybrid_alpha: float = Field(default=0.7, ge=0.0, le=1.0)           # weight of the semantic score in hybrid mode
    rerank: Literal["none", "lexical"] = "none"                        # lexical = deterministic query-term overlap reranker
    candidate_k: int = Field(default=16, ge=1, le=100)                 # candidates considered before access filtering / rerank
    max_context_tokens: int | None = Field(default=None, ge=50, le=8000)  # approximate token budget of the returned context
    category_filter: list[str] = Field(default_factory=list, max_length=20)  # restricts document categories (never widens access)

    @model_validator(mode="after")
    def validate_chunking(self) -> RagTuningConfig:
        # An overlap as large as the chunk would repeat whole chunks forever.
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be at least top_k")
        return self


def baseline_config(embedding_model: str) -> RagTuningConfig:
    """The configuration the service ran with before tuning existed (backend/scinsight/rag.py: 900/120 section chunks, top 4)."""
    return RagTuningConfig(embedding_model=embedding_model)


def diff(active: dict, candidate: dict) -> dict:
    """Changed settings, split into those that need a rebuild (cold) and those that apply at query time (hot)."""
    changed = {k: {"active": active.get(k), "candidate": candidate.get(k)} for k in candidate if active.get(k) != candidate.get(k)}
    return {"changed": changed, "rebuild_required": [k for k in changed if k in COLD_FIELDS],
            "query_time": [k for k in changed if k in HOT_FIELDS], "needs_new_index": any(k in COLD_FIELDS for k in changed)}


def index_signature(cfg: RagTuningConfig) -> dict:
    """The cold settings: two configurations with the same signature can share one index."""
    return {k: getattr(cfg, k) for k in COLD_FIELDS}
