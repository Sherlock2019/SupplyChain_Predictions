"""The three required business scenarios, the human-review lifecycle and the outcome-learning loop, through the HTTP API."""
from __future__ import annotations

from tests.scinsight.conftest import key


def test_scenario_1_factory_material_shortage(client):
    r = client.post("/api/v1/optimizer/material-readiness", json={"production_order_id": "PRD-1001"}, headers=key("agent"))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "short" and body["calculation_id"].startswith("CALC-")
    assert body["shortages"] == [{"material_id": "PUMP-DISP-24", "missing": 20000.0, "uom": "EA", "required_date": "2026-10-27"}]
    pump = next(line for line in body["lines"] if line["material_id"] == "PUMP-DISP-24")
    assert pump["required_quantity"] == 50000 and pump["usable"] == 30000 and pump["confirmed_timely_inbound"] == 0
    assert [e["batch_id"] for e in pump["excluded_stock"]] == ["P-BLK-03"]
    assert [p["po_id"] for p in pump["late_purchase_orders"]] == ["PO-4500021001"]
    assert [p["po_id"] for p in pump["unconfirmed_purchase_orders"]] == ["PO-4500021002"]
    unvetted = next(o for o in pump["supply_options"] if o.get("supplier_id") == "SUP-X")
    assert unvetted["feasible"] is False and "not approved" in unvetted["reasons"][0]
    assert not any(o["recommended"] for o in pump["supply_options"])  # nothing arrives in time from an approved supplier
    assert body["partial_production_possible"] == 30000
    actions = {a["action"]: a for a in body["proposed_actions"]}
    assert actions["purchase_request"]["supplier_id"] == "SUP-A" and actions["purchase_request"]["arrives_in_time"] is False
    assert actions["replan_production"]["produce_now"] == 30000
    assert body["provenance"]["synthetic"] is True and body["provenance"]["snapshot_id"]


def test_production_order_quantity_cannot_be_overridden(client):
    # a model once sent PRD-1001 with an invented quantity of 500; the order's SAP quantity must win, so the request is refused
    r = client.post("/api/v1/optimizer/material-readiness", json={"production_order_id": "PRD-1001", "quantity": 500}, headers=key("agent"))
    assert r.status_code == 422 and "alone" in r.text


def test_scenario_2_three_warehouse_balancing(client):
    body = client.post("/api/v1/optimizer/warehouse-balancing", json={"sku": "SUN-SPF50-100", "target_warehouse": "WH-B"}, headers=key("agent")).json()
    wh_b = next(p for p in body["positions"] if p["warehouse"] == "WH-B")
    assert wh_b["usable"] == 1200 and wh_b["days_of_cover"] == 6.0
    best = body["options"][0]
    assert best["donor"] == "WH-C" and best["recommended"] and best["in_time"] and best["covers_need"]
    excluded = {e["batch_id"] for e in best["not_transferable"]}
    assert {"S-C-02", "S-C-03", "S-C-04", "S-C-05", "S-C-06"} <= excluded  # near-expiry, expired, blocked, reserved, inspection never move
    assert best["quantity"] <= 3000 - 0  # never more than the long-dated released batch
    partial = next(o for o in body["options"] if o.get("donor") == "WH-A")
    assert partial["covers_need"] is False
    assert body["proposed_actions"][0]["from"] == "WH-C" and body["proposed_actions"][0]["cost_eur"] == best["cost_eur"]


def test_scenario_3_expiry_and_quality_protection(client):
    q = client.post("/api/v1/quality/check-stock", json={"item_id": "SUN-SPF50-100", "location": "WH-C"}, headers=key("agent")).json()
    assert q["on_hand"] == 7500 and q["usable"] == 4500
    reasons = {e["batch_id"]: e["reason"] for e in q["excluded"]}
    assert reasons == {"S-C-03": "expired 2026-10-15", "S-C-04": "QA blocked", "S-C-05": "reserved for a customer order",
                       "S-C-06": "not released by quality (inspection)"}
    assert [n["batch_id"] for n in q["near_expiry"]] == ["S-C-02"]
    assert q["proposed_actions"] == [{"action": "block_for_destruction_review", "batch_id": "S-C-03", "quantity": 800.0}]


