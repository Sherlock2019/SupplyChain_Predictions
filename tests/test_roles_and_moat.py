"""Role-centred decision views, decision outcome learning and the customer data intelligence moat."""
from __future__ import annotations

import pytest

from backend.app.graphs import _role_setup
from backend.app.roles import ROLES

TENANTS = ["cosmetics/aurelia", "pharmaceutical/medivia", "automotive/voltara", "food/verdant", "ecommerce/shopnova"]


def test_catalogue_puts_the_five_mvp_roles_first(client, assistant_headers):
    roles = client.get("/api/v1/roles", headers=assistant_headers).json()
    assert [r["id"] for r in roles][:5] == ["director", "demand", "production", "procurement", "warehouse"]
    assert all(r["mvp"] for r in roles[:5]) and not any(r["mvp"] for r in roles[5:])
    assert {r["agent"] for r in roles} >= {"Supervisor Agent", "Forecast Agent", "Factory Agent", "Procurement Agent", "Inventory Agent", "Learning Agent"}


@pytest.mark.parametrize("tenant", TENANTS)
def test_every_role_answers_the_four_questions(client, assistant_headers, tenant):
    h = {**assistant_headers, "X-Tenant": tenant}
    for role in ROLES:
        v = client.get(f"/api/v1/roles/{role}", headers=h).json()
        assert v["kpis"], role
        for k in v["kpis"]:  # every KPI has an agreed definition; missing source data is said, never invented
            assert k["definition"] and k["formula"] and k["source"]
            if not k["available"]:
                assert k["value"] is None and k["hint"].startswith("needs SAP data")
        assert {"at_risk_eur", "fix_cost_eur", "note"} <= set(v["cost"])
        assert all(a["action"]["kind"] and a["action"]["label"] for a in v["actions"])
        assert all(p["basis"] for p in v["predictions"])
        assert v["agent"]["name"] == ROLES[role]["agent"] and v["agent"]["starters"]


def test_role_views_know_the_aurelia_situation(client, assistant_headers):
    director = client.get("/api/v1/roles/director", headers=assistant_headers).json()
    labels = [k["label"] for k in director["kpis"]]
    assert {"Customer OTIF (projected)", "Material readiness", "Inventory turnover", "Forecast WAPE"} <= set(labels)
    demand = client.get("/api/v1/roles/demand", headers=assistant_headers).json()
    assert any("runs out at DC22" in p["what"] for p in demand["predictions"])
    procurement = client.get("/api/v1/roles/procurement", headers=assistant_headers).json()
    assert any("likely arrives" in p["what"] for p in procurement["predictions"])
    warehouse = client.get("/api/v1/roles/warehouse", headers=assistant_headers).json()
    picking = next(k for k in warehouse["kpis"] if k["label"] == "Picking accuracy")
    assert picking["available"] is False  # no WM picking confirmations in the snapshot
    focused = client.get("/api/v1/roles/production?material=FG-SERUM-50", headers=assistant_headers).json()
    assert focused["product"]["material"] == "FG-SERUM-50"
    assert client.get("/api/v1/roles/nobody", headers=assistant_headers).status_code == 404


def test_north_star_platform_kpis_and_industry_kpis(client, assistant_headers):
    ns = client.get("/api/v1/northstar", headers=assistant_headers).json()
    assert "lowest sustainable supply-chain cost" in ns["statement"]
    assert [k["label"] for k in ns["platform_kpis"]] == ["Customer OTIF (projected)", "Material readiness", "Inventory turnover", "Forecast WAPE", "Supply-chain cost (30 d)"]
    assert ns["industry"]["industry"] == "cosmetics"
    assert [k["label"] for k in ns["industry"]["kpis"]][0] == "Packaging readiness"
    pharma = client.get("/api/v1/northstar", headers={**assistant_headers, "X-Tenant": "pharmaceutical/medivia"}).json()
    assert pharma["industry"]["industry"] == "pharmaceutical" and "GMP" in pharma["industry"]["rules"]


