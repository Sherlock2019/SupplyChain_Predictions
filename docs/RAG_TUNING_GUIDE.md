# RAG Tuning Guide — SCInsight Company RAG Search

The RAG Tuning Console tunes, tests and publishes the retrieval behind the SCInsight chatflow
`SCInsight-Cosmetics-Chatflow-v1`. It controls the real retrieval path (no separate demo retriever, no second vector
database). Open it in the dashboard: **AI / RAG → RAG Tuning** (manager key), or use `scripts/rag_tuning.py`.

## 1. The audited retrieval path

The chatflow's Tool Agent reaches company policies through two tools. Both are controlled by the console:

```
Chat (Flowise) → Tool Agent "SCInsight Supply Chain Assistant"
 ├─ search_supply_chain_policy  (Custom Tool, JavaScript: POST $vars.sci_api_url/api/v1/rag/search, query only)
 │    → SCInsight routes (/scinsight of the one FastAPI app, :8000) rag_search → KnowledgeBase.search (backend/scinsight/rag.py)
 │    → PostgreSQL "scinsight": rag_chunks (pgvector, index_version of the ACTIVE configuration) + rag_documents
 │    → passages with citation {doc_id, version, section, chunk, validity}, injection flags, config_version, index_version
 └─ company_policy_rag_db       (Flowise Retriever tool, no code)
      → Flowise Postgres vector store, table scinsight_flowise_rag (database scinsight, cosine, topK)
      ← Folder loader opt/flows/scinsight/knowledge ← Markdown text splitter ← embeddings via gateway /v1/embeddings
        (BAAI/bge-small-en-v1.5), Postgres record manager (cleanup: full)
```

Findings of the audit (before tuning):

