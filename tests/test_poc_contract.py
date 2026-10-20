"""POC contract endpoints (short REST paths for Flowise / LangGraph HTTP nodes) and tenant-scoped authorization."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.store import Store


def test_sap_read_endpoints_are_read_only(client, assistant_headers):
    inv = client.get("/sap/inventory?plant=DC21", headers=assistant_headers).json()
    assert inv["count"] and all(i["plant"] == "DC21" for i in inv["items"]) and "read-only" in inv["source"]
    orders = client.get("/sap/production-orders", headers=assistant_headers).json()
    assert {o["order"] for o in orders["items"]} >= {"10000101", "10000102"}
    assert client.post("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_MaterialStock", json={}, headers=assistant_headers).status_code == 405
    assert client.get("/sap/inventory").status_code == 401


def test_forecasts_and_optimizers(client, assistant_headers):
    demand = client.post("/forecast/demand", json={"material": "FG-PERFUME-100", "warehouse": "DC21", "horizon_days": 14}, headers=assistant_headers).json()
    assert demand["analysis_id"].startswith("AN-") and demand["forecasts"]
    lt = client.post("/forecast/supplier-lead-time", json={"supplier": "AirlessPack Asia"}, headers=assistant_headers).json()
    assert lt["contract_lead_time_days"] == 42 and lt["predicted_lead_time_days"] == 55 and lt["receipts"] >= 1
    assert lt["p90_lead_time_days"] >= lt["predicted_lead_time_days"] and lt["method"].startswith("empirical")
    ready = client.post("/optimizer/material-readiness", json={"plant": "FR20", "material": "FG-SERUM-50", "quantity": 6000, "need_by": "2026-10-27"},
                        headers=assistant_headers).json()
    assert ready["status"] == "not_ready" and ready["component_readiness_pct"] == 50.0  # RM-ACTIVE + cartons short
    transfer = client.post("/optimizer/warehouse-transfer", json={"material": "FG-PERFUME-100"}, headers=assistant_headers).json()
    assert any(a["action"] == "stock_transfer" and a["to"] == "DC21" for a in transfer["proposed_actions"])


def test_decision_lifecycle_human_review_and_reconciliation(client, assistant_headers, manager_headers):
    transfer = client.post("/optimizer/warehouse-transfer", json={"material": "FG-PERFUME-100"}, headers=assistant_headers).json()
    decision = client.post("/decisions", json={"analysis_id": transfer["analysis_id"], "explanation": "move stock to Dubai"}, headers=assistant_headers)
    assert decision.status_code == 201
    did = decision.json()["id"]
    assert client.post(f"/decisions/{did}/human-review", json={"decision": "accepted"}, headers=assistant_headers).status_code == 403  # human manager only
    reviewed = client.post(f"/decisions/{did}/human-review", json={"decision": "accepted", "modified": True, "reason_code": "timing"}, headers=manager_headers).json()
    assert reviewed["status"] == "accepted" and reviewed["sap_written"] is False
    assert client.post("/outcomes/reconcile", json={"decision_id": did, "sap_document": "5000001"}, headers=manager_headers).status_code == 409  # not executed yet
    client.post(f"/api/v1/recommendations/{did}/execute", json={}, headers=manager_headers).raise_for_status()
    expected = sum(a["quantity"] for a in transfer["proposed_actions"] if a["action"] == "stock_transfer")
    late = client.post("/outcomes/reconcile", json={"decision_id": did, "sap_document": "5000001", "actual_quantity": expected, "actual_date": "2026-12-31",
                                                     "note": "goods receipt at DC21"}, headers=manager_headers).json()
    assert late["achieved"] is False and late["reconciliation"]["checks"] == {"quantity_in_full": True, "on_time": False}
    assert late["reconciliation"]["days_late"] > 0
    assert client.post("/outcomes/reconcile", json={"decision_id": did, "sap_document": "5000001"}, headers=manager_headers).status_code == 409  # once
    perf = client.get("/learning/model-performance", headers=assistant_headers).json()
    assert perf["models"] and perf["summary"]["observed"] >= 1


def test_tenant_scoped_authorization(settings):
    scoped = settings.model_copy(update={"tenant_scopes": "flowise=cosmetics/aurelia|cosmetics/lumiere;manager=*"})
    c = TestClient(__import__("backend.app.main", fromlist=["create_app"]).create_app(scoped, Store.memory()))
    planner, manager = {"X-API-Key": "test-assistant"}, {"X-API-Key": "test-manager"}
    assert c.get("/sap/inventory", headers=planner).status_code == 200  # default tenant (Aurelia) is in scope
    assert c.get("/sap/inventory", headers={**planner, "X-Tenant": "cosmetics/lumiere"}).status_code == 200
    denied = c.get("/sap/inventory", headers={**planner, "X-Tenant": "pharmaceutical/medivia"})
    assert denied.status_code == 403 and "not authorized for tenant" in denied.json()["detail"]
    assert c.get("/api/v1/roles/director", headers={**planner, "X-Tenant": "automotive/voltara"}).status_code == 403  # every route, not just the contract
    assert c.get("/sap/inventory", headers={**manager, "X-Tenant": "pharmaceutical/medivia"}).status_code == 200  # "*" = all tenants
    events = c.get("/api/v1/audit?limit=20", headers=manager).json()["events"]
    assert any(e["action"] == "auth.tenant_forbidden" for e in events)


def test_contract_is_documented_in_openapi(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for path, method in [("/sap/inventory", "get"), ("/sap/production-orders", "get"), ("/forecast/demand", "post"), ("/forecast/supplier-lead-time", "post"),
                         ("/optimizer/material-readiness", "post"), ("/optimizer/warehouse-transfer", "post"), ("/decisions", "post"),
                         ("/decisions/{decision_id}/human-review", "post"), ("/outcomes/reconcile", "post"), ("/learning/model-performance", "get")]:
        assert method in paths[path], path
        assert "POC contract (Flowise / LangGraph REST)" in paths[path][method]["tags"]
