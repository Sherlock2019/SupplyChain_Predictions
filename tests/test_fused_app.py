"""ONE FastAPI app: the gateway, with the SCInsight API included as a router at /scinsight (hermetic: SQLite, hash embeddings)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.store import Store
from backend.scinsight.app import create_router
from backend.scinsight.db import Database
from tests.scinsight.conftest import key
from tests.scinsight.conftest import settings as sci_settings


def fused(settings) -> TestClient:
    sci = create_router(sci_settings(sci_jobs_inline=True), Database("sqlite:///:memory:"))
    gw = settings.model_copy(update={"sci_tuning_key": "sci-dev-director-key", "sci_tuning_reader_key": "sci-dev-mlops-key"})
    return TestClient(create_app(gw, Store.memory(), scinsight_router=sci))


def test_one_fastapi_instance_serves_both_apis_with_their_own_auth(settings, manager_headers):
    c = fused(settings)
    assert isinstance(c.app, FastAPI) and not [r for r in c.app.routes if r.__class__.__name__ == "Mount" and r.path == "/scinsight"]
    assert c.get("/health").json()["service"] == "supply-chain-copilot"
    assert c.get("/scinsight/health").json()["sap_write_enabled"] is False
    hits = c.post("/scinsight/api/v1/rag/search", json={"query": "Who must approve a warehouse stock transfer?"}, headers=key("planner")).json()
    assert hits["results"] and hits["results"][0]["citation"]["doc_id"] == "POL-WH-020"
    assert c.post("/scinsight/api/v1/rag/search", json={"query": "x"}, headers=manager_headers).status_code == 401  # gateway keys are not SCInsight keys
    assert c.post("/scinsight/api/v1/sap/purchase-orders", json={}, headers=key("planner")).status_code == 405  # SAP stays read-only
    paths = c.get("/openapi.json").json()["paths"]
    assert "/scinsight/api/v1/decisions" in paths and "/health" in paths  # one OpenAPI document, one Swagger (/docs)
    assert c.get("/").status_code == 200  # the dashboard still answers at the root


def test_rag_tuning_page_reaches_the_scinsight_routes_in_process(settings, manager_headers, assistant_headers):
    c = fused(settings)
    assert c.get("/api/v1/rag-tuning/config", headers=manager_headers).json()["active"]["name"] == "baseline"
    assert c.get("/api/v1/rag-tuning/documents", headers=assistant_headers).json()["summary"]["documents"] == 8
    assert c.post("/api/v1/rag-tuning/publish", json={"config_id": "RCFG-00000000", "confirm": True}, headers=assistant_headers).status_code == 403
