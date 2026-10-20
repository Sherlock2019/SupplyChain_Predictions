"""Industry / customer tenants (X-Tenant header) and the supply-network map."""
from __future__ import annotations

import pytest

from backend.app.config import ROOT
from backend.app.engine import SupplyChainEngine
from backend.app.sap import SapRepository

MEDIVIA = {"X-Tenant": "pharmaceutical/medivia"}


def test_catalogue_lists_industries_and_customers(client):
    cat = client.get("/api/v1/tenants").json()
    industries = {i["id"]: i for i in cat["industries"]}
    assert {"cosmetics", "ecommerce", "pharmaceutical", "automotive", "food"} <= set(industries)
    assert cat["default"] == "cosmetics/aurelia"
    assert {c["id"] for c in industries["cosmetics"]["customers"]} == {"cosmetics/aurelia", "cosmetics/lumiere"}
    assert sum(len(i["customers"]) for i in cat["industries"]) >= 9


@pytest.mark.parametrize("tenant", ["cosmetics/lumiere", "ecommerce/shopnova", "pharmaceutical/medivia", "automotive/voltara", "food/verdant"])
def test_every_view_works_for_each_customer(client, assistant_headers, tenant):
    h = {**assistant_headers, "X-Tenant": tenant}
    snap = client.get("/api/v1/snapshot", headers=h).json()
    assert snap["tenant"]["id"] == tenant and snap["synthetic"] is True
    fg = next(m["code"] for m in snap["materials"] if m["type"] == "FG")
    assert client.get("/api/v1/insights", headers=h).json()["insights"]
    assert client.get("/api/v1/dashboards/executive", headers=h).status_code == 200
    assert client.get(f"/api/v1/dashboards/procurement?material={fg}", headers=h).status_code == 200
    assert client.get(f"/api/v1/products/{fg}", headers=h).json()["material"] == fg
    site = client.get("/api/v1/sites", headers=h).json()[0]["code"]
    assert client.get(f"/api/v1/sites/{site}", headers=h).json()["site"]["contacts"]
    assert client.get("/api/v1/network/map", headers=h).json()["sites"]


def test_customers_are_isolated(client, assistant_headers, manager_headers):
    analysis = client.post("/api/v1/analysis/sales-orders", json={}, headers=assistant_headers).json()
    client.post("/api/v1/recommendations", json={"analysis_id": analysis["analysis_id"], "explanation": "aurelia"}, headers=assistant_headers)
    assert client.get("/api/v1/recommendations", headers=assistant_headers).json()
    assert client.get("/api/v1/recommendations", headers={**assistant_headers, **MEDIVIA}).json() == []
    client.post("/api/v1/watches", json={"name": "w", "kind": "sales_orders_at_risk", "params": {}, "threshold": 1}, headers=assistant_headers)
    assert client.get("/api/v1/watches", headers={**assistant_headers, **MEDIVIA}).json() == []
    # Aurelia codes do not exist for Medivia
    bad = client.post("/api/v1/analysis/stock-balance", json={"material": "FG-PERFUME-100"}, headers={**assistant_headers, **MEDIVIA})
    assert bad.status_code == 422
    assert client.get("/api/v1/kpis", headers={**assistant_headers, "X-Tenant": "nope/none"}).status_code == 422


def test_network_map_tiers_and_sourcing():
    engine = SupplyChainEngine(SapRepository(ROOT / "data" / "sap_mock.json"))
    m = engine.network_map()
    tier = {(s["name"], x["plant"]): x["tier"] for s in m["suppliers"] for x in s["serves"]}
    assert tier[("Carton Luxe", "FR10")] == "local"  # France -> Paris
    assert tier[("PackGlass Europe", "FR10")] == "regional"  # Italy -> France, same zone
    assert tier[("AirlessPack Asia", "FR20")] == "international"  # Korea -> Lyon
    fr10 = next(f for f in m["factory_sourcing"] if f["plant"] == "FR10")
    assert fr10["within_zone_pct"] == 100.0
    bio = next(s for s in m["suppliers"] if s["name"] == "BioActive Labs")
    assert bio["learned_time_to_deliver_days"] > bio["sap_lead_time_days"]  # reality vs SAP promise
    assert {o["origin"] for o in m["origins"]} >= {"Madagascar", "Burkina Faso"}
    assert {f["kind"] for f in m["flows"]} >= {"supply", "tier2", "distribution", "lane", "shipment"}
    assert m["reference"]["figures"][0]["value_pct"] == 80
