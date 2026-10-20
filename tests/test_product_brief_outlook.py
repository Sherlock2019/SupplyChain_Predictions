"""Product brief (issues -> proposed fixes) and the sales-rate / out-of-stock calendar outlook."""
from __future__ import annotations

import pytest

from backend.app.config import ROOT
from backend.app.engine import SupplyChainEngine
from backend.app.sap import SapRepository


@pytest.fixture(scope="module")
def engine():
    return SupplyChainEngine(SapRepository(ROOT / "data" / "sap_mock.json"))


def test_brief_pairs_every_issue_with_a_fix_and_action(engine):
    b = engine.product_brief("FG-PERFUME-100")
    assert b["status"] == "critical"
    first = b["issues"][0]
    # Dubai runs out on 28 Oct; DC01 can send 1,170 units that arrive before the stock-out.
    assert first["severity"] == "critical" and "Dubai" in first["issue"] and "DC01" in first["fix"] and "before the stock-out" in first["fix"]
    assert first["action"]["kind"] == "stock_balance" and first["action"]["params"]["material"] == "FG-PERFUME-100"
    assert all(i["fix"] and i["action"]["label"] for i in b["issues"])
    severities = [i["severity"] for i in b["issues"]]
    assert severities == sorted(severities, key=["critical", "warning", "info"].index)
    assert b["time_to_out_of_stock"] == {**b["time_to_out_of_stock"], "days": 8, "date": "2026-10-28", "warehouse": "DC21"}
    assert b["reserve"]["safety_stock_total"] == 3 * b["reserve"]["safety_stock_per_dc"]
    assert b["supply"]["on_hand"] == 7130
    assert {s["material"] for s in b["top_suppliers"]} == {"RM-ALCOHOL", "PK-CARTON", "RM-FRAGRANCE", "PK-BOTTLE-100"}
    assert b["top_warehouses"][0]["rank"] == 1
    assert not any(" by now" in i["fix"] for i in b["issues"])  # past order-by dates read "now"


def test_outlook_sales_rates_and_calendar(engine):
    o = engine.sales_outlook()
    assert len(o["sales_rates"]) == 9 and o["sales_rates"][0]["days_to_stockout"] == 5  # Singapore serum first
    r = o["sales_rates"][0]
    assert len(r["sparkline"]) == 28 and r["trend"] in {"up", "down", "flat"} and r["last_7d_per_day"] > 0
    kinds = {e["kind"] for e in o["calendar"]}
    assert kinds == {"stockout", "below_safety", "arrival", "production"}
    assert {(e["material"], e["warehouse"], e["date"]) for e in o["calendar"] if e["kind"] == "stockout"} >= {("FG-PERFUME-100", "DC21", "2026-10-28")}
    dates = [e["date"] for e in o["calendar"]]
    assert dates == sorted(dates) and all(0 <= e["days_from_today"] <= o["horizon_days"] for e in o["calendar"])
    dcs = set(engine._warehouses()) | {"all DCs"}
    assert all(e["warehouse"] in dcs for e in o["calendar"])  # customer deliveries are not resupply


def test_brief_and_outlook_endpoints_follow_tenant(client, assistant_headers):
    b = client.get("/api/v1/products/fg-serum-50/brief", headers=assistant_headers).json()
    assert b["material"] == "FG-SERUM-50" and b["issues"]
    one = client.get("/api/v1/sales/outlook?material=FG-SERUM-50", headers=assistant_headers).json()
    assert {r["material"] for r in one["sales_rates"]} == {"FG-SERUM-50"}
    h = {**assistant_headers, "X-Tenant": "automotive/voltara"}
    fg = client.get("/api/v1/products", headers=h).json()[0]["material"]
    assert client.get(f"/api/v1/products/{fg}/brief", headers=h).json()["issues"] is not None
    assert client.get("/api/v1/sales/outlook", headers=h).json()["calendar"]
    assert client.get("/api/v1/sales/outlook?material=NOPE", headers=assistant_headers).status_code in (400, 404, 422)
