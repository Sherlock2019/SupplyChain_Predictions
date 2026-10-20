from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from backend.app.config import ROOT
from backend.app.rag import HashEmbedder, MemoryRag, chunk_markdown, keyword_boost
from backend.app.store import Store


def test_chunking_keeps_title_and_section():
    chunks = chunk_markdown("doc", "# Contract X\n\n## Lead time\nTwenty days.\n\n## Penalties\nThree percent.")
    assert chunks == ["Contract X — Lead time\nTwenty days.", "Contract X — Penalties\nThree percent."]


def test_keyword_boost_rewards_exact_sap_codes():
    assert keyword_boost("status of QL-260014", "lot QL-260014 rejected") > 0
    assert keyword_boost("status of QL-260014", "other text") == 0


def test_memory_rag_finds_category_and_injection_text_is_just_data():
    rag = MemoryRag(HashEmbedder())
    assert rag.load_directory(ROOT / "data" / "knowledge") > 20
    hits = rag.search("PackGlass neck finish defect AQL", 3, "quality")
    assert hits and all(h["category"] == "quality" for h in hits)
    stats = rag.stats()
    assert stats["documents"] == 11


@pytest.mark.skipif(os.environ.get("RUN_FASTEMBED") != "1", reason="semantic embedding model download; set RUN_FASTEMBED=1")
def test_fastembed_semantic_retrieval():
    from backend.app.rag import FastEmbedder

    rag = MemoryRag(FastEmbedder("BAAI/bge-small-en-v1.5"))
    rag.load_directory(ROOT / "data" / "knowledge")
    top = rag.search("Who can replace the glass perfume bottle supplier?", 2)
    assert any("packglass" in hit["title"] for hit in top)


def test_mcp_server_tools_health_and_auth(monkeypatch):
    monkeypatch.setenv("MCP_API_KEYS", "mcp-test-key")
    from backend.app.mcp_server import create_mcp_app, mcp

    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert tools == {
        "sap_snapshot",
        "factory_material_readiness",
        "warehouse_stock_balance",
        "supplier_risk",
        "quality_status",
        "logistics_status",
        "inventory_overview",
        "sales_order_fulfilment",
        "stocktake_reconciliation",
        "search_governed_knowledge",
    }
    with TestClient(create_mcp_app()) as client:
        assert client.get("/health").json()["tools"] == 10
        assert client.post("/mcp", json={}).status_code == 401
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}}
        response = client.post("/mcp", json=init, headers={"X-API-Key": "mcp-test-key", "Accept": "application/json, text/event-stream"})
        assert response.status_code == 200 and response.json()["result"]["serverInfo"]["name"] == "aurelia-supply-chain-readonly"


def _exercise_store(store: Store) -> None:
    analysis_id = store.save_analysis("stock_balance", {"m": 1}, {"proposed_actions": [{"action": "stock_transfer", "quantity": 5}]}, "SNAP", "tester")
    rec = store.submit(analysis_id, "why", "tester")
    assert rec["status"] == "pending_review" and rec["actions"][0]["quantity"] == 5
    assert store.submit(analysis_id, "dup", "tester")["id"] == rec["id"]
    assert store.decide(rec["id"], "accepted", "boss", "fine")["status"] == "accepted"
    assert store.decide(rec["id"], "rejected", "boss", "late") is None
    for i in range(5):
        store.audit("tester", "assistant", f"event.{i}", {"i": i}, "corr")
    assert store.verify_chain()
    assert store.counts()["recommendations"]["accepted"] >= 1


def test_sqlite_store():
    _exercise_store(Store.memory())


@pytest.mark.skipif(not os.environ.get("TEST_POSTGRES_URL"), reason="set TEST_POSTGRES_URL for the PostgreSQL integration test")
def test_postgres_store_and_pgvector_rag():
    url = os.environ["TEST_POSTGRES_URL"]
    _exercise_store(Store(url))
    from backend.app.rag import PgVectorRag

    rag = PgVectorRag(url, HashEmbedder())
    rag.load_directory(ROOT / "data" / "knowledge")
    assert rag.stats()["chunks"] > 20
    assert rag.search("BioActive expedite clause", 2)[0]["title"].startswith("contract__bioactive")
