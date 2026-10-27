"""Knowledge-base inventory and metadata quality checks. Deficiencies are reported as found; no value is ever invented."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

from backend.scinsight.rag import INJECTION, REQUIRED, DocumentError, parse_document
from backend.scinsight.security import READ_ROLES

KNOWN_ROLES = READ_ROLES | {"all", "sap_executor"}
RECOMMENDED = ("valid_to", "approval_status", "owner")  # not required by ingestion, but needed to govern a policy
# What the Company RAG Search does with each front-matter field (anything else is stored but not used by retrieval).
FIELD_USE = {"doc_id": "citation", "title": "citation + chunk heading", "category": "category filter", "version": "citation + index key",
             "tenant": "tenant isolation", "valid_from": "validity filter", "valid_to": "validity filter", "access_roles": "role filter"}


def _front_matter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return {k.strip(): v.strip() for k, _, v in (line.partition(":") for line in m.group(1).splitlines()) if k.strip()} if m else {}


def inventory(db, kb, knowledge_dir: Path, tenant_id: str, on: date) -> dict:
    """Every source file of the caller's tenant with its metadata, index state and deficiencies (other tenants are not listed)."""
    _, cfg, index_version = kb.active(tenant_id)
    counts = {(r["doc_id"], r["version"]): r["n"] for r in db.query(
        "select doc_id, version, count(*) as n from rag_chunks where tenant_id=? and index_version=? group by doc_id, version", (tenant_id, index_version))}
    registered = {(r["doc_id"], r["version"]): r for r in db.query("select * from rag_documents where tenant_id=?", (tenant_id,))}
    docs, rejected = [], []
    for path in sorted(knowledge_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = _front_matter(text)
        if fm.get("tenant") and fm["tenant"] != tenant_id:
            continue  # another tenant's document: not even its name is shown
        try:
            meta, body = parse_document(path)
        except DocumentError as exc:
            rejected.append({"source": path.name, "error": str(exc), "present_fields": sorted(fm)})
            continue
        key = (meta["doc_id"], meta["version"])
        reg = registered.get(key)
        issues = validate_document_metadata(meta, fm, body, on)
        docs.append({"doc_id": meta["doc_id"], "title": meta["title"], "source": path.name, "tenant": meta["tenant"], "category": meta["category"],
                     "version": meta["version"], "valid_from": meta["valid_from"], "valid_to": meta.get("valid_to") or None,
                     "approval_status": fm.get("approval_status") or None, "owner": fm.get("owner") or None,
                     "access_roles": meta["access_roles"], "ingested_at": reg["ingested_at"] if reg else None,
                     "indexed_sha_matches": bool(reg) and reg["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest(),
                     "chunks": counts.get(key, 0), "index_version": index_version, "flags": json.loads(reg["flags"]) if reg else [],
                     "in_flowise_rag_db": bool({"agent_service", "all"} & set(meta["access_roles"])), "issues": issues,
                     "chars": len(body),
                     "metadata": [{"field": k, "value": v, "used_for": FIELD_USE.get(k, "stored only")} for k, v in fm.items()],
                     "metadata_missing": [f for f in (*REQUIRED, *RECOMMENDED) if not fm.get(f)]})
    _cross_document_checks(docs, on)
    by_type = {}
    for d in docs:  # metadata fields used per document type (category)
        t = by_type.setdefault(d["category"], {"category": d["category"], "documents": 0, "fields": set(), "missing": set()})
        t["documents"] += 1
        t["fields"] |= {m["field"] for m in d["metadata"]}
        t["missing"] |= set(d["metadata_missing"])
    types = [{"category": t["category"], "documents": t["documents"],
              "fields": [{"field": f, "used_for": FIELD_USE.get(f, "stored only")} for f in sorted(t["fields"], key=lambda f: (f not in FIELD_USE, f))],
              "missing": sorted(t["missing"])} for t in sorted(by_type.values(), key=lambda t: t["category"])]
    return {"tenant": tenant_id, "index_version": index_version, "embedding_model": cfg.embedding_model, "documents": docs, "rejected": rejected,
            "metadata_by_type": types, "field_use": FIELD_USE,
            "summary": {"documents": len(docs), "rejected": len(rejected), "with_issues": sum(1 for d in docs if d["issues"]),
                        "chunks": sum(d["chunks"] for d in docs)}}


def validate_document_metadata(meta: dict, front_matter: dict, body: str, on: date) -> list[dict]:
    """Checks on one document: missing fields, scope, validity and source quality (severity: error | warning | info)."""
    issues = []
    for f in REQUIRED:
        if not front_matter.get(f):
            issues.append({"severity": "error", "check": "required_field", "detail": f"missing {f}"})
    for f in RECOMMENDED:
        if not front_matter.get(f):
            issues.append({"severity": "warning", "check": "recommended_field", "detail": f"missing {f} (not invented: add it to the front matter)"})
    unknown = sorted(set(meta["access_roles"]) - KNOWN_ROLES)
    if unknown:
        issues.append({"severity": "error", "check": "access_scope", "detail": f"unknown roles {', '.join(unknown)} (nobody can match them)"})
    if "all" in meta["access_roles"]:
        issues.append({"severity": "info", "check": "access_scope", "detail": "readable by every role of the tenant (access_roles: all)"})
    if meta.get("valid_to") and date.fromisoformat(meta["valid_to"]) < on:
        issues.append({"severity": "error", "check": "expired", "detail": f"expired on {meta['valid_to']}: excluded from retrieval"})
    if date.fromisoformat(meta["valid_from"]) > on:
        issues.append({"severity": "warning", "check": "not_yet_effective", "detail": f"effective from {meta['valid_from']}"})
    if INJECTION.search(body):
        issues.append({"severity": "warning", "check": "source_quality", "detail": "contains instruction-like text (flagged; agents must ignore it as a command)"})
    if "## " not in body:
        issues.append({"severity": "warning", "check": "source_quality", "detail": "no '## ' sections: section-aware chunking cannot preserve clauses"})
    if len(body) < 200:
        issues.append({"severity": "info", "check": "source_quality", "detail": f"short document ({len(body)} characters)"})
    return issues


def _cross_document_checks(docs: list[dict], on: date) -> None:
    # Superseded: a newer version of the same doc_id is valid on the business date while an older one still is too.
    by_id = {}
    for d in docs:
        by_id.setdefault(d["doc_id"], []).append(d)
    for versions in by_id.values():
        if len(versions) > 1:
            newest = max(versions, key=lambda d: [int(x) if x.isdigit() else x for x in re.split(r"[.-]", d["version"])])
            for d in versions:
                if d is not newest:
                    still = not d["valid_to"] or date.fromisoformat(d["valid_to"]) >= on
                    d["issues"].append({"severity": "error" if still else "info", "check": "superseded",
                                        "detail": f"superseded by version {newest['version']}" + (" but still valid (both versions can be retrieved)" if still else "")})
    # Duplicates: same title under different ids, or same body size and title prefix.
    seen = {}
    for d in docs:
        key = d["title"].lower().strip()
        if key in seen and seen[key]["doc_id"] != d["doc_id"]:
            d["issues"].append({"severity": "warning", "check": "duplicate", "detail": f"same title as {seen[key]['doc_id']}"})
        seen.setdefault(key, d)


def source_text(knowledge_dir: Path, tenant_id: str, doc_id: str) -> dict:
    """The source document of the caller's tenant (front matter + body) for preview; other tenants' documents are not found."""
    for path in sorted(knowledge_dir.glob("*.md")):
        try:
            meta, body = parse_document(path)
        except DocumentError:
            continue
        if meta["doc_id"] == doc_id and meta["tenant"] == tenant_id:
            return {"doc_id": doc_id, "source": path.name, "meta": meta, "body": body}
    raise KeyError(doc_id)
