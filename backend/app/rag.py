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

DIMENSIONS = 384
CODE_TOKEN = re.compile(r"\b[A-Z]{1,4}-[A-Z0-9-]{2,}\b|\b\d{8,10}\b")


class HashEmbedder:
    name = "hash-bow-384"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    @staticmethod
    def _one(text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        for token in re.findall(r"[a-z0-9-]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:2], "big") % DIMENSIONS
            vector[index] += -1.0 if digest[2] & 1 else 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class FastEmbedder:
    def __init__(self, model: str):
        from fastembed import TextEmbedding

        self.name = model
        self._model = TextEmbedding(model)
        self._lock = threading.Lock()

    def embed(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            return [vector.tolist() for vector in self._model.embed(texts)]


_embedders: dict[str, object] = {}


def get_embedder(backend: str = "fastembed", model: str = "BAAI/bge-small-en-v1.5"):
    key = f"{backend}:{model}"
    if key not in _embedders:
        _embedders[key] = FastEmbedder(model) if backend == "fastembed" else HashEmbedder()
    return _embedders[key]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def chunk_markdown(title: str, text: str) -> list[str]:
    """Split on second-level headings; each chunk carries the document title and section for context."""
    heading = title
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("# "):
        heading = lines[0][2:].strip()
        lines = lines[1:]
    chunks: list[str] = []
    section, buffer = "", []

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


def keyword_boost(query: str, text: str) -> float:
    codes = set(CODE_TOKEN.findall(query.upper()))
    if not codes:
        return 0.0
    return 0.08 * sum(1 for code in codes if code in text.upper())


@dataclass
class Chunk:
    id: str
    title: str
    category: str
    source: str
    text: str
    vector: list[float]


class MemoryRag:
    backend = "memory"

    def __init__(self, embedder=None):
        self.embedder = embedder or HashEmbedder()
        self.chunks: list[Chunk] = []

    def add(self, title: str, category: str, source: str, text: str) -> int:
        parts = chunk_markdown(title, text)
        for part, vector in zip(parts, self.embedder.embed(parts), strict=True):
            self.chunks.append(Chunk(uuid.uuid4().hex, title, category, source, part, vector))
        return len(parts)

    def search(self, query: str, top_k: int = 4, category: str | None = None) -> list[dict]:
        query_vector = self.embedder.embed([query])[0]
        candidates = [chunk for chunk in self.chunks if category is None or chunk.category == category]
        scored = [(cosine(query_vector, chunk.vector) + keyword_boost(query, chunk.text), chunk) for chunk in candidates]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {"id": chunk.id, "title": chunk.title, "category": chunk.category, "source": chunk.source, "text": chunk.text, "score": round(score, 4)}
            for score, chunk in scored[:top_k]
        ]

    def stats(self) -> dict:
        return {"backend": self.backend, "embedding_model": self.embedder.name, "chunks": len(self.chunks), "documents": len({c.title for c in self.chunks})}

    def load_directory(self, directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(self.add(path.stem, path.stem.split("__", 1)[0], f"knowledge/{path.name}", path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.md")))


class PgVectorRag:
    backend = "pgvector"

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
            cursor.execute("create index if not exists rag_chunk_hnsw on rag_chunk using hnsw (embedding vector_cosine_ops)")

    def _connect(self):
        import psycopg
        from pgvector.psycopg import register_vector

        connection = psycopg.connect(self.database_url)
        register_vector(connection)
        return connection

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

    def stats(self) -> dict:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute("select count(*), count(distinct title) from rag_chunk")
            chunks, documents = cursor.fetchone()
        return {"backend": self.backend, "embedding_model": self.embedder.name, "chunks": int(chunks), "documents": int(documents)}

    def load_directory(self, directory: Path) -> int:
        """Index the approved corpus once; re-index everything if the embedding model changed."""
        if not directory.exists():
            return 0
        with self._connect() as connection, connection.cursor() as cursor:
            # API, MCP and LangGraph start together; one transaction-scoped lock makes indexing happen once.
            cursor.execute("select pg_advisory_xact_lock(7316001)")
            cursor.execute("select count(*) filter (where embedding_model=%s), count(*) from rag_chunk", (self.embedder.name,))
            current, total = cursor.fetchone()
            if total and current == total:
                return 0
            cursor.execute("delete from rag_chunk where source like 'knowledge/%%' or embedding_model<>%s", (self.embedder.name,))
            return sum(
                self.add(path.stem, path.stem.split("__", 1)[0], f"knowledge/{path.name}", path.read_text(encoding="utf-8"), cursor)
                for path in sorted(directory.glob("*.md"))
            )

    def search(self, query: str, top_k: int = 4, category: str | None = None) -> list[dict]:
        import numpy as np

        vector = np.array(self.embedder.embed([query])[0])
        where = "where category=%s" if category else ""
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


def create_rag(backend: str, postgres_url: str, knowledge_dir: Path, embedding_backend: str = "fastembed", embedding_model: str = "BAAI/bge-small-en-v1.5"):
    embedder = get_embedder(embedding_backend, embedding_model)
    repository = PgVectorRag(postgres_url, embedder) if backend == "pgvector" else MemoryRag(embedder)
    repository.load_directory(knowledge_dir)
    return repository
