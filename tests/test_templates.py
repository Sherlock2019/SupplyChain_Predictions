"""The starter templates (templates/backend) run: each one is exercised the way its real counterpart is."""
from __future__ import annotations

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from templates.backend import fastapi_app, fastapi_router, langgraph_graph, mcp_server


def test_fastapi_template_auth_roles_validation_and_read_only_sap():
    c = TestClient(fastapi_app.create_app())
    reader, manager = {"X-API-Key": "dev-reader"}, {"X-API-Key": "dev-manager"}
    assert c.get("/api/v1/stock/SKU-001").status_code == 401
    assert c.get("/api/v1/stock/SKU-001", headers=reader).json()["on_hand"] == 120.0
    assert c.post("/api/v1/adjustments", json={"sku": "SKU-001", "quantity": 5}, headers=reader).status_code == 403
    assert c.post("/api/v1/adjustments", json={"sku": "bad sku", "quantity": 5}, headers=manager).status_code == 422
    assert c.post("/api/v1/adjustments", json={"sku": "SKU-001", "quantity": 5}, headers=manager).json()["on_hand"] == 125.0
    assert c.post("/api/v1/sap/purchase-orders", headers=manager).status_code == 405
    assert c.get("/api/v1/audit", headers=manager).json()[0]["action"] == "stock.adjusted"


def test_router_template_is_one_app_with_a_prefixed_module():
    c = TestClient(fastapi_router.create_app())
    assert c.get("/health").json()["service"] == "app"
    assert c.get("/inner/health").json() == {"status": "ok", "module": "inner"}
    assert c.get("/inner/api/v1/stock/SKU-001").status_code == 401
    assert c.get("/inner/api/v1/stock/SKU-001", headers={"X-API-Key": "dev-inner-key"}).json()["on_hand"] == 120.0
    assert "/inner/api/v1/stock/{sku}" in c.get("/openapi.json").json()["paths"]  # one Swagger for the whole app


def test_langgraph_template_interrupts_for_approval_then_resumes():
    g = langgraph_graph.build_graph(MemorySaver())
    cfg = {"configurable": {"thread_id": "t1"}}
    first = g.invoke({"question": "Should we transfer stock to B?"}, cfg)
    assert "__interrupt__" in first and "answer" not in first
    done = g.invoke(Command(resume="approved"), cfg)
    assert done["answer"] == "Transfer 120 units: approved"
    assert langgraph_graph.build_graph(MemorySaver()).invoke({"question": "status?"}, {"configurable": {"thread_id": "t2"}})["answer"] == "No action needed."


def test_backend_code_page_serves_each_apps_templates_and_nothing_else(client, assistant_headers):
    idx = client.get("/api/v1/code/files", headers=assistant_headers).json()
    templates = {c["id"]: c["templates"] for c in idx["components"]}
    assert templates == {"scinsight": ["fastapi_app.py"], "api": ["fastapi_router.py", "fastapi_app.py"],
                         "langgraph": ["langgraph_graph.py"], "mcp": ["mcp_server.py"]}
    t = client.get("/api/v1/code/template", params={"name": "langgraph_graph.py"}, headers=assistant_headers).json()
    assert t["template"] and "def build_graph" in t["source"]
    for bad in ("conftest.py", "..%2F.env", "main.py"):
        assert client.get("/api/v1/code/template", params={"name": bad}, headers=assistant_headers).status_code in (404, 422)


def test_mcp_template_tools_are_read_only_and_the_endpoint_needs_a_key(monkeypatch):
    assert '"on_hand": 120.0' in mcp_server.stock_level("SKU-001") and mcp_server.low_stock() == '["SKU-002"]'
    monkeypatch.setenv("TPL_MCP_KEYS", "k1")
    with TestClient(mcp_server.create_mcp_app()) as c:
        assert c.post("/mcp", json={}).status_code == 401