def test_approval_is_not_proof_until_the_outcome_is_recorded(client, assistant_headers, manager_headers):
    analysis = client.post("/api/v1/analysis/stock-balance", json={"material": "FG-PERFUME-100"}, headers=assistant_headers).json()
    rec = client.post("/api/v1/recommendations", json={"analysis_id": analysis["analysis_id"], "explanation": "rebalance"}, headers=assistant_headers).json()
    decided = client.post(f"/api/v1/recommendations/{rec['id']}/decision", json={"decision": "accepted", "modified": True, "reason_code": "timing", "comment": "ship Monday"},
                          headers=manager_headers)
    assert decided.status_code == 200
    client.post(f"/api/v1/recommendations/{rec['id']}/execute", json={}, headers=manager_headers).raise_for_status()
    learning = client.get("/api/v1/learning", headers=assistant_headers).json()
    outcome = next(o for o in learning["outcomes"] if o["recommendation_id"] == rec["id"])
    assert outcome["status"] == "awaiting_observation" and "DC21" in outcome["expected"]["summary"]
    assert learning["summary"]["verified_pct"] == 0.0  # accepted + executed, but nothing observed yet
    assert learning["summary"]["decided"] >= 1 and learning["summary"]["override_pct"] > 0  # "approve with changes" is an override
    body = {"achieved": True, "realized_impact_eur": 4200, "source_document": "4500900001", "note": "DC21 did not stock out"}
    assert client.post(f"/api/v1/recommendations/{rec['id']}/outcome", json=body, headers=assistant_headers).status_code == 403  # managers only
    assert client.post(f"/api/v1/recommendations/{rec['id']}/outcome", json={**body, "source_document": ""}, headers=manager_headers).status_code == 422
    recorded = client.post(f"/api/v1/recommendations/{rec['id']}/outcome", json=body, headers=manager_headers).json()
    assert recorded["status"] == "verified" and recorded["achieved"] is True
    assert client.post(f"/api/v1/recommendations/{rec['id']}/outcome", json=body, headers=manager_headers).status_code == 409  # once
    after = client.get("/api/v1/learning", headers=assistant_headers).json()["summary"]
    assert after["verified"] >= 1 and after["realized_impact_eur"] >= 4200
    moat = client.get("/api/v1/moat", headers=assistant_headers).json()
    assert moat["realised_by_line"]["Better warehouse stock balancing"] >= 4200
    assert moat["decisions"]["reason_codes"].get("timing", 0) >= 1


def test_moat_view_flywheel_metrics_and_consent_gate(client, assistant_headers, manager_headers):
    m = client.get("/api/v1/moat", headers=assistant_headers).json()
    assert [x["id"] for x in m["moats"]] == ["erp_history", "supplier_reality", "human_expertise", "verified_outcomes", "operating_knowledge", "industry_learning"]
    assert "AirlessPack Asia: SAP promises 42 d, actually 55 d" in m["moats"][1]["learned"]
    assert [s["stage"] for s in m["flywheel"]][0] == "Private customer data" and len(m["flywheel"]) == 5
    assert [x["name"] for x in m["metrics"]] == ["Verified decision outcomes", "Model accuracy uplift", "Business value realised",
                                                  "Customer personalisation advantage", "Industry learning advantage"]
    assert m["consent"]["industry_learning"] is False  # the primary customer starts private
    assert m["models"]["participants"]["this_customer_contributes"] is False
    assert client.post("/api/v1/moat/consent", json={"industry_learning": True}, headers=assistant_headers).status_code == 403
    on = client.post("/api/v1/moat/consent", json={"industry_learning": True}, headers=manager_headers).json()
    assert on["industry_learning"] is True and on["source"].startswith("recorded by")
    after = client.get("/api/v1/moat", headers=assistant_headers).json()
    assert after["models"]["participants"]["this_customer_contributes"] is True
    assert after["models"]["cold_start_wape"] is not None  # a new customer with only a demand-plan level
    lumiere = client.get("/api/v1/moat", headers={**assistant_headers, "X-Tenant": "cosmetics/lumiere"}).json()
    assert "cosmetics/aurelia" in lumiere["models"]["participants"]["same_industry_consenting"]  # consent is what admits data
    client.post("/api/v1/moat/consent", json={"industry_learning": False}, headers=manager_headers).raise_for_status()


def test_role_agent_gets_scoped_tools_and_industry_rules():
    system, tools = _role_setup("procurement")
    names = {t.name for t in tools}
    assert "Procurement Agent" in system and "Cosmetics rules" in system
    assert names == set(ROLES["procurement"]["tools"]) and "warehouse_stock_balance" not in names
    general, all_tools = _role_setup(None)
    assert len(all_tools) > len(tools) and "Procurement Agent" not in general


def test_chat_accepts_only_known_roles(client, assistant_headers):
    assert client.post("/api/v1/chat", json={"message": "hi", "role": "astronaut"}, headers=assistant_headers).status_code == 422
