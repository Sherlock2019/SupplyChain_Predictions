"""Candidate indexes: built next to the active index (separate index_version rows), validated, never published here."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.scinsight.db import now_iso
from backend.scinsight.rag import DocumentError, parse_document
from backend.scinsight.rag_tuning.config import RagTuningConfig, diff
from backend.scinsight.rag_tuning.embeddings import approved


def current_docs_sha(knowledge_dir: Path, tenant_id: str) -> dict:
    """doc_id:version -> sha256 of the source files that an index of this tenant must contain."""
    out = {}
    for path in sorted(knowledge_dir.glob("*.md")):
        try:
            meta, _ = parse_document(path)
        except DocumentError:
            continue
        if meta["tenant"] == tenant_id:
            out[f"{meta['doc_id']}:{meta['version']}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def build_candidate_index(registry, kb, knowledge_dir: Path, tenant_id: str, config_id: str) -> dict:
    """Index the tenant's documents with the configuration's cold settings under a new index version."""
    row = registry.get(tenant_id, config_id)
    if row["status"] in ("active", "retired"):
        raise ValueError(f"{config_id} is {row['status']}: build candidates from a draft")
    cfg = RagTuningConfig.model_validate(row["config"])
    active = registry.get_active_rag_config(tenant_id)
    # 1. hot-only change: the active index already has the right chunks and embeddings, nothing to build
    if not diff(active["config"], cfg.model_dump())["needs_new_index"]:
        registry.set_status(config_id, "candidate", index_version=active["index_version"])
        return {"config_id": config_id, "index_version": active["index_version"], "reused": True, "note": "query-time change only: reuses the active index"}
    index_version = f"idx-{config_id.lower()}"
    dims = approved(kb.backend).get(cfg.embedding_model, {}).get("dims")
    kb.db.execute("delete from rag_index_builds where index_version=?", (index_version,))
    kb.db.execute("insert into rag_index_builds(index_version,tenant_id,config_id,status,embedding_model,dims,started_at) values(?,?,?,?,?,?,?)",
                  (index_version, tenant_id, config_id, "building", cfg.embedding_model, dims, now_iso()))
    try:
        # 2. write the new index version (the active one keeps serving every query meanwhile)
        stats = kb.build_index(knowledge_dir, tenant_id, cfg, index_version)
        # 3. validate before anyone can publish it
        report = validate_index(kb, knowledge_dir, tenant_id, index_version, cfg)
        if not report["ok"]:
            raise ValueError("candidate index failed validation: " + "; ".join(report["problems"]))
    except Exception as exc:
        kb.db.execute("delete from rag_chunks where tenant_id=? and index_version=?", (tenant_id, index_version))
        kb.db.execute("update rag_index_builds set status='failed', finished_at=?, error=? where index_version=?", (now_iso(), str(exc)[:1000], index_version))
        registry.set_status(config_id, "failed", validation={"index_error": str(exc)[:1000]})
        raise
    kb.db.execute("update rag_index_builds set status='ready', finished_at=?, documents=?, chunks=?, docs_sha=? where index_version=?",
                  (now_iso(), stats["documents"], stats["chunks"], json.dumps(stats["docs_sha"]), index_version))
    registry.set_status(config_id, "candidate", index_version=index_version)
    return {"config_id": config_id, "index_version": index_version, "reused": False, **{k: stats[k] for k in ("documents", "chunks")}, "validation": report}


def validate_index(kb, knowledge_dir: Path, tenant_id: str, index_version: str, cfg: RagTuningConfig) -> dict:
    """Complete, single-model, right dimensions, and built from the current documents (not stale)."""
    problems = []
    rows = kb.db.query("select doc_id, version, embedding, embedding_model from rag_chunks where tenant_id=? and index_version=?", (tenant_id, index_version))
    expected = current_docs_sha(knowledge_dir, tenant_id)
    present = {f"{r['doc_id']}:{r['version']}" for r in rows}
    missing = sorted(set(expected) - present)
    if missing:
        problems.append(f"documents without chunks: {', '.join(missing)}")
    models = {r["embedding_model"] for r in rows}
    if models and models != {cfg.embedding_model}:
        problems.append(f"mixed embedding models in one index: {sorted(models)}")
    dims = {len(json.loads(r["embedding"])) for r in rows}
    want = approved(kb.backend).get(cfg.embedding_model, {}).get("dims")
    if want and dims and dims != {want}:
        problems.append(f"embedding dimensions {sorted(dims)} != {want}")
    if index_version != "baseline":
        build = kb.db.one("select docs_sha, status from rag_index_builds where index_version=?", (index_version,))
        if build and build["docs_sha"] and json.loads(build["docs_sha"]) != expected:
            problems.append("stale: the source documents changed since this index was built (rebuild it)")
    if not rows:
        problems.append("empty index")
    return {"ok": not problems, "problems": problems, "chunks": len(rows), "documents": len(present), "dims": sorted(dims), "models": sorted(models)}


def list_indexes(kb, tenant_id: str) -> list[dict]:
    rows = kb.db.query("select index_version, embedding_model, count(*) as chunks, count(distinct doc_id) as documents from rag_chunks "
                       "where tenant_id=? group by index_version, embedding_model", (tenant_id,))
    builds = {b["index_version"]: b for b in kb.db.query("select * from rag_index_builds where tenant_id=?", (tenant_id,))}
    out = [{**r, "status": builds.get(r["index_version"], {}).get("status", "ready"), "config_id": builds.get(r["index_version"], {}).get("config_id"),
            "built_at": builds.get(r["index_version"], {}).get("finished_at")} for r in rows]
    out += [{"index_version": b["index_version"], "embedding_model": b["embedding_model"], "chunks": 0, "documents": 0, "status": b["status"],
             "config_id": b["config_id"], "error": b["error"]} for v, b in builds.items() if v not in {r["index_version"] for r in rows}]
    return out