def test_decision_lifecycle_requires_an_authorised_human(client):
    calc = client.post("/api/v1/optimizer/warehouse-balancing", json={"sku": "SUN-SPF50-100", "target_warehouse": "WH-B"}, headers=key("agent")).json()
    created = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent"))
    assert created.status_code == 201
    rec = created.json()
    assert rec["status"] == "pending_review" and rec["domain"] == "warehouse" and rec["proposed_actions"][0]["quantity"] == calc["proposed_actions"][0]["quantity"]
    replay = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent")).json()
    assert replay["id"] == rec["id"] and replay["idempotent_replay"]  # idempotent
    review = {"decision": "approve", "explanation": "Move the long-dated batch to Madrid."}
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json=review, headers=key("agent")).status_code == 403   # Flowise cannot approve
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json=review, headers=key("quality")).status_code == 403  # wrong domain
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "modify", "explanation": "less"}, headers=key("warehouse")).status_code == 422
    ok = client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "modify", "explanation": "Ship 1,800 to keep a buffer.",
                                                                    "modifications": {"quantity": 1800}}, headers=key("warehouse"))
    assert ok.status_code == 200 and ok.json()["status"] == "modified" and ok.json()["sap_written"] is False and ok.json()["verified_review"]
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json=review, headers=key("director")).status_code == 409  # decided once
    exe = {"sap_document": "STO-4600001234", "doc_type": "stock_transport_order", "executed_at": "2026-10-21T15:00:00Z"}
    assert client.post(f"/api/v1/decisions/{rec['id']}/sap-execution", json=exe, headers=key("agent")).status_code == 403
    done = client.post(f"/api/v1/decisions/{rec['id']}/sap-execution", json=exe, headers=key("sap_executor")).json()
    assert done["status"] == "executed" and done["sap_execution"][0]["source"] == "manual_sap_execution_record"
    pending = client.get("/api/v1/decisions?status=pending_review", headers=key("planner")).json()
    assert all(r["id"] != rec["id"] for r in pending)


def test_defer_then_review_and_withdraw(client):
    calc = client.post("/api/v1/optimizer/material-readiness", json={"production_order_id": "PRD-1001"}, headers=key("agent")).json()
    rec = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent")).json()
    assert rec["domain"] == "factory" and rec["risk_level"] == "high"
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "defer", "explanation": "Waiting for Supplier A."},
                       headers=key("planner")).json()["status"] == "deferred"
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "approve", "explanation": "Approved after call."},
                       headers=key("planner")).json()["status"] == "approved"
    other = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"], "idempotency_key": "second-copy"}, headers=key("agent")).json()
    assert client.post(f"/api/v1/decisions/{other['id']}/withdraw", headers=key("planner")).status_code == 403  # not the creator
    assert client.post(f"/api/v1/decisions/{other['id']}/withdraw", headers=key("agent")).json()["status"] == "withdrawn"


def test_outcome_learning_loop_and_model_governance(client):
    rec = client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": "REC-HIST-0001"}, headers=key("agent")).json()
    assert rec["status"] == "verified" and rec["error"] == {"predicted": 5.0, "actual": 9.0, "signed_error": 4.0, "absolute_error": 4.0, "percentage_error": 80.0}
    assert rec["human_decision"] == "approve" and rec["approved_for_training"] is True and rec["source_document"] == "PO-4500020950"
    again = client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": "REC-HIST-0001"}, headers=key("agent")).json()
    assert again["status"] == "already_reconciled"
    metrics = client.get("/api/v1/learning/metrics", headers=key("director")).json()
    assert metrics["verified_outcome_coverage"]["verified"] == 1 and metrics["supplier_lead_time_mae_days"]["value"] == 4.0
    assert metrics["stockout_warning_accuracy"]["value"] is None  # never invented
    assert client.post("/api/v1/learning/train-lead-time-model", headers=key("director")).status_code == 403
    trained = client.post("/api/v1/learning/train-lead-time-model", headers=key("mlops")).json()
    assert trained["status"] == "candidate" and trained["holdout_rows"] > 0 and set(trained["baselines"]) == {"contract_lead_time_mae_days", "supplier_mean_mae_days"}
    assert client.post(f"/api/v1/learning/models/{trained['model_version_id']}/promote", headers=key("mlops")).status_code == 403
    promo = client.post(f"/api/v1/learning/models/{trained['model_version_id']}/promote", headers=key("director"))
    assert promo.status_code == (200 if trained["beats_best_baseline"] else 409)  # the gate decides, not the caller
    rr = client.post("/api/v1/learning/retraining-requests", json={"reason": "Supplier A deliveries are 4 days later than predicted."}, headers=key("agent")).json()
    assert rr["status"] == "pending_human_approval" and rr["evidence"]["verified_learning_records"] == 1


