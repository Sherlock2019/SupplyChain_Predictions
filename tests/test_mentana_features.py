"""Insights, watches, sales orders, stocktake, product 360, role dashboards and 1-click sandbox execution."""
from __future__ import annotations

import pytest

from backend.app.config import ROOT
from backend.app.dashboards import PERSONAS
from backend.app.engine import SupplyChainEngine
from backend.app.insights import InsightEngine
from backend.app.sap import SapRepository


@pytest.fixture(scope="module")
def engine() -> SupplyChainEngine:
    return SupplyChainEngine(SapRepository(ROOT / "data" / "sap_mock.json"))


def test_insights_are_plain_english_deterministic_and_sorted(engine):
    first, second = InsightEngine(engine).insights(), InsightEngine(engine).insights()
    assert first == second  # deterministic
    assert first[0]["severity"] == "critical"
    order = [i["severity"] for i in first]
    assert order == sorted(order, key=["critical", "warning", "info", "good"].index)
    dubai = next(i for i in first if "Dubai" in i["title"] and i["category"] == "Inventory" and i["severity"] == "critical")
    assert "3.5 days" in dubai["title"] and dubai["evidence"] and dubai["action"]["kind"] == "stock_balance"


def test_sales_orders_find_shortfall_and_cheapest_on_time_transfer(engine):
    result = engine.sales_order_fulfilment()
    changi = next(o for o in result["orders"] if o["order"] == "SO-7710052")
    assert changi["status"] == "at_risk" and changi["shortfall"] == 380
    assert changi["resolution"]["action"] == "stock_transfer" and changi["resolution"]["from"] == "DC21"
    dubai = next(o for o in result["orders"] if o["order"] == "SO-7710044")
    assert dubai["status"] == "depends_on_inbound"  # needs the delayed SH-880101


def test_stocktake_explains_differences_with_evidence(engine):
    counts = {c["count_id"]: c for c in engine.stocktake_reconciliation()["counts"]}
    assert counts["PI-2026-1019-01"]["status"] == "explained" and counts["PI-2026-1019-01"]["evidence"][0]["document"] == "4900007781"
    assert counts["PI-2026-1019-02"]["status"] == "within_tolerance"
    assert counts["PI-2026-1019-04"]["evidence"][0]["type"] == "scrap_not_posted"
    assert counts["PI-2026-1019-05"]["status"] == "investigate" and counts["PI-2026-1019-05"]["recommendation"]["action"] == "recount"
    assert counts["PI-2026-1019-06"]["status"] == "matched"


def test_product_360_end_of_stock_resupply_suppliers_and_donor(engine):
    p = engine.product_360("FG-SERUM-50")
    dc22 = next(d for d in p["warehouses"] if d["warehouse"] == "DC22")
    assert dc22["stockout_date"] == "2026-10-25" and len(dc22["projection"]) == 60
    assert dc22["best_donor"]["from"] == "DC21" and dc22["best_donor"]["in_time"] is True
    active = next(c for c in p["resupply"]["components"] if c["component"] == "RM-ACTIVE")
    assert active["first_shortage_date"] == "2026-10-22" and active["status"] == "late"
    assert active["best_suppliers"][0]["supplier"] == "BioActive Labs" and "4500001002" in active["expedite_candidates"]
    assert {pr["material"] for pr in engine.products()} == {"FG-PERFUME-100", "FG-SERUM-50", "FG-CREAM-50"}
    with pytest.raises(ValueError):
        engine.product_360("RM-ACTIVE")


def test_forecast_vs_actuals_backtest(engine):
    fva = engine.forecast_vs_actuals("FG-PERFUME-100", "DC21")
    assert len(fva["actual"]) == 45 and len(fva["backtest"]) == 14 and len(fva["forecast"]) == 14
    assert 0 <= fva["holdout_mape_pct"] < 20


def test_watch_evaluation(engine):
    insights = InsightEngine(engine)
    assert insights.evaluate("days_of_cover", {"material": "FG-PERFUME-100", "warehouse": "DC21"}, 5)["triggered"] is True
    assert insights.evaluate("sales_orders_at_risk", {}, 1)["value"] == 1
    with pytest.raises(ValueError):
        insights.evaluate("nope", {}, 1)


