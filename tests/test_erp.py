"""ERP / SAP Setup — integration tests against the SAP S/4HANA OData V2 EMULATOR (backend/app/erp/emulator.py) through an httpx
MockTransport. These are mock tests: no real SAP system is contacted."""
from __future__ import annotations

import base64
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.config import ROOT
from backend.app.erp.emulator import USER, build_entities, respond
from backend.app.store import Store

PASSWORD = "emulator-secret-123"
OTHER = "automotive/kestrel"


def emulator_transport() -> httpx.MockTransport:
    entities = build_entities(json.loads((ROOT / "data" / "sap_mock.json").read_text(encoding="utf-8")))

    def handle(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "sap.down.test":
            raise httpx.ConnectError("connection refused", request=request)
        if request.url.path == "/oauth/token":
            ok = request.headers.get("authorization") == "Basic " + base64.b64encode(f"cid:{PASSWORD}".encode()).decode()
            return httpx.Response(200 if ok else 401, json={"access_token": "tok-1"} if ok else {})
        headers = {k.lower(): v for k, v in request.headers.items()}
        if headers.get("authorization") == "Bearer tok-1":
            headers["authorization"] = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        status, body, ctype = respond(entities, PASSWORD, request.method, request.url.path, dict(request.url.params), headers)
        return httpx.Response(status, text=body, headers={"content-type": ctype})

    return httpx.MockTransport(handle)


@pytest.fixture()
def app(settings):
    from backend.app.main import create_app

    settings.flowise_url = ""
    application = create_app(settings, Store.memory())
    application.state.erp.transport = emulator_transport()
    return application


@pytest.fixture()
def c(app) -> TestClient:
    return TestClient(app)


M = {"X-API-Key": "test-manager"}
A = {"X-API-Key": "test-assistant"}
LIVE = {"name": "S/4HANA test", "provider": "sap_s4hana", "environment": "development", "mode": "read_only_live", "protocol": "odata_v2",
        "base_url": "https://sap.example.test", "sap_client": "100", "auth": "basic", "username": USER, "secret_ref": "stored", "secret": PASSWORD}


def live(c, **over) -> dict:
    r = c.post("/api/v1/erp/connections", json={**LIVE, **over}, headers=M)
    assert r.status_code == 201, r.text
    return r.json()


def snapshot_id(c, headers=M) -> str:
    return c.get("/api/v1/snapshot", headers=headers).json()["id"]


def test_a_mock_sap_connection(c):
    builtin = snapshot_id(c)
    conn = c.post("/api/v1/erp/connections", json={"name": "Mock SAP", "provider": "mock_sap", "mode": "mock"}, headers=M).json()
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/test", headers=M).json()["ok"]
    entities = c.get(f"/api/v1/erp/connections/{conn['id']}/entities", headers=M).json()["entities"]
    assert {e["section"] for e in entities if e["available"]} >= {"materials", "stock", "production_orders", "suppliers"}
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/validate", headers=M).json()["valid"]
    act = c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).json()
    assert act["snapshot_id"] == builtin == snapshot_id(c)
    check = c.post("/api/v1/erp/validate-integrations", headers=M).json()
    by = {r["component"]: r for r in check["results"]}
    assert by["FastAPI SAP adapter"]["status"] == "pass" and by["Business analytics engine"]["status"] == "pass"
    assert by["Flowise Chatflow"]["status"] == "n/a" and by["LangGraph"]["status"] == "n/a"  # not configured here: never shown green
    assert by["Audit & monitoring"]["status"] == "pass"
    assert c.get("/api/v1/erp/integration-status", headers=A).json()["last_check"]["snapshot"] == builtin