def test_purchase_request_carries_a_reconcilable_lead_time_prediction(client):
    calc = client.post("/api/v1/optimizer/replenishment", json={"item_id": "PUMP-DISP-24", "location": "FAC-1", "quantity": 20000, "need_date": "2026-10-27"},
                       headers=key("agent")).json()
    action = calc["proposed_actions"][0]
    assert action["action"] == "purchase_request" and action["lead_days"] == 9.0  # demonstrated, not the 5-day contract figure
    rec = client.post("/api/v1/decisions", json={"calculation_id": calc["calculation_id"]}, headers=key("agent")).json()
    assert rec["domain"] == "procurement" and rec["prediction"]["metric"] == "lead_time_days" and rec["prediction"]["predicted"] == 9.0
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "approve", "explanation": "fine"}, headers=key("warehouse")).status_code == 403
    assert client.post(f"/api/v1/decisions/{rec['id']}/review", json={"decision": "approve", "explanation": "Order from Alpine."},
                       headers=key("procurement")).json()["status"] == "approved"
    taken = {"sap_document": "PO-4500020950", "doc_type": "purchase_order", "executed_at": "2026-09-30T09:00:00Z"}
    assert client.post(f"/api/v1/decisions/{rec['id']}/sap-execution", json=taken, headers=key("sap_executor")).status_code == 409  # linked to REC-HIST-0001
    pos = client.get("/api/v1/sap/purchase-orders?material_id=PUMP-DISP-24&supplier_id=SUP-A", headers=key("agent")).json()["items"]
    po = next(x for x in pos if x["received_date"] and x["po_id"] != "PO-4500020950")
    exe = {"sap_document": po["po_id"], "doc_type": "purchase_order", "executed_at": f"{po['order_date']}T09:00:00Z"}
    assert client.post(f"/api/v1/decisions/{rec['id']}/sap-execution", json=exe, headers=key("sap_executor")).json()["status"] == "executed"
    out = client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": rec["id"]}, headers=key("agent")).json()
    assert out["status"] == "verified" and out["error"]["predicted"] == 9.0 and out["source_document"] == po["po_id"]
    assert out["error"]["signed_error"] == out["error"]["actual"] - 9.0


def test_reconcile_requires_executed_recommendation(client):
    calc = client.post("/api/v1/forecast/lead-time", json={"supplier_id": "SUP-A", "material_id": "PUMP-DISP-24"}, headers=key("agent")).json()
    assert calc["estimate"]["receipts"] >= 3 and calc["predicted_lead_time_days"] > calc["estimate"]["contract_days"]
    assert client.post("/api/v1/outcomes/reconcile", json={"recommendation_id": "REC-NOPE0000"}, headers=key("agent")).status_code == 404


def test_demand_forecast_has_backtest_and_feeds_metrics(client):
    f = client.post("/api/v1/forecast/demand", json={"sku": "SUN-SPF50-100", "warehouse": "WH-B", "horizon_days": 7}, headers=key("agent")).json()
    assert len(f["forecast"]) == 7 and f["backtest"]["wape_pct"] < 25 and f["method"].startswith("baseline")
    assert client.get("/api/v1/learning/metrics", headers=key("planner")).json()["demand_forecast_wape_pct"]["value"] == f["backtest"]["wape_pct"]


def test_rag_is_tenant_scoped_cited_and_flags_injection(client, app):
    report = app.state.ingest_report
    assert any("missing front matter" in r for r in report["rejected"])  # invalid document rejected at ingestion
    hits = client.post("/api/v1/rag/search", json={"query": "pump dispenser supplier agreement expedite lead time"}, headers=key("procurement")).json()["results"]
    assert hits and all(h["citation"]["doc_id"] and h["citation"]["version"] for h in hits)
    assert all(h["citation"]["doc_id"] != "POL-NW-001" for h in hits)
    flagged = [h for h in hits if h["flags"]]
    assert flagged and flagged[0]["citation"]["doc_id"] == "AGR-SUP-A-002"
    other = client.post("/api/v1/rag/search", json={"query": "distribution policy"}, headers=key("other_tenant")).json()["results"]
    assert {h["citation"]["doc_id"] for h in other} == {"POL-NW-001"}  # the other tenant only ever sees its own documents