def test_api_dashboards_products_insights_watches(client, assistant_headers):
    for persona in PERSONAS:
        board = client.get(f"/api/v1/dashboards/{persona}", headers=assistant_headers).json()
        assert board["kpis"] and board["charts"], persona
    procurement = client.get("/api/v1/dashboards/procurement", headers=assistant_headers).json()
    otif = next(c for c in procurement["charts"] if c["id"] == "otif")
    values = [r["value"] for r in otif["rows"]]
    assert values == sorted(values, reverse=True) and len(otif["rows"]) <= 10
    inventory = client.get("/api/v1/dashboards/inventory", headers=assistant_headers).json()
    assert len(next(c for c in inventory["charts"] if c["id"] == "understock")["rows"]) == 10
    assert client.get("/api/v1/dashboards/nobody", headers=assistant_headers).status_code == 422
    assert client.get("/api/v1/insights", headers=assistant_headers).json()["counts"]["critical"] >= 1
    assert client.get("/api/v1/products/FG-PERFUME-100", headers=assistant_headers).json()["health"] == "critical"
    watch = client.post("/api/v1/watches", json={"name": "Dubai perfume", "kind": "days_of_cover", "params": {"material": "FG-PERFUME-100", "warehouse": "DC21"}, "threshold": 5},
                        headers=assistant_headers)
    assert watch.status_code == 201
    assert client.post("/api/v1/watches", json={"name": "bad", "kind": "days_of_cover", "params": {}, "threshold": 5}, headers=assistant_headers).status_code == 422
    evaluated = client.post("/api/v1/watches/evaluate", headers=assistant_headers).json()
    assert evaluated["triggered"] == 1 and evaluated["watches"][0]["value"] == 3.5
    assert client.delete(f"/api/v1/watches/{watch.json()['id']}", headers=assistant_headers).json()["deleted"]


def test_dashboards_focus_on_one_product(client, assistant_headers):
    for persona in PERSONAS:
        board = client.get(f"/api/v1/dashboards/{persona}?material=FG-SERUM-50", headers=assistant_headers)
        assert board.status_code == 200, (persona, board.text)
        assert board.json()["product"]["material"] == "FG-SERUM-50"
    sales = client.get("/api/v1/dashboards/sales?material=FG-SERUM-50", headers=assistant_headers).json()
    orders = next(t for t in sales["tables"] if t["title"] == "Orders and resolutions")["rows"]
    assert {row[0] for row in orders} == {"SO-7710052", "SO-7710063"}  # serum orders only
    procurement = client.get("/api/v1/dashboards/procurement?material=FG-SERUM-50", headers=assistant_headers).json()
    suppliers = {r["label"] for r in next(c for c in procurement["charts"] if c["id"] == "otif")["rows"]}
    assert suppliers == {"BioActive Labs", "BaseChem Iberia", "AirlessPack Asia", "Carton Luxe"}  # serum BOM suppliers
    inventory = client.get("/api/v1/dashboards/inventory?material=FG-SERUM-50", headers=assistant_headers).json()
    assert inventory["forecast"] == {"material": "FG-SERUM-50", "warehouse": "DC22"}
    assert client.get("/api/v1/dashboards/inventory?material=RM-ACTIVE", headers=assistant_headers).status_code == 422


def test_one_click_execution_only_after_acceptance_and_only_for_manager(client, assistant_headers, manager_headers):
    analysis = client.post("/api/v1/analysis/sales-orders", json={}, headers=assistant_headers).json()
    rec = client.post("/api/v1/recommendations", json={"analysis_id": analysis["analysis_id"], "explanation": "fix Changi"}, headers=assistant_headers).json()
    assert client.post(f"/api/v1/recommendations/{rec['id']}/execute", headers=manager_headers).status_code == 409  # not accepted yet
    client.post(f"/api/v1/recommendations/{rec['id']}/decision", json={"decision": "accepted"}, headers=manager_headers)
    assert client.post(f"/api/v1/recommendations/{rec['id']}/execute", headers=assistant_headers).status_code == 403  # planners/agents cannot
    done = client.post(f"/api/v1/recommendations/{rec['id']}/execute", headers=manager_headers).json()
    assert done["status"] == "executed" and done["documents"][0]["doc_type"] == "STO" and done["sap_written"] == "sandbox"
    assert client.post(f"/api/v1/recommendations/{rec['id']}/execute", headers=manager_headers).status_code == 409  # once only
    odata = client.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument", headers=assistant_headers).json()
    assert odata["@odata.count"] == 1 and odata["__sandbox"] is True
    # agents and tools still cannot write to the SAP OData service
    assert client.post("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument", headers=manager_headers).status_code == 405