| Question | Finding (evidence) |
|---|---|
| Frontend | Vanilla JS dashboard served by the gateway (`frontend/`, FastAPI :8000) |
| FastAPI app with RAG | SCInsight API `backend/scinsight/app.py` (`/api/v1/rag/search`, `/api/v1/rag/documents`) |
| Tools invoking Company RAG Search | `search_supply_chain_policy` (Custom Tool → API) and `company_policy_rag_db` (Retriever tool → Flowise vector store). The live labels are "SCInsight API · governed policy search (cited)" and "Retriever tool · company RAG DB (policies)"; no node is labelled "5b" in the deployed flow |
| Ingestion | `KnowledgeBase.ingest_dir` at API start (data/scinsight/knowledge); Flowise upsert by `flowise/scinsight/deploy.py import` |
| Chunking | API: `## ` sections then 900/120-character windows. Flowise: Markdown splitter 800/100 characters |
| Embeddings | BAAI/bge-small-en-v1.5 (fastembed, 384 dims) in both paths (Flowise through the gateway) |
| Vector store | pgvector in PostgreSQL database `scinsight`: `rag_chunks.embedding_vec` (HNSW, cosine) and `scinsight_flowise_rag` |
| Retrieval parameters | API: top 4 (request default), 16 candidates, no threshold. Flowise: topK 4 |
| Permissions | API: tenant from the API key (other tenants' rows never loaded), `access_roles`, validity dates. Flowise path: only documents the agent key may read are copied into its folder; no per-user filter |
| Reranker | none |
| Evaluations / tests | API scenario tests only; no retrieval-quality evaluation existed |

The Agentflow specialists use a third copy (Document Store "SCInsight policy RAG DB"). The console does not change it.

## 2. Parameters

All sizes are **characters** (the splitters cut text; they do not tokenize). Token counts shown are approximate (characters / 4).

| Setting | Kind | What it does | Notes |
|---|---|---|---|
| `chunk_strategy` | index (cold) | `section` = split on `## ` headings then windows (original splitter, identical output); `fixed` = windows over the whole document; `clause` = whole sentences packed up to the size, overlap made of whole sentences | `clause` keeps a condition and its approval rule together unless one sentence is longer than the chunk |
| `chunk_size` | index | characters per chunk | presets small 300/50, medium 600/100, large 1000/150 are starting points, not optimal values |
| `chunk_overlap` | index | characters repeated between neighbouring chunks | must be ≥ 0 and < `chunk_size` (validated) |
| `preserve_headings` | index | prefix "title — section" to every chunk | improves retrieval of short sections |
| `preserve_source_ids` | index | prefix "[doc_id vX]" | |
| `embedding_model` | index | approved models only (`/embedding-models`) | another model or dimension always gets its own index; models are never mixed in one index |
| `top_k` | query (hot) | passages returned | presets 3, 5, 8 |
| `similarity_threshold` | query | drop passages whose cosine similarity is below it | cosine of normalised embeddings, −1..1, **model specific, not a confidence**; a threshold tuned for one model does not transfer |
| `retrieval_mode` | query | `semantic`, `keyword` (query-term overlap) or `hybrid` (`hybrid_alpha` × semantic + (1 − alpha) × keyword) | the threshold applies to the semantic score; it is ignored in keyword mode |
| `rerank` | query | `lexical`: re-order candidates by query-term overlap | deterministic, no model download; no cross-encoder is installed |
| `candidate_k` | query | candidates scored before access filtering / rerank | ≥ `top_k` |
| `max_context_tokens` | query | approximate token budget of the returned passages | the first passage is always kept |
| `category_filter` | query | restrict document categories | can only narrow access, never widen it |

**Hot vs cold.** Hot settings take effect on the next query with the same index. Cold settings (chunking, headings/ids,
embedding model, document content) need a new index version: the console builds it next to the active one.

**What reaches Flowise.** On publish, the chatflow RAG DB mirrors `chunk_size`, `chunk_overlap` and `top_k` (its Markdown
splitter is closest to `section`) and is tagged with the configuration id. Threshold, mode, rerank and context budget have no
equivalent on the Flowise Postgres retriever: they apply to the API path only. The Flowise path can follow only
`BAAI/bge-small-en-v1.5` (the model the gateway serves), so publish is refused for other models.

## 3. Recommended experiment method

1. **Knowledge & metadata**: run the checks; fix errors in the source documents first (missing fields are reported, never invented).
2. **Chunking**: preview one procurement document against the active configuration; save a draft.
3. **Embeddings**: test loading a candidate model (download needs internet); draft with it.
4. **Retrieval**: try hot settings on real questions with role fixtures; check the *Excluded* table (access, threshold, budget).
5. **Evaluation lab**: benchmark the active configuration and the candidates on the same dataset (`v1`); compare A vs B.
   A grid shows its workload first and runs only when confirmed.
6. **Publish**: validate, then publish (director). Monitor the query log; roll back if needed.

Tune on dataset `v1`, then confirm on new questions: with 15 questions a threshold can over-fit.

## 4. Evaluation

Dataset `data/scinsight/rag_benchmark/v1.json` (versioned, synthetic): 15 labelled questions: approvals, safety stock,
emergency supplier, shortages, shelf life, supplier terms, quality, expiry, the effective policy version, one question the
corpus cannot answer, one other-tenant question and one role-access question. Each case has relevant document ids, expected
facts, a role fixture, expected behaviour and expected citations.

| Metric | Definition |
|---|---|
| Hit Rate@K | 1 if at least one relevant document is in the top K (cases with relevant documents) |
| Recall@K | relevant documents found in the top K / relevant documents |
| Precision@K | returned chunks from a relevant document / K (a threshold that returns fewer chunks lowers it) |
| MRR | 1 / rank of the first relevant chunk |
| Evidence coverage | expected facts present in the retrieved text (deterministic grounding of the context) |
| No-evidence pass | 1 if nothing is returned for the question the corpus cannot answer |
| Version accuracy | citation carries the effective version |
| Leakage | chunks from a forbidden document (other tenant, role without access); must be 0 |
| Latency | embed, retrieve, total; mean and p95 per query |
| Answers (optional) | Qwen answers checked deterministically: fact coverage, citation correctness, unsupported numbers, refusal. No LLM judge; cost N/A (local models) |

Acceptance criteria for publish (`evaluation.ACCEPTANCE`): hit rate not lower, recall at most −0.05, leakage 0, p95 latency
≤ max(2 × active, active + 200 ms), no-evidence not lower, same dataset version.

## 5. Lifecycle, publish and rollback

Draft → Preview → Benchmark → Validate → Publish → Monitor → Rollback.

* **Candidate index**: `idx-<config id>` rows in `rag_chunks` (the active index keeps serving). A failed build is deleted and the configuration marked `failed`.
* **Validate**: built and complete, single model, right dimensions, not stale (documents unchanged since the build), model loads, Flowise-compatible, benchmark passes the criteria against the active configuration.
* **Publish** (supply_chain_director, `confirm=true`): Flowise chatflow first (save its JSON, update splitter / topK / loader tag, `POST /api/v1/vector/upsert/<id>`, verify that every row of `scinsight_flowise_rag` carries the new tag; on failure the saved chatflow is restored and re-indexed), then the active pointer switches in one transaction. Audited (`rag.published`).
* **Rollback**: re-activates a previously published version; its index is kept, and its exact chatflow JSON is restored.
* **Record manager**: verified on Flowise 3.1.2. A re-upsert with `cleanup: full` deleted all 12 old chunks and added 12 new ones (the metadata tag changes every chunk hash).
* **Caveat**: `flowise/scinsight/deploy.py import` re-imports the exported chatflow (800/100, untagged). Re-publish afterwards if a tuned configuration is active.

## 6. API and CLI

SCInsight API, prefix `/api/v1/rag-tuning` (Swagger tag *rag-tuning*); the dashboard calls the same paths on the gateway, which
forwards a manager's calls with `SCI_TUNING_KEY` (= `SCI_DIRECTOR_KEY`, server-side only):

`GET config` · `PUT draft` · `GET history` · `GET diff/{id}` · `GET documents` · `POST metadata/validate` ·
`GET documents/{doc_id}/source` · `POST chunks/preview` · `GET embedding-models` · `POST embedding-models/test` (job) ·
`POST index/build-candidate` (job) · `GET jobs/{id}` · `POST retrieve/preview` · `POST evaluate` (job) · `POST evaluate/grid` ·
`GET experiments` · `GET experiments/compare` · `GET experiments/{id}` · `POST validate` · `POST publish` · `POST rollback` ·
`GET flowise` · `GET metrics`.

Roles: in the SCInsight API, supply_chain_director and mlops_engineer can use the console and only the director can publish or
roll back. In the dashboard, every role can open the console. The gateway forwards managers' calls with the director key
(`SCI_TUNING_KEY`) and everyone else's with the MLOps key (`SCI_TUNING_READER_KEY`). Publish and rollback are refused for
non-managers (403). For non-managers the Retrieval tab tests access with a role fixture (default `planner`).

```bash
python3 scripts/rag_tuning.py config | documents | validate | models | history | flowise | metrics
python3 scripts/rag_tuning.py preview POL-PROC-001 --size 600 --overlap 100 --strategy clause
python3 scripts/rag_tuning.py retrieve "Who must approve a warehouse stock transfer?" --top-k 5 --threshold 0.66 --role planner
python3 scripts/rag_tuning.py draft --threshold 0.66 --name "threshold 0.66"
python3 scripts/rag_tuning.py build RCFG-XXXXXXXX && python3 scripts/rag_tuning.py evaluate RCFG-ACTIVE RCFG-XXXXXXXX
python3 scripts/rag_tuning.py publish RCFG-XXXXXXXX --confirm
python3 scripts/rag_tuning.py verify "Who must approve a warehouse stock transfer?"   # asks the live chatflow
python3 scripts/rag_tuning.py rollback RCFG-PREVIOUS --confirm
```

## 7. Verification report (2026-10-27, local stack)

**Code paths**: `backend/scinsight/rag.py` (KnowledgeBase: versioned indexes, active configuration, shared ranking, query log),
`backend/scinsight/rag_tuning/` (config, chunking, embeddings, retrieval, registry, documents, indexing, evaluation, publishing,
flowise_adapter, api), migration `0003_rag_tuning.sql`, gateway proxy `backend/app/main.py`, dashboard page `#rag`,
`scripts/rag_tuning.py`.

**Tests**: `tests/scinsight/test_rag_tuning.py` (17 tests: config validation, chunk size/overlap, clause boundaries, metadata
checks incl. expired/superseded/missing, approved models and dimensions, candidate index isolation, top-k, threshold, role and
tenant access, metric definitions, answer checks, reproducible benchmark, grid workload, publish authorisation and gate,
rollback, candidate-index failure, stale index) plus the proxy test; whole suite 153 passed, 11 skipped (opt-in); ruff clean.
The new splitter reproduces the old one exactly (83 chunks, 3 size settings).

**Live run** (gateway → SCInsight API → PostgreSQL / Flowise 3.1.2):

| Configuration | Hit@4 | Recall@4 | Precision@4 | MRR | Evidence | No-evidence | Leakage | Mean / p95 ms |
|---|---|---|---|---|---|---|---|---|
| baseline (section 900/120, no threshold) | 1.0 | 1.0 | 0.667 | 1.0 | 1.0 | 0.0 | 0 | 17.2 / 19.5 |
| threshold 0.66 (reuses the baseline index) | 1.0 | 1.0 | 0.604 | 1.0 | 1.0 | 1.0 | 0 | 11.8 / 13.2 |
| section 600/100 + 0.66 (new index) | 1.0 | 1.0 | 0.604 | 1.0 | 1.0 | 1.0 | 0 | 12.3 / 14.8 |
| clause 600/100 + 0.66 (new index) | 1.0 | 1.0 | 0.604 | 1.0 | 1.0 | 1.0 | 0 | 12.5 / 14.6 |

* Chunk size does not matter for this corpus: every section is shorter than 600 characters, so all three indexes hold 21 chunks.
* The threshold fixes the unanswerable question (top score 0.623 vs ≥ 0.712 for every real question), but it was chosen on these 15 questions.
* Published "threshold 0.66" (director): the Flowise chatflow RAG DB was re-indexed (12 deleted, 12 added, all tagged).
* Asked the live chatflow two questions:
  * Via `company_policy_rag_db`: sources tagged with the published version; answer "approved by the warehouse manager [POL-WH-020]".
  * Via `search_supply_chain_policy`: logged against the published configuration; cited POL-PROC-001 v3.1.
  * No other-tenant document appeared in either answer.
* Rolled back to the baseline: the original chatflow came back (800/100, 12 untagged chunks) and the baseline is active again. **The live system was left on the baseline**; publishing "threshold 0.66" is the director's decision.

**Limitations**:
* Only bge-small is installed. The multilingual and bge-base candidates download on first use, which needs internet.
* No cross-encoder reranker is installed.
* Keyword and hybrid modes score all chunks in Python. That is fine for 21 chunks, but would need a text index for a large corpus.
* The Agentflow Document Store copy is not synchronised.
* Answer evaluation depends on the local Qwen endpoint.
