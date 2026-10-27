"""RAG Tuning Console: configuration, chunking, metadata, indexes, retrieval, evaluation, publish / rollback (hermetic: SQLite, hash embedder)."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.scinsight.app import create_app
from backend.scinsight.db import Database
from backend.scinsight.rag_tuning import evaluation
from backend.scinsight.rag_tuning.chunking import chunk, preview_document_chunks
from backend.scinsight.rag_tuning.config import RagTuningConfig, diff
from backend.scinsight.settings import ROOT
from tests.scinsight.conftest import key, settings

KNOWLEDGE = ROOT / "data" / "scinsight" / "knowledge"
BASE = "/api/v1/rag-tuning"


@pytest.fixture()
def kdir(tmp_path: Path) -> Path:
    d = tmp_path / "knowledge"
    shutil.copytree(KNOWLEDGE, d)
    return d


@pytest.fixture()
def client(kdir) -> TestClient:
    return TestClient(create_app(settings(sci_jobs_inline=True, sci_knowledge_dir=kdir), Database("sqlite:///:memory:")))


def draft(client, name="t", **cfg) -> dict:
    r = client.put(f"{BASE}/draft", json={"config": {"embedding_model": "hash-bow-384", **cfg}, "name": name}, headers=key("mlops"))
    assert r.status_code == 200, r.text
    return r.json()


def run_job(client, path, body, who="mlops") -> dict:
    job = client.post(f"{BASE}{path}", json=body, headers=key(who)).json()
    assert job.get("status") == "done", job
    return job["result"]


# ---------------------------------------------------------------- configuration
def test_config_validation_rejects_overlap_not_smaller_than_size_and_negative_overlap():
    with pytest.raises(ValidationError, match="chunk_overlap must be smaller"):
        RagTuningConfig(chunk_size=300, chunk_overlap=300)
    with pytest.raises(ValidationError):
        RagTuningConfig(chunk_size=300, chunk_overlap=-1)
    with pytest.raises(ValidationError, match="candidate_k"):
        RagTuningConfig(top_k=8, candidate_k=4)
    d = diff(RagTuningConfig().model_dump(), RagTuningConfig(chunk_size=600, chunk_overlap=100, top_k=5).model_dump())
    assert d["rebuild_required"] == ["chunk_size", "chunk_overlap"] and d["query_time"] == ["top_k"] and d["needs_new_index"]


def test_only_admins_see_the_console_and_tenant_comes_from_the_key(client):
    assert client.get(f"{BASE}/config", headers=key("planner")).status_code == 403
    assert client.get(f"{BASE}/config", headers=key("agent")).status_code == 403
    cfg = client.get(f"{BASE}/config", headers=key("director")).json()
    assert cfg["active"]["name"] == "baseline" and cfg["active"]["index_version"] == "baseline" and cfg["chunk_unit"] == "characters"
    assert client.get(f"{BASE}/config", headers={**key("director"), "X-Tenant": "northwind-pharma"}).status_code == 403


# ---------------------------------------------------------------- chunking
def test_chunk_preview_sizes_overlap_and_clause_boundaries():
    body = "# T\n## Approval\n" + " ".join(f"Sentence number {i} explains a rule." for i in range(40)) + " Transfers are approved by the warehouse manager."
    small = preview_document_chunks("T", body, RagTuningConfig(chunk_size=300, chunk_overlap=50), "POL-X", "1")
    large = preview_document_chunks("T", body, RagTuningConfig(chunk_size=1000, chunk_overlap=150), "POL-X", "1")
    assert small["count"] > large["count"] > 0 and small["unit"] == "characters"
    assert all(c["chars"] <= 300 + len("T — Approval\n") for c in small["chunks"])
    assert all(c["overlap_with_previous"] == 50 for c in small["chunks"][1:])
    clause = chunk("T", body, RagTuningConfig(chunk_strategy="clause", chunk_size=300, chunk_overlap=50))
    assert any("Transfers are approved by the warehouse manager." in c["content"] for c in clause)  # never cut mid-sentence
    assert all(c["content"].endswith(".") for c in clause)


def test_chunk_preview_endpoint_compares_without_writing(client):
    before = client.get(f"{BASE}/documents", headers=key("mlops")).json()["summary"]["chunks"]
    r = client.post(f"{BASE}/chunks/preview", json={"doc_id": "POL-PROC-001", "config": {"chunk_size": 300, "chunk_overlap": 50, "embedding_model": "hash-bow-384"},
                                                   "compare_with": {"chunk_size": 1000, "chunk_overlap": 150, "embedding_model": "hash-bow-384"}}, headers=key("mlops")).json()
    assert r["preview"]["count"] >= r["compare"]["count"] and r["writes"] == "none (preview only)"
    assert client.get(f"{BASE}/documents", headers=key("mlops")).json()["summary"]["chunks"] == before
    other = client.post(f"{BASE}/chunks/preview", json={"doc_id": "POL-NW-001", "config": {"embedding_model": "hash-bow-384"}}, headers=key("mlops"))
    assert other.status_code == 404  # another tenant's document does not exist for this caller


# ---------------------------------------------------------------- knowledge & metadata
def test_metadata_checks_report_missing_expired_and_superseded_without_inventing(client, kdir):
    old = (kdir / "POL-WH-020_warehouse_transfer_policy.md").read_text().replace("version: 2.4", "version: 2.3").replace("valid_to: 2027-12-31", "valid_to: 2028-06-30")
    (kdir / "POL-WH-020_v2.3.md").write_text(old)
    expired = (kdir / "POL-QA-045_expiry_fefo.md").read_text().replace("doc_id: POL-QA-045", "doc_id: POL-QA-001").replace("valid_to: 2027-12-31", "valid_to: 2025-01-31")
    (kdir / "POL-QA-001_old.md").write_text(expired)
    inv = client.get(f"{BASE}/documents", headers=key("director")).json()
    docs = {(d["doc_id"], d["version"]): d for d in inv["documents"]}
    assert ("POL-NW-001", "1.0") not in docs  # other tenant never listed
    assert docs[("POL-PROC-001", "3.1")]["approval_status"] is None  # missing field stays missing
    assert any(i["check"] == "recommended_field" and "approval_status" in i["detail"] for i in docs[("POL-PROC-001", "3.1")]["issues"])
    assert any(i["check"] == "superseded" and i["severity"] == "error" for i in docs[("POL-WH-020", "2.3")]["issues"])
    assert any(i["check"] == "expired" for i in docs[("POL-QA-001", "2.1")]["issues"])
    assert inv["rejected"] and inv["rejected"][0]["source"] == "BROKEN_no_metadata.md"
    report = client.post(f"{BASE}/metadata/validate", headers=key("director")).json()
    assert report["by_check"]["rejected"] == 1 and report["errors"] >= 3


# ---------------------------------------------------------------- embeddings, indexes, retrieval
def test_embedding_models_are_an_approved_list_and_dimensions_are_checked(client):
    models = {m["id"]: m for m in client.get(f"{BASE}/embedding-models", headers=key("mlops")).json()["models"]}
    assert models["hash-bow-384"]["active"] and models["hash-bow-128"]["dims"] == 128
    assert client.post(f"{BASE}/embedding-models/test", json={"model": "../evil-model"}, headers=key("mlops")).status_code == 422
    result = run_job(client, "/embedding-models/test", {"model": "hash-bow-128"})
    assert result["dims"] == [128] and result["dims_ok"]


def test_candidate_index_is_separate_and_active_search_is_unchanged(client):
    q = {"query": "Who must approve a warehouse stock transfer?"}
    live_before = client.post("/api/v1/rag/search", json=q, headers=key("planner")).json()
    cand = draft(client, chunk_size=300, chunk_overlap=50, embedding_model="hash-bow-128")
    built = run_job(client, "/index/build-candidate", {"config_id": cand["id"]})
    assert built["index_version"] == f"idx-{cand['id'].lower()}" and built["chunks"] > 0 and built["validation"]["dims"] == [128]
    live_after = client.post("/api/v1/rag/search", json=q, headers=key("planner")).json()
    assert live_after["index_version"] == "baseline" and live_after["results"] == live_before["results"]
    prev = client.post(f"{BASE}/retrieve/preview", json={**q, "config_id": cand["id"]}, headers=key("mlops")).json()
    assert prev["index_version"] == built["index_version"] and prev["embedding_model"] == "hash-bow-128"


def test_top_k_threshold_and_access_control_in_retrieval_preview(client):
    q = "Who must approve a warehouse stock transfer?"
    for k in (3, 5, 8):
        r = client.post(f"{BASE}/retrieve/preview", json={"query": q, "overrides": {"top_k": k, "candidate_k": 16}}, headers=key("mlops")).json()
        assert len(r["results"]) <= k
    strict = client.post(f"{BASE}/retrieve/preview", json={"query": q, "overrides": {"similarity_threshold": 0.99}}, headers=key("mlops")).json()
    assert strict["results"] == [] and any(e["reason"] == "below threshold" for e in strict["excluded"])
    wh = client.post(f"{BASE}/retrieve/preview", json={"query": "purchase request above EUR 10,000 approval", "roles": ["warehouse_manager"]}, headers=key("mlops")).json()
    assert "POL-PROC-001" not in [h["citation"]["doc_id"] for h in wh["results"]]
    assert any(e["doc_id"] == "POL-PROC-001" and e["reason"] == "role not in access_roles" for e in wh["excluded"])
    cold = client.post(f"{BASE}/retrieve/preview", json={"query": q, "overrides": {"chunk_size": 300}}, headers=key("mlops"))
    assert cold.status_code == 422  # index settings cannot be changed at query time


def test_unauthorized_tenant_never_sees_other_documents(client):
    other = client.post("/api/v1/rag/search", json={"query": "Northwind cold-chain temperature logger"}, headers=key("other_tenant")).json()
    belleva = client.post("/api/v1/rag/search", json={"query": "Northwind cold-chain temperature logger"}, headers=key("planner")).json()
    assert {h["citation"]["doc_id"] for h in other["results"]} <= {"POL-NW-001"}
    assert "POL-NW-001" not in {h["citation"]["doc_id"] for h in belleva["results"]}


# ---------------------------------------------------------------- evaluation
def test_metrics_definitions_hit_recall_precision_mrr_and_leakage():
    case = {"id": "x", "category": "c", "question": "q", "roles": ["planner"], "relevant_doc_ids": ["A", "B"], "forbidden_doc_ids": ["Z"],
            "expected_facts": ["warehouse manager"], "expected_behavior": "answer"}
    res = {"results": [{"citation": {"doc_id": d, "version": "1"}, "text": t, "score": 0.5} for d, t in
                       (("C", "x"), ("A", "approved by the warehouse manager"), ("Z", "secret"))], "latency_ms": {"total": 1, "embed": 0, "retrieve": 1}}
    s = evaluation.score_case(case, res, k=3)
    assert s["hit"] == 1.0 and s["recall"] == 0.5 and s["precision"] == pytest.approx(1 / 3) and s["rr"] == 0.5 and s["evidence"] == 1.0 and s["leakage"] == 1


def test_answer_checks_catch_wrong_citations_and_unsupported_numbers():
    case = {"relevant_doc_ids": ["POL-WH-020"], "expected_facts": ["warehouse manager"], "expected_behavior": "answer"}
    res = {"results": [{"citation": {"doc_id": "POL-WH-020", "version": "2.4"}, "text": "Transfers are approved by the warehouse manager. 14 days of cover."}]}
    good = evaluation.score_answer(case, "The warehouse manager approves [POL-WH-020].", res)
    bad = evaluation.score_answer(case, "The CFO approves transfers above 50,000 [POL-PROC-001].", res)
    assert good["citation_correct"] == 1.0 and good["fact_coverage"] == 1.0 and not good["unsupported_numbers"]
    assert bad["citation_correct"] == 0.0 and bad["unsupported_numbers"] == ["50,000"]


def test_benchmark_runs_the_real_search_and_is_reproducible(client):
    active = client.get(f"{BASE}/config", headers=key("mlops")).json()["active"]["id"]
    r1 = run_job(client, "/evaluate", {"config_ids": [active]})["experiments"][0]
    r2 = run_job(client, "/evaluate", {"config_ids": [active]})["experiments"][0]
    for m in ("hit_rate", "recall", "precision", "mrr", "evidence_coverage", "leakage"):
        assert r1["summary"][m] == r2["summary"][m]
    assert r1["summary"]["leakage"] == 0 and r1["summary"]["cases"] == len(evaluation.load_dataset()["cases"])
    exp = client.get(f"{BASE}/experiments/{r1['experiment_id']}", headers=key("mlops")).json()
    assert exp["dataset_version"] == "v1" and len(exp["cases"]) == exp["summary"]["cases"]


def test_grid_shows_workload_before_running(client):
    r = client.post(f"{BASE}/evaluate/grid", json={"presets": ["small", "large"], "top_k": [3, 5]}, headers=key("mlops")).json()
    assert r["confirm_required"] and r["workload"]["configurations"] == 4 and r["workload"]["index_builds"] == 2


# ---------------------------------------------------------------- publish / rollback
def test_publish_needs_director_benchmark_and_confirm_then_rollback(client):
    active = client.get(f"{BASE}/config", headers=key("director")).json()["active"]["id"]
    cand = draft(client, top_k=5, candidate_k=16, similarity_threshold=-1.0)
    assert client.post(f"{BASE}/publish", json={"config_id": cand["id"], "confirm": True}, headers=key("mlops")).status_code == 403
    run_job(client, "/index/build-candidate", {"config_id": cand["id"]})
    refused = client.post(f"{BASE}/publish", json={"config_id": cand["id"], "confirm": True}, headers=key("director"))
    assert refused.status_code == 409 and "benchmark" in refused.json()["detail"]
    run_job(client, "/evaluate", {"config_ids": [active, cand["id"]]})
    assert client.post(f"{BASE}/publish", json={"config_id": cand["id"]}, headers=key("director")).status_code == 422
    pub = client.post(f"{BASE}/publish", json={"config_id": cand["id"], "confirm": True}, headers=key("director"))
    assert pub.status_code == 200, pub.text
    live = client.post("/api/v1/rag/search", json={"query": "Who approves warehouse transfers?"}, headers=key("planner")).json()
    assert live["config_version"] == cand["id"] and len(live["results"]) <= 5
    back = client.post(f"{BASE}/rollback", json={"config_id": active, "confirm": True}, headers=key("director")).json()
    assert back["active"] == active and back["previous"] == cand["id"]
    assert client.post("/api/v1/rag/search", json={"query": "x y z"}, headers=key("planner")).json()["index_version"] == "baseline"
    assert any(e["action"] == "rag.published" for e in client.get("/api/v1/audit", headers=key("director")).json()["events"])


def test_candidate_index_failure_keeps_the_active_configuration(client, monkeypatch):
    from backend.scinsight import rag
    cand = draft(client, chunk_size=300, chunk_overlap=50)

    def boom(*a, **k):
        raise RuntimeError("embedding service down")
    monkeypatch.setattr(rag.KnowledgeBase, "build_index", boom)
    job = client.post(f"{BASE}/index/build-candidate", json={"config_id": cand["id"]}, headers=key("mlops")).json()
    assert job["status"] == "failed" and "embedding service down" in job["error"]
    hist = {v["id"]: v for v in client.get(f"{BASE}/history", headers=key("mlops")).json()["versions"]}
    assert hist[cand["id"]]["status"] == "failed"
    assert client.get(f"{BASE}/config", headers=key("mlops")).json()["active"]["name"] == "baseline"


def test_rollback_only_to_previously_published_versions(client):
    cand = draft(client, top_k=3)
    r = client.post(f"{BASE}/rollback", json={"config_id": cand["id"], "confirm": True}, headers=key("director"))
    assert r.status_code == 409 and "never published" in r.json()["detail"]


def test_stale_index_is_detected_when_documents_change(client, kdir):
    cand = draft(client, chunk_size=300, chunk_overlap=50)
    run_job(client, "/index/build-candidate", {"config_id": cand["id"]})
    p = kdir / "POL-WH-020_warehouse_transfer_policy.md"
    p.write_text(p.read_text() + "\nA new sentence that changes the document.\n")
    v = client.post(f"{BASE}/validate", json={"config_id": cand["id"]}, headers=key("director")).json()
    assert not v["ok"] and any("stale" in c["detail"] for c in v["checks"] if c["check"] == "index")
