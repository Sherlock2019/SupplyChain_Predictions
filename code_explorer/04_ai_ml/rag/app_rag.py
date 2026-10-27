# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/rag.py
# What this module is: the governed RAG of the SPARC gateway (contracts, SOPs, quality, product specs, logistics policies in
# data/knowledge): embedders (fastembed bge-small or offline hash), markdown chunking by "##" section, a keyword boost for SAP codes,
# and two stores — in-memory (tests) and PostgreSQL + pgvector with an HNSW index (deployments). Also provides the embedder shared
# with the SCInsight RAG (scinsight/rag.make_embedder) and the gateway's OpenAI-compatible /v1/embeddings endpoint.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Governed RAG: approved contracts, SOPs, quality policies, product specs and logistics policies.

Embeddings: fastembed BAAI/bge-small-en-v1.5 (384-d, CPU/ONNX) in every real deployment; a hashed
bag-of-words embedder is kept only for offline unit tests. Storage: pgvector (local Compose, RDS, Cloud SQL)
or an in-memory index for tests.
"""
from __future__ import annotations

import hashlib
import math
import re
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

# bge-small produces 384-dimensional vectors.
DIMENSIONS = 384
# SAP-like codes in a query (e.g. FG-PERFUME-100) or 8-10 digit document numbers get a small score boost when the chunk contains them.
CODE_TOKEN = re.compile(r"\b[A-Z]{1,4}-[A-Z0-9-]{2,}\b|\b\d{8,10}\b")


# ===== CLASS: HashEmbedder =====
# ID: F0731 · class · used
# ORIGINAL FILE: backend/app/rag.py:21-35
# ROLE: Deterministic offline embedder (hashed bag of words, unit length) for tests without a model download.
# FIELDS:
#   name: str.
# CALLED BY:
#   <- F0737 get_embedder() (calls)
#   <- F0744 MemoryRag.__init__() (calls)
#   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
#   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
# CALLS:
#   (none found)
class HashEmbedder:
    name = "hash-bow-384"

    # ===== FUNCTION: HashEmbedder.embed() =====
    # ID: F0732 · method · used
    # ORIGINAL FILE: backend/app/rag.py:24-25
    # ROLE: Embed several texts.
    # INPUTS:
    #   texts: list[str].
    # OUTPUT:
    #   list[list[float]].
    # CALLED BY:
    #   <- F0745 MemoryRag.add() (calls)
    #   <- F0746 MemoryRag.search() (calls)
    #   <- F0752 PgVectorRag.add() (calls)
    #   <- F0755 PgVectorRag.search() (calls)
    #   <- F0765 KnowledgeBase.ingest_dir() (calls)
    #   <- F0766 KnowledgeBase.search() (calls)
    # CALLS:
    #   -> F0733 HashEmbedder._one() (calls)
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    # ===== FUNCTION: HashEmbedder._one() =====
    # ID: F0733 · method · used
    # ORIGINAL FILE: backend/app/rag.py:27-35
    # ROLE: Embed one text: each token hashed to one of 384 slots with a +/-1 sign, then L2-normalised.
    # INPUTS:
    #   text: str.
    # OUTPUT:
    #   list[float].
    # CALLED BY:
    #   <- F0732 HashEmbedder.embed() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _one(text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for token in re.findall(r"[a-z0-9-]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:2], "big") % DIMENSIONS
            vector[index] += -1.0 if digest[2] & 1 else 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


# ===== CLASS: FastEmbedder =====
# ID: F0734 · class · used
# ORIGINAL FILE: backend/app/rag.py:38-48
# ROLE: Real embedder: fastembed (ONNX, CPU) running BAAI/bge-small-en-v1.5; a lock serialises calls (the model is not thread-safe).
# FIELDS:
#   name: str (model name), _model: TextEmbedding, _lock: threading.Lock.
# CALLED BY:
#   <- F0737 get_embedder() (calls)
#   <- F0950 test_fastembed_semantic_retrieval() (calls)
# CALLS:
#   (none found)
class FastEmbedder:
    # ===== FUNCTION: FastEmbedder.__init__() =====
    # ID: F0735 · method · used (framework)
    # ORIGINAL FILE: backend/app/rag.py:39-44
    # ROLE: Load the model (downloaded on first use, then cached).
    # INPUTS:
    #   model: str.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, model: str):
        from fastembed import TextEmbedding

        self.name = model
        self._model = TextEmbedding(model)
        self._lock = threading.Lock()

    # ===== FUNCTION: FastEmbedder.embed() =====
    # ID: F0736 · method · used
    # ORIGINAL FILE: backend/app/rag.py:46-48
    # ROLE: Embed texts (numpy arrays converted to lists).
    # INPUTS:
    #   texts: list[str].
    # OUTPUT:
    #   list[list[float]].
    # CALLED BY:
    #   <- F0745 MemoryRag.add() (calls)
    #   <- F0746 MemoryRag.search() (calls)
    #   <- F0752 PgVectorRag.add() (calls)
    #   <- F0755 PgVectorRag.search() (calls)
    #   <- F0765 KnowledgeBase.ingest_dir() (calls)
    #   <- F0766 KnowledgeBase.search() (calls)
    # CALLS:
    #   (none found)
    def embed(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            return [vector.tolist() for vector in self._model.embed(texts)]


# Process-wide embedder cache (one loaded model per backend:model).
_embedders: dict[str, object] = {}


# ===== FUNCTION: get_embedder() =====
# ID: F0737 · function · used
# ORIGINAL FILE: backend/app/rag.py:54-58
# ROLE: Return the cached embedder for (backend, model), creating it once. Shared by the gateway RAG, /v1/embeddings and SCInsight.
# INPUTS:
#   backend: str ("fastembed" | anything else -> hash), model: str.
# OUTPUT:
#   FastEmbedder | HashEmbedder.
# CALLED BY:
#   <- F0756 create_rag() (calls)
#   <- F0762 make_embedder() (calls)
# CALLS:
#   -> F0734 FastEmbedder (calls)
#   -> F0731 HashEmbedder (calls)
def get_embedder(backend: str = "fastembed", model: str = "BAAI/bge-small-en-v1.5"):
    key = f"{backend}:{model}"
    if key not in _embedders:
        _embedders[key] = FastEmbedder(model) if backend == "fastembed" else HashEmbedder()
    return _embedders[key]


# ===== FUNCTION: cosine() =====
# ID: F0738 · function · used
# ORIGINAL FILE: backend/app/rag.py:61-62
# ROLE: Cosine similarity of two unit-length vectors (= dot product).
# INPUTS:
#   left, right: list[float].
# OUTPUT:
#   float.
# CALLED BY:
#   <- F0746 MemoryRag.search() (calls)
# CALLS:
#   (none found)
def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


# ===== FUNCTION: chunk_markdown() =====
# ID: F0739 · function · used
# ORIGINAL FILE: backend/app/rag.py:65-87
# ROLE: Split a markdown document on "##" headings; each chunk starts with "<title> — <section>" for context.
# INPUTS:
#   title: str, text: str.
# OUTPUT:
#   list[str] (at least one chunk).
# CALLED BY:
#   <- F0745 MemoryRag.add() (calls)
#   <- F0752 PgVectorRag.add() (calls)
#   <- F0947 test_chunking_keeps_title_and_section() (calls)
# CALLS:
#   -> F0740 chunk_markdown.flush() (calls)
def chunk_markdown(title: str, text: str) -> list[str]:
    """Split on second-level headings; each chunk carries the document title and section for context."""
    heading = title
    lines = text.strip().splitlines()
    # A leading "# Title" line replaces the file-name title.
    if lines and lines[0].startswith("# "):
        heading = lines[0][2:].strip()
        lines = lines[1:]
    chunks: list[str] = []
    section, buffer = "", []

    # ===== FUNCTION: chunk_markdown.flush() =====
    # ID: F0740 · nested · used
    # ORIGINAL FILE: backend/app/rag.py:75-78
    # ROLE: Close the current section into a chunk (closure over chunks / heading / section / buffer).
    # INPUTS:
    #   none.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0739 chunk_markdown() (calls)
    # CALLS:
    #   (none found)
    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            chunks.append(f"{heading}{' — ' + section if section else ''}\n{body}")

    for line in lines:
        if line.startswith("## "):
            flush()
            section, buffer = line[3:].strip(), []
        else:
            buffer.append(line)
    flush()
    return chunks or [f"{heading}\n{text.strip()}"]


# ===== FUNCTION: keyword_boost() =====
# ID: F0741 · function · used
# ORIGINAL FILE: backend/app/rag.py:90-94
# ROLE: +0.08 score per SAP code of the query that literally appears in the chunk (exact codes matter more than semantics).
# INPUTS:
#   query: str, text: str.
# OUTPUT:
#   float.
# CALLED BY:
#   <- F0746 MemoryRag.search() (calls)
#   <- F0755 PgVectorRag.search() (calls)
#   <- F0948 test_keyword_boost_rewards_exact_sap_codes() (calls)
# CALLS:
#   (none found)
def keyword_boost(query: str, text: str) -> float:
    codes = set(CODE_TOKEN.findall(query.upper()))
    if not codes:
        return 0.0
    return 0.08 * sum(1 for code in codes if code in text.upper())


# ===== CLASS: Chunk =====
# ID: F0742 · class · used
# ORIGINAL FILE: backend/app/rag.py:97-104
# ROLE: One stored chunk of the in-memory index.
# FIELDS:
#   id, title, category, source, text: str; vector: list[float].
# CALLED BY:
#   <- F0744 MemoryRag.__init__() (references)
#   <- F0745 MemoryRag.add() (calls)
# CALLS:
#   (none found)
@dataclass
class Chunk:
    id: str
    title: str
    category: str
    source: str
    text: str
    vector: list[float]


# ===== CLASS: MemoryRag =====
# ID: F0743 · class · used
# ORIGINAL FILE: backend/app/rag.py:107-136
# ROLE: In-memory RAG store (unit tests, laptops without PostgreSQL).
# FIELDS:
#   backend = "memory", embedder, chunks: list[Chunk].
# CALLED BY:
#   <- F0483 build_backend() (calls)
#   <- F0756 create_rag() (calls)
#   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
#   <- F0950 test_fastembed_semantic_retrieval() (calls)
# CALLS:
#   (none found)
class MemoryRag:
    backend = "memory"

    # ===== FUNCTION: MemoryRag.__init__() =====
    # ID: F0744 · method · used (framework)
    # ORIGINAL FILE: backend/app/rag.py:110-112
    # ROLE: Create an empty index.
    # INPUTS:
    #   embedder (default HashEmbedder).
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0731 HashEmbedder (calls)
    #   -> F0742 Chunk (references)
    def __init__(self, embedder=None):
        self.embedder = embedder or HashEmbedder()
        self.chunks: list[Chunk] = []

    # ===== FUNCTION: MemoryRag.add() =====
    # ID: F0745 · method · used
    # ORIGINAL FILE: backend/app/rag.py:114-118
    # ROLE: Chunk, embed and store one document.
    # INPUTS:
    #   title, category, source, text: str.
    # OUTPUT:
    #   int -> number of chunks added.
    # CALLED BY:
    #   <- F0081 create_app.rag_add() (calls)
    #   <- F0748 MemoryRag.load_directory() (calls)
    # CALLS:
    #   -> F0739 chunk_markdown() (calls)
    #   -> F0736 FastEmbedder.embed() (calls)
    #   -> F0732 HashEmbedder.embed() (calls)
    #   -> F0761 HashEmbedder.embed() (calls)
    #   -> F0742 Chunk (calls)
    def add(self, title: str, category: str, source: str, text: str) -> int:
        parts = chunk_markdown(title, text)
        for part, vector in zip(parts, self.embedder.embed(parts), strict=True):
            self.chunks.append(Chunk(uuid.uuid4().hex, title, category, source, part, vector))
        return len(parts)

    # ===== FUNCTION: MemoryRag.search() =====
    # ID: F0746 · method · used
    # ORIGINAL FILE: backend/app/rag.py:120-128
    # ROLE: Top-k chunks by cosine similarity + keyword boost, optionally within one category.
    # INPUTS:
    #   query: str, top_k: int, category: str | None.
    # OUTPUT:
    #   list[dict] -> {id, title, category, source, text, score}.
    # CALLED BY:
    #   <- F0464 LocalBackend.search_knowledge() (calls)
    #   <- F0076 create_app.rag_search() (calls)
    #   <- F0077 create_app.rag_search_get() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0950 test_fastembed_semantic_retrieval() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   -> F0736 FastEmbedder.embed() (calls)
    #   -> F0732 HashEmbedder.embed() (calls)
    #   -> F0761 HashEmbedder.embed() (calls)
    #   -> F0738 cosine() (calls)
    #   -> F0741 keyword_boost() (calls)
    def search(self, query: str, top_k: int = 4, category: str | None = None) -> list[dict]:
        query_vector = self.embedder.embed([query])[0]
        candidates = [chunk for chunk in self.chunks if category is None or chunk.category == category]
        scored = [(cosine(query_vector, chunk.vector) + keyword_boost(query, chunk.text), chunk) for chunk in candidates]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"id": chunk.id, "title": chunk.title, "category": chunk.category, "source": chunk.source, "text": chunk.text, "score": round(score, 4)}
            for score, chunk in scored[:top_k]
        ]

    # ===== FUNCTION: MemoryRag.stats() =====
    # ID: F0747 · method · used
    # ORIGINAL FILE: backend/app/rag.py:130-131
    # ROLE: Index statistics.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict -> backend, embedding_model, chunks, documents.
    # CALLED BY:
    #   <- F0026 create_app.ready() (calls)
    #   <- F0031 create_app.status() (calls)
    #   <- F0080 create_app.rag_stats() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   (none found)
    def stats(self) -> dict:
        return {"backend": self.backend, "embedding_model": self.embedder.name, "chunks": len(self.chunks), "documents": len({c.title for c in self.chunks})}

    # ===== FUNCTION: MemoryRag.load_directory() =====
    # ID: F0748 · method · used
    # ORIGINAL FILE: backend/app/rag.py:133-136
    # ROLE: Index every *.md of a folder; category = file-name prefix before "__" (e.g. contract__aromachem.md -> "contract").
    # INPUTS:
    #   directory: Path.
    # OUTPUT:
    #   int -> chunks added.
    # CALLED BY:
    #   <- F0483 build_backend() (calls)
    #   <- F0756 create_rag() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0950 test_fastembed_semantic_retrieval() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   -> F0745 MemoryRag.add() (calls)
    def load_directory(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(self.add(path.stem, path.stem.split("__", 1)[0], f"knowledge/{path.name}", path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.md")))


# ===== CLASS: PgVectorRag =====
# ID: F0749 · class · used
# ORIGINAL FILE: backend/app/rag.py:139-221
# ROLE: PostgreSQL + pgvector RAG store: table rag_chunk with a vector(384) column and an HNSW cosine index.
# FIELDS:
#   backend = "pgvector", database_url, embedder.
# CALLED BY:
#   <- F0756 create_rag() (calls)
#   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
# CALLS:
#   (none found)
class PgVectorRag:
    backend = "pgvector"

    # ===== FUNCTION: PgVectorRag.__init__() =====
    # ID: F0750 · method · used (framework)
    # ORIGINAL FILE: backend/app/rag.py:142-157
    # ROLE: Create the extension, table, columns and indexes if missing (idempotent DDL).
    # INPUTS:
    #   database_url: str, embedder.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, database_url: str, embedder):
        import psycopg

        self.database_url = database_url
        self.embedder = embedder
        with psycopg.connect(database_url, autocommit=True) as connection, connection.cursor() as cursor:
            cursor.execute("create extension if not exists vector")
            cursor.execute(
                f"""create table if not exists rag_chunk(
                id uuid primary key, title text not null, category text not null, source text not null,
                content text not null, embedding vector({DIMENSIONS}) not null, embedding_model text not null default 'unknown',
                created_at timestamptz default now())"""
            )
            cursor.execute("alter table rag_chunk add column if not exists embedding_model text not null default 'unknown'")
            cursor.execute("create index if not exists rag_chunk_category on rag_chunk(category)")
            # HNSW = approximate nearest-neighbour index for fast cosine search.
            cursor.execute("create index if not exists rag_chunk_hnsw on rag_chunk using hnsw (embedding vector_cosine_ops)")

    # ===== FUNCTION: PgVectorRag._connect() =====
    # ID: F0751 · method · used
    # ORIGINAL FILE: backend/app/rag.py:159-165
    # ROLE: New connection with the pgvector type adapter registered (numpy arrays <-> vector).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   psycopg.Connection.
    # CALLED BY:
    #   <- F0752 PgVectorRag.add() (calls)
    #   <- F0753 PgVectorRag.stats() (calls)
    #   <- F0754 PgVectorRag.load_directory() (calls)
    #   <- F0755 PgVectorRag.search() (calls)
    # CALLS:
    #   (none found)
    def _connect(self):
        import psycopg
        from pgvector.psycopg import register_vector

        connection = psycopg.connect(self.database_url)
        register_vector(connection)
        return connection

    # ===== FUNCTION: PgVectorRag.add() =====
    # ID: F0752 · method · used
    # ORIGINAL FILE: backend/app/rag.py:167-179
    # ROLE: Chunk, embed and insert one document (optionally inside the caller's cursor / transaction).
    # INPUTS:
    #   title, category, source, text: str; cursor (optional).
    # OUTPUT:
    #   int -> chunks inserted.
    # CALLED BY:
    #   <- F0081 create_app.rag_add() (calls)
    #   <- F0754 PgVectorRag.load_directory() (calls)
    # CALLS:
    #   -> F0739 chunk_markdown() (calls)
    #   -> F0736 FastEmbedder.embed() (calls)
    #   -> F0732 HashEmbedder.embed() (calls)
    #   -> F0761 HashEmbedder.embed() (calls)
    #   -> F0424 Database.executemany() (calls)
    #   -> F0751 PgVectorRag._connect() (calls)
    def add(self, title: str, category: str, source: str, text: str, cursor=None) -> int:
        import numpy as np

        parts = chunk_markdown(title, text)
        vectors = self.embedder.embed(parts)
        rows = [(uuid.uuid4(), title, category, source, part, np.array(vector), self.embedder.name) for part, vector in zip(parts, vectors, strict=True)]
        sql = "insert into rag_chunk(id,title,category,source,content,embedding,embedding_model) values(%s,%s,%s,%s,%s,%s,%s)"
        if cursor is not None:
            cursor.executemany(sql, rows)
        else:
            with self._connect() as connection, connection.cursor() as own:
                own.executemany(sql, rows)
        return len(parts)

    # ===== FUNCTION: PgVectorRag.stats() =====
    # ID: F0753 · method · used
    # ORIGINAL FILE: backend/app/rag.py:181-185
    # ROLE: Index statistics from the table.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0026 create_app.ready() (calls)
    #   <- F0031 create_app.status() (calls)
    #   <- F0080 create_app.rag_stats() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   -> F0751 PgVectorRag._connect() (calls)
    def stats(self) -> dict:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("select count(*), count(distinct title) from rag_chunk")
            chunks, documents = cursor.fetchone()
        return {"backend": self.backend, "embedding_model": self.embedder.name, "chunks": int(chunks), "documents": int(documents)}

    # ===== FUNCTION: PgVectorRag.load_directory() =====
    # ID: F0754 · method · used
    # ORIGINAL FILE: backend/app/rag.py:187-202
    # ROLE: Index the approved corpus once; re-index everything when the embedding model changed (under an advisory lock).
    # INPUTS:
    #   directory: Path.
    # OUTPUT:
    #   int -> chunks added (0 when already up to date).
    # CALLED BY:
    #   <- F0483 build_backend() (calls)
    #   <- F0756 create_rag() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0950 test_fastembed_semantic_retrieval() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   -> F0751 PgVectorRag._connect() (calls)
    #   -> F0752 PgVectorRag.add() (calls)
    def load_directory(self, directory: Path) -> int:
        """Index the approved corpus once; re-index everything if the embedding model changed."""
        if not directory.exists():
            return 0
        with self._connect() as connection, connection.cursor() as cursor:
            # API, MCP and LangGraph start together; one transaction-scoped lock makes indexing happen once.
            cursor.execute("select pg_advisory_xact_lock(7316001)")
            # count(*) filter (where ...) = conditional count in PostgreSQL.
            cursor.execute("select count(*) filter (where embedding_model=%s), count(*) from rag_chunk", (self.embedder.name,))
            current, total = cursor.fetchone()
            if total and current == total:
                return 0
            # "%%" is a literal % in a psycopg query string (LIKE 'knowledge/%').
            cursor.execute("delete from rag_chunk where source like 'knowledge/%%' or embedding_model<>%s", (self.embedder.name,))
            return sum(
                self.add(path.stem, path.stem.split("__", 1)[0], f"knowledge/{path.name}", path.read_text(encoding="utf-8"), cursor)
                for path in sorted(directory.glob("*.md"))
            )

    # ===== FUNCTION: PgVectorRag.search() =====
    # ID: F0755 · method · used
    # ORIGINAL FILE: backend/app/rag.py:204-221
    # ROLE: Top-k by pgvector cosine distance (<=>), fetching 3x top_k then re-ranking with the keyword boost.
    # INPUTS:
    #   query: str, top_k: int, category: str | None.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0464 LocalBackend.search_knowledge() (calls)
    #   <- F0076 create_app.rag_search() (calls)
    #   <- F0077 create_app.rag_search_get() (calls)
    #   <- F0949 test_memory_rag_finds_category_and_injection_text_is_just_data() (calls)
    #   <- F0950 test_fastembed_semantic_retrieval() (calls)
    #   <- F0954 test_postgres_store_and_pgvector_rag() (calls)
    # CALLS:
    #   -> F0736 FastEmbedder.embed() (calls)
    #   -> F0732 HashEmbedder.embed() (calls)
    #   -> F0761 HashEmbedder.embed() (calls)
    #   -> F0751 PgVectorRag._connect() (calls)
    #   -> F0741 keyword_boost() (calls)
    def search(self, query: str, top_k: int = 4, category: str | None = None) -> list[dict]:
        import numpy as np

        vector = np.array(self.embedder.embed([query])[0])
        where = "where category=%s" if category else ""
        # Parameter order follows the placeholders: score vector, [category], order-by vector, limit.
        params: list = [vector] + ([category] if category else []) + [vector, top_k * 3]
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"select id,title,category,source,content,1-(embedding <=> %s) score from rag_chunk {where} order by embedding <=> %s limit %s",
                params,
            )
            rows = cursor.fetchall()
        results = [
            {"id": str(row[0]), "title": row[1], "category": row[2], "source": row[3], "text": row[4], "score": round(float(row[5]) + keyword_boost(query, row[4]), 4)}
            for row in rows
        ]
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]


# ===== FUNCTION: create_rag() =====
# ID: F0756 · function · used
# ORIGINAL FILE: backend/app/rag.py:224-228
# ROLE: Factory used by create_app(): choose the store ("pgvector" or memory), then index the knowledge folder.
# INPUTS:
#   backend: str, postgres_url: str, knowledge_dir: Path, embedding_backend: str, embedding_model: str.
# OUTPUT:
#   MemoryRag | PgVectorRag.
# CALLED BY:
#   <- F0483 build_backend() (calls)
#   <- F0017 create_app() (calls)
# CALLS:
#   -> F0737 get_embedder() (calls)
#   -> F0749 PgVectorRag (calls)
#   -> F0743 MemoryRag (calls)
#   -> F0748 MemoryRag.load_directory() (calls)
#   -> F0754 PgVectorRag.load_directory() (calls)
def create_rag(backend: str, postgres_url: str, knowledge_dir: Path, embedding_backend: str = "fastembed", embedding_model: str = "BAAI/bge-small-en-v1.5"):
    embedder = get_embedder(embedding_backend, embedding_model)
    repository = PgVectorRag(postgres_url, embedder) if backend == "pgvector" else MemoryRag(embedder)
    repository.load_directory(knowledge_dir)
    return repository
