"""Unit tests of the deterministic business functions (units, availability rules, edge cases)."""
from __future__ import annotations

from datetime import date

import pytest

from backend.scinsight import business as bz

AS_OF = date(2026, 10, 21)


def batch(bid, qty, status="released", expiry=None, reserved=None, loc="WH-C", item="SUN-SPF50-100"):
    return {"batch_id": bid, "quantity": qty, "status": status, "expiry_date": expiry, "reserved_for": reserved, "location": loc, "item_id": item}


def test_usable_stock_excludes_blocked_inspection_reserved_expired_and_flags_near_expiry():
    rows = [batch("A", 3000, expiry="2027-06-30"), batch("B", 1500, expiry="2026-11-10"), batch("C", 800, expiry="2026-10-15"),
            batch("D", 700, "blocked"), batch("E", 1000, "reserved", reserved="SO-1"), batch("F", 500, "quality_inspection")]
    u = bz.calculate_usable_stock(rows, AS_OF)
    assert u["usable"] == 4500
    assert {e["batch_id"] for e in u["excluded"]} == {"C", "D", "E", "F"}
    assert [n["batch_id"] for n in u["near_expiry"]] == ["B"]
    moved = bz.calculate_usable_stock(rows, AS_OF, transfer_arrival=date(2026, 10, 23))
    assert moved["usable"] == 3000  # near-expiry batch stays local (FEFO, < 60 days on arrival)


def test_duplicate_batches_are_counted_once():
    rows = [batch("A", 100, expiry="2027-01-01"), batch("A", 100, expiry="2027-01-01")]
    assert bz.calculate_usable_stock(rows, AS_OF)["usable"] == 100


def test_days_of_cover_and_replenishment_handle_zero_demand():
    assert bz.calculate_days_of_cover(1200, 200) == 6.0
    assert bz.calculate_days_of_cover(1200, 0) is None
    assert bz.calculate_replenishment_quantity(0, 100, 14, 2) == 0
    assert bz.calculate_replenishment_quantity(200, 1200, 14, 2) == 2000


def test_bom_requirements_units_rounding_and_invalid_versions():
    bom = [{"bom_version": "v2", "material_id": "PUMP", "qty_per_unit": 1, "uom": "EA", "scrap_pct": 0.5, "valid_from": "2026-01-01", "valid_to": None, "status": "approved"},
           {"bom_version": "v2", "material_id": "BASE", "qty_per_unit": 0.031, "uom": "KG", "scrap_pct": 2.0, "valid_from": "2026-01-01", "valid_to": None, "status": "approved"},
           {"bom_version": "v3", "material_id": "PUMP", "qty_per_unit": 1, "uom": "EA", "scrap_pct": 0, "valid_from": "2026-01-01", "valid_to": None, "status": "draft"}]
    r = bz.calculate_bom_requirements(bom, 50000, AS_OF, {"PUMP": "EA", "BASE": "KG"})
    assert r["bom_version"] == "v2"  # draft v3 is never used
    lines = {line["material_id"]: line["required_quantity"] for line in r["lines"]}
    assert lines == {"PUMP": 50250.0, "BASE": 1581.0}  # EA rounded up, KG to 3 decimals
    with pytest.raises(bz.BusinessRuleError, match="unit of measure mismatch"):
        bz.calculate_bom_requirements(bom, 10, AS_OF, {"PUMP": "EA", "BASE": "L"})
    with pytest.raises(bz.BusinessRuleError, match="no approved BOM"):
        bz.calculate_bom_requirements([bom[2]], 10, AS_OF, {"PUMP": "EA"})
    with pytest.raises(bz.BusinessRuleError, match="positive"):
        bz.calculate_bom_requirements(bom, 0, AS_OF, {"PUMP": "EA", "BASE": "KG"})


def test_shortage_counts_only_confirmed_timely_inbound_and_dedupes_pos():
    pos = [{"po_id": "1", "supplier_id": "S", "quantity": 25000, "promised_date": "2026-11-05", "status": "confirmed", "received_quantity": None},
           {"po_id": "2", "supplier_id": "S", "quantity": 8000, "promised_date": "2026-10-24", "status": "open", "received_quantity": None},
           {"po_id": "3", "supplier_id": "S", "quantity": 5000, "promised_date": "2026-10-25", "status": "confirmed", "received_quantity": None},
           {"po_id": "3", "supplier_id": "S", "quantity": 5000, "promised_date": "2026-10-25", "status": "confirmed", "received_quantity": None}]
    s = bz.calculate_material_shortage(50000, 30000, pos, date(2026, 10, 27), "EA")
    assert s["confirmed_timely_inbound"] == 5000 and s["missing"] == 15000
    assert [p["po_id"] for p in s["late_purchase_orders"]] == ["1"] and [p["po_id"] for p in s["unconfirmed_purchase_orders"]] == ["2"]