def test_b_live_connection_sync_activate_and_rollback(c):
    builtin = snapshot_id(c)
    before = c.get("/api/v1/inventory", headers=A).json()
    before.pop("snapshot")
    conn = live(c)
    assert conn["secret_set"] and "secret" not in conn["config"] and PASSWORD not in json.dumps(conn)
    test = c.post(f"/api/v1/erp/connections/{conn['id']}/test", headers=M).json()
    assert test["ok"] and test["activated"] is False and snapshot_id(c) == builtin  # a test never activates
    services = {e["service"]: e["entity_sets"] for e in c.get(f"/api/v1/erp/connections/{conn['id']}/entities", headers=M).json()["entities"]}
    assert "A_MatlStkInAcctMod" in services["/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV"]
    preview = c.post(f"/api/v1/erp/connections/{conn['id']}/preview", json={"section": "stock", "top": 3}, headers=M).json()
    assert len(preview["rows"]) == 3 and {"plant", "material", "quantity", "status"} <= set(preview["rows"][0])
    # activation needs a validated mapping and a validated sync
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).status_code == 422
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/validate", headers=M).json() == {"valid": True, "problems": []}
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).status_code == 422
    job = c.post(f"/api/v1/erp/connections/{conn['id']}/sync", headers=M).json()
    assert job["status"] == "validated", job["errors"]
    assert job["counts"]["stock"] > 0 and "materials" in job["carried"] and snapshot_id(c) == builtin  # a sync never activates
    act = c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).json()
    new = act["snapshot_id"]
    assert new.startswith("ERP-") and new != builtin and act["previous_snapshot_id"] is None
    # every business service now computes on the new snapshot (the emulator reports +10% unrestricted stock)
    assert snapshot_id(c) == new
    assert c.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_MaterialStock?$top=1", headers=A).json()["__snapshot"] == new
    order = c.get("/sap/production-orders", headers=A).json()["items"][0]
    readiness = c.post("/api/v1/analysis/factory-readiness", json={"plant": order["plant"], "material": order["material"], "quantity": order["quantity"],
                                                                  "need_by": order["finish_date"]}, headers=A).json()
    assert readiness["snapshot"]["id"] == new
    after = c.get("/api/v1/inventory", headers=A).json()
    after.pop("snapshot")
    assert after != before
    health = c.get(f"/api/v1/erp/connections/{conn['id']}/health", headers=A).json()
    assert health["status"] == "connected" and health["active"] and health["records_synced"] > 0 and health["tenant_snapshot"]["id"] == new
    actions = [e["action"] for e in c.get(f"/api/v1/erp/connections/{conn['id']}/logs", headers=A).json()["events"]]
    assert {"erp.connection_created", "erp.connection_tested", "erp.sync_completed", "erp.connection_activated"} <= set(actions)
    # rollback returns to the snapshot that was active before
    back = c.post(f"/api/v1/erp/connections/{conn['id']}/rollback", headers=M).json()
    assert back["snapshot_id"] == builtin == snapshot_id(c)


def test_c_failures_keep_the_active_snapshot(c):
    good = live(c)
    for step in ("test", "validate", "sync"):
        c.post(f"/api/v1/erp/connections/{good['id']}/{step}", headers=M)
    active = c.post(f"/api/v1/erp/connections/{good['id']}/activate", headers=M).json()["snapshot_id"]
    down = live(c, name="unreachable", base_url="https://sap.down.test")
    test = c.post(f"/api/v1/erp/connections/{down['id']}/test", headers=M).json()
    assert not test["ok"] and "not reachable" in test["error"]
    job = c.post(f"/api/v1/erp/connections/{down['id']}/sync", headers=M).json()
    assert job["status"] == "failed" and job["errors"] and job["snapshot_id"] is None
    assert c.post(f"/api/v1/erp/connections/{down['id']}/activate", headers=M).status_code == 422
    assert snapshot_id(c) == active
    assert c.get(f"/api/v1/erp/connections/{down['id']}/health", headers=A).json()["status"] == "error"
    assert "erp.connection_tested" in [e["action"] for e in c.get(f"/api/v1/erp/connections/{down['id']}/logs", headers=A).json()["events"]]
    wrong = live(c, name="wrong password", secret="nope")
    t = c.post(f"/api/v1/erp/connections/{wrong['id']}/test", headers=M).json()
    assert not t["ok"] and t["auth"] == "rejected" and "nope" not in json.dumps(t)
    # a configuration change must be tested again before activation; the active snapshot is untouched
    c.patch(f"/api/v1/erp/connections/{good['id']}", json={"timeout_seconds": 20}, headers=M)
    assert c.post(f"/api/v1/erp/connections/{good['id']}/activate", headers=M).status_code == 422
    assert snapshot_id(c) == active


