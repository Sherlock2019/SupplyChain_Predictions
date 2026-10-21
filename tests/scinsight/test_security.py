"""Security and reliability tests (brief section 17)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.scinsight.app import create_app
from backend.scinsight.db import Database
from tests.scinsight.conftest import key, settings


def test_unauthenticated_and_invalid_keys(client):
    assert client.get("/api/v1/sap/inventory").status_code == 401
    assert client.get("/api/v1/sap/inventory", headers={"X-API-Key": "nope"}).status_code == 401
    assert client.get("/api/v1/sap/inventory", headers={"Authorization": "Bearer sci-dev-agent-key"}).status_code == 200  # OpenAI-style bearer works


def test_configured_keys_rotate_out_stored_dev_keys():
    db = Database("sqlite:///:memory:")
    create_app(settings(), db)  # first start stores the public dev keys
    rotated = TestClient(create_app(settings(sci_agent_key="sci-agent-rotated-0123456789"), db))
    assert rotated.get("/api/v1/sap/warehouses", headers=key("agent")).status_code == 401
    assert rotated.get("/api/v1/sap/warehouses", headers={"X-API-Key": "sci-agent-rotated-0123456789"}).status_code == 200


def test_postgres_deployment_refuses_to_start_without_all_keys():
    with pytest.raises(RuntimeError, match="SCI_PLANNER_KEY"):
        create_app(settings(sci_database_url="postgresql://u:p@127.0.0.1:1/none", sci_agent_key="k"))


def test_forged_tenant_is_rejected_and_audited(client):
    assert client.get("/api/v1/sap/warehouses", headers={**key("agent"), "X-Tenant": "northwind-pharma"}).status_code == 403
    events = client.get("/api/v1/audit?limit=20", headers=key("director")).json()
    assert any(e["action"] == "auth.forged_tenant" for e in events["events"]) and events["chain_valid"]


def test_cross_tenant_data_is_invisible(client):
    rec = client.get("/api/v1/decisions/REC-HIST-0001", headers=key("other_tenant"))
    assert rec.status_code == 404
    inv = client.get("/api/v1/sap/inventory?item_id=SUN-SPF50-100", headers=key("other_tenant")).json()
    assert {b["location"] for b in inv["batches"]} == {"WH-X"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_sap_writes_are_blocked(client, method):
    response = getattr(client, method)("/api/v1/sap/purchase-orders", headers=key("director"))
    assert response.status_code == 405


def test_sap_write_enabled_refuses_to_start():
    with pytest.raises(RuntimeError, match="not allowed in Phase 1"):
        create_app(settings(sap_write_enabled=True), Database("sqlite:///:memory:"))


def test_expired_snapshot_blocks_calculations():
    app = create_app(settings(sci_business_date="2026-10-30"), Database("sqlite:///:memory:"))
    c = TestClient(app)
    r = c.post("/api/v1/optimizer/material-readiness", json={"production_order_id": "PRD-1001"}, headers=key("agent"))
    assert r.status_code == 409 and "days old" in r.json()["detail"]


def test_missing_snapshot_blocks_calculations(app, client):
    app.state.db.execute("update sap_snapshots set status='expired' where tenant_id='scinsight-cosmetics'")
    assert client.get("/api/v1/sap/inventory", headers=key("agent")).status_code == 409


def test_invalid_bom_and_unit_mismatch_are_explained(client):
    r = client.post("/api/v1/optimizer/material-readiness", json={"sku": "SER-RETI-30", "quantity": 6000, "need_date": "2026-11-16"}, headers=key("agent"))
    assert r.status_code == 422 and "unit of measure mismatch" in r.json()["detail"]
    old = client.post("/api/v1/optimizer/material-readiness", json={"sku": "SER-VITC-30", "quantity": 10, "need_date": "2024-06-01"}, headers=key("agent"))
    assert old.status_code == 422 and "no approved BOM" in old.json()["detail"]


def test_malformed_and_injected_tool_arguments(client):
    bad = [("/api/v1/optimizer/material-readiness", {"sku": "SER-VITC-30"}),                                   # incomplete
           ("/api/v1/optimizer/warehouse-balancing", {"sku": "SUN-SPF50-100; DROP TABLE users"}),             # injection in a code
           ("/api/v1/optimizer/warehouse-balancing", {"sku": "SUN-SPF50-100", "approve": True}),             # unexpected field
           ("/api/v1/forecast/demand", {"sku": "SUN-SPF50-100", "warehouse": "WH-B", "horizon_days": 5000}),  # out of range
           ("/api/v1/decisions", {"calculation_id": "not-a-calc"})]
    for path, body in bad:
        assert client.post(path, json=body, headers=key("agent")).status_code == 422, path


def test_unknown_calculation_and_no_action_calculation(client):
    assert client.post("/api/v1/decisions", json={"calculation_id": "CALC-DOESNOTEXIST"}, headers=key("agent")).status_code == 404
    forecast = client.post("/api/v1/forecast/demand", json={"sku": "SUN-SPF50-100", "warehouse": "WH-B"}, headers=key("agent")).json()
    assert client.post("/api/v1/decisions", json={"calculation_id": forecast["calculation_id"]}, headers=key("agent")).status_code == 422


def test_roles_are_enforced_server_side(client):
    assert client.post("/api/v1/decisions", json={"calculation_id": "CALC-ANY12345"}, headers=key("mlops")).status_code == 403
    calc = client.post("/api/v1/optimizer/warehouse-balancing", json={"sku": "SUN-SPF50-100", "target_warehouse": "WH-B"}, headers=key("agent")).json()
    rec = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent")).json()
    review = {"decision": "approve", "explanation": "Approving on behalf of the director."}
    for slot in ("agent", "sap_executor", "mlops", "procurement", "other_tenant"):
        assert client.post(f"/api/v1/decisions/{rec['id']}/review", json=review, headers=key(slot)).status_code in (403, 404), slot


def test_incomplete_outcome_is_not_used_for_training(app, client):
    db = app.state.db
    db.execute("update purchase_orders set received_quantity=20000 where po_id='PO-4500020950'")
    out = client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": "REC-HIST-0001"}, headers=key("agent")).json()
    assert out["status"] == "incomplete" and out["approved_for_training"] is False and out["quality_flags"]


def test_pending_outcome_is_reported_not_invented(app, client):
    app.state.db.execute("update purchase_orders set received_date=null, received_quantity=null where po_id='PO-4500020950'")
    out = client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": "REC-HIST-0001"}, headers=key("agent")).json()
    assert out["status"] == "pending"


def test_concurrent_reviews_cannot_both_win(client):
    calc = client.post("/api/v1/optimizer/warehouse-balancing", json={"sku": "SUN-SPF50-100", "target_warehouse": "WH-B"}, headers=key("agent")).json()
    rec = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent")).json()
    a = client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "approve", "explanation": "first reviewer"}, headers=key("warehouse"))
    b = client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "reject", "explanation": "second reviewer"}, headers=key("director"))
    assert (a.status_code, b.status_code) == (200, 409)
    assert len(client.get(f"/api/v1/decisions/{rec['id']}", headers=key("planner")).json()["reviews"]) == 1
