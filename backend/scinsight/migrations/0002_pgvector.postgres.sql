-- PostgreSQL only: pgvector column + HNSW index for the private RAG chunks (SQLite keeps JSON vectors for unit tests).
create extension if not exists vector;
alter table rag_chunks add column if not exists embedding_vec vector(384);
create index if not exists ix_rag_chunks_hnsw on rag_chunks using hnsw (embedding_vec vector_cosine_ops);