def test_invalid_mapping_blocks_activation(c):
    conn = live(c)
    mapping = c.get(f"/api/v1/erp/connections/{conn['id']}/mappings", headers=A).json()["mapping"]
    mapping["stock"]["fields"]["quantity"] = "NoSuchProperty"
    del mapping["bom"]["fields"]["component"]
    assert c.put(f"/api/v1/erp/connections/{conn['id']}/mappings", json={"mapping": mapping}, headers=M).status_code == 200
    c.post(f"/api/v1/erp/connections/{conn['id']}/test", headers=M)
    v = c.post(f"/api/v1/erp/connections/{conn['id']}/validate", headers=M).json()
    assert not v["valid"] and any("NoSuchProperty" in p for p in v["problems"]) and any("component" in p for p in v["problems"])
    job = c.post(f"/api/v1/erp/connections/{conn['id']}/sync", headers=M).json()
    assert job["status"] == "failed"
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).status_code == 422


def test_oauth_client_credentials(c):
    conn = live(c, auth="oauth2_client_credentials", client_id="cid", token_url="https://sap.example.test/oauth/token", username="")
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/test", headers=M).json()["ok"]


def test_d_security(c, app):
    conn = live(c)
    # read-only users cannot change, test, sync or activate
    assert c.post("/api/v1/erp/connections", json=LIVE, headers=A).status_code == 403
    for method, path in [("patch", ""), ("post", "/test"), ("post", "/sync"), ("post", "/activate"), ("post", "/rollback"), ("put", "/mappings")]:
        r = getattr(c, method)(f"/api/v1/erp/connections/{conn['id']}{path}", json={} if method != "put" else {"mapping": {}}, headers=A)
        assert r.status_code == 403, (method, path)
    assert c.get(f"/api/v1/erp/connections/{conn['id']}", headers=A).status_code == 200  # reading is allowed
    # another customer cannot see or use this connection
    other = {**M, "X-Tenant": OTHER}
    assert c.get(f"/api/v1/erp/connections/{conn['id']}", headers=other).status_code == 404
    assert c.post(f"/api/v1/erp/connections/{conn['id']}/test", headers=other).status_code == 404
    assert c.get("/api/v1/erp/connections", headers=other).json()["connections"] == []
    # secrets never come back
    for path in ("", "/health", "/logs"):
        assert PASSWORD not in c.get(f"/api/v1/erp/connections/{conn['id']}{path}", headers=M).text
    assert PASSWORD not in json.dumps(app.state.store.audit_events(1000))
    # destination and environment rules
    bad = [{"base_url": "https://169.254.169.254"}, {"base_url": "ftp://sap.example.test"},
           {"environment": "production", "secret_ref": "env:SAP_SECRET", "base_url": "http://sap.example.test"},
           {"environment": "production", "secret_ref": "env:SAP_SECRET", "verify_tls": False},
           {"environment": "production"},  # stored secret: production needs a secrets-manager reference
           {"environment": "production", "secret_ref": "env:SAP_SECRET"},  # host not in ERP_ALLOWED_HOSTS
           {"mode": "approved_write"}, {"provider": "generic_rest", "protocol": "rest"}, {"sync_mode": "event"}]
    for over in bad:
        assert c.post("/api/v1/erp/connections", json={**LIVE, **over}, headers=M).status_code == 422, over
    # SAP writes stay blocked; agents cannot reach a write path
    assert c.post("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_PurchaseOrderItem", json={}, headers=A).status_code == 405


def test_activation_is_per_customer(c):
    other_before = snapshot_id(c, {**A, "X-Tenant": OTHER})
    conn = live(c)
    for step in ("test", "validate", "sync", "activate"):
        assert c.post(f"/api/v1/erp/connections/{conn['id']}/{step}", headers=M).status_code == 200, step
    assert snapshot_id(c).startswith("ERP-")
    assert snapshot_id(c, {**A, "X-Tenant": OTHER}) == other_before


def test_activation_survives_restart(settings, tmp_path):
    from backend.app.main import create_app

    settings.flowise_url = ""
    store = Store(f"sqlite:///{tmp_path / 'erp.sqlite'}")
    first = create_app(settings, store)
    first.state.erp.transport = emulator_transport()
    c = TestClient(first)
    conn = live(c)
    for step in ("test", "validate", "sync"):
        c.post(f"/api/v1/erp/connections/{conn['id']}/{step}", headers=M)
    new = c.post(f"/api/v1/erp/connections/{conn['id']}/activate", headers=M).json()["snapshot_id"]
    restarted = TestClient(create_app(settings, store))
    assert snapshot_id(restarted) == new