def test_transfer_candidates_feasibility_and_ranking():
    sites = {"WH-C": bz.Site("WH-C", 3000, 4500, 110, 14), "WH-B": bz.Site("WH-B", 0, 1200, 200, 14)}
    cands = bz.generate_transfer_candidates("WH-B", sites)
    assert cands == [{"donor": "WH-C", "surplus": 2960.0, "donor_keeps_days": 14}]
    lane = {"lane_id": "L1", "mode": "road", "lead_days": 2, "cost_per_unit_eur": 0.35, "fixed_cost_eur": 120, "capacity_units": 5000}
    ev = bz.evaluate_transfer_feasibility(cands[0], 2000, lane, AS_OF, date(2026, 10, 27))
    assert ev["feasible"] and ev["in_time"] and ev["quantity"] == 2000 and ev["cost_eur"] == 820.0
    late = bz.evaluate_transfer_feasibility(cands[0], 2000, {**lane, "lead_days": 9}, AS_OF, date(2026, 10, 27))
    assert not late["feasible"] and "after the stock-out" in late["reasons"][0]
    no_lane = bz.evaluate_transfer_feasibility(cands[0], 2000, None, AS_OF, None)
    assert not no_lane["feasible"] and "no transport lane" in no_lane["reasons"][0]
    ranked = bz.compare_supply_options([late, ev])
    assert ranked[0] is ev and ev["recommended"] and not late["recommended"]


def test_nothing_is_recommended_when_no_option_is_in_time():
    ranked = bz.compare_supply_options([{"feasible": True, "in_time": False, "covers_need": True, "cost_eur": 10, "lead_days": 9}])
    assert ranked[0]["recommended"] is False


def test_lead_time_estimate_and_prediction_error_and_reconciliation():
    rec = [{"po_id": "A", "order_date": "2026-09-01", "promised_date": "2026-09-06", "received_date": "2026-09-10"},
           {"po_id": "A", "order_date": "2026-09-01", "promised_date": "2026-09-06", "received_date": "2026-09-10"},  # duplicate receipt
           {"po_id": "B", "order_date": "2026-09-10", "promised_date": "2026-09-15", "received_date": "2026-09-18"}]
    est = bz.estimate_supplier_lead_time(rec, 5)
    assert est["receipts"] == 2 and est["estimate_days"] == 8.5 and est["on_time_rate"] == 0.0 and est["status"] == "low_confidence"
    assert bz.estimate_supplier_lead_time([], 5)["status"] == "insufficient_history"
    assert bz.calculate_prediction_error(5, 9) == {"predicted": 5, "actual": 9, "signed_error": 4, "absolute_error": 4, "percentage_error": 80.0}
    po = {"po_id": "P", "order_date": "2026-09-30", "received_date": "2026-10-09", "quantity": 25000, "received_quantity": 25000}
    out = bz.reconcile_actual_outcome({"predicted": 5}, po)
    assert out["status"] == "verified" and out["actual"] == 9 and out["error"]["signed_error"] == 4
    assert bz.reconcile_actual_outcome({"predicted": 5}, {**po, "received_quantity": 20000})["status"] == "incomplete"
    assert bz.reconcile_actual_outcome({"predicted": 5}, {**po, "received_date": None})["status"] == "pending"
    assert bz.reconcile_actual_outcome({"predicted": 5}, None)["status"] == "missing"


def test_expiry_risk_is_ordered_most_urgent_first():
    risks = bz.detect_expiry_risk([batch("A", 1, expiry="2026-11-10"), batch("B", 1, expiry="2026-10-15"), batch("C", 1, expiry="2028-01-01")], AS_OF)
    assert [r["batch_id"] for r in risks] == ["B", "A"] and risks[0]["risk"] == "expired" and risks[1]["risk"] == "near_expiry"
