-- RAG tuning: index versions, configuration versions, experiments, background jobs and the query log.
-- Existing chunks become the 'baseline' index version (the configuration before tuning).
alter table rag_chunks add column index_version text not null default 'baseline';
create index if not exists ix_chunks_index on rag_chunks (tenant_id, index_version);

create table if not exists rag_config_versions (
  id text primary key, tenant_id text not null, status text not null,          -- draft | candidate | active | retired | failed
  config text not null, index_version text, name text not null, notes text not null,
  created_by text not null, created_at text not null, published_by text, published_at text,
  flowise_backup text, flowise_sync text, validation text
);
create index if not exists ix_rag_config_tenant on rag_config_versions (tenant_id, status);

create table if not exists rag_index_builds (
  index_version text primary key, tenant_id text not null, config_id text not null, status text not null,  -- building | ready | failed
  embedding_model text not null, dims integer, documents integer, chunks integer, docs_sha text,
  started_at text not null, finished_at text, error text
);

create table if not exists rag_experiments (
  id text primary key, tenant_id text not null, config_id text not null, dataset_version text not null,
  created_by text not null, created_at text not null, params text not null, summary text not null, cases text not null
);

create table if not exists rag_jobs (
  id text primary key, tenant_id text not null, kind text not null, status text not null,  -- queued | running | done | failed
  created_by text not null, created_at text not null, finished_at text, params text not null, result text, error text
);

create table if not exists rag_query_log (
  id text primary key, tenant_id text not null, ts text not null, config_id text not null, index_version text not null,
  query_sha text not null, top_k integer not null, mode text not null, doc_ids text not null, results integer not null,
  latency_ms real not null, source text not null
);
create index if not exists ix_rag_query_log on rag_query_log (tenant_id, ts);
