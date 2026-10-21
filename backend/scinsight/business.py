"""Deterministic supply-chain business functions — the only place quantities, dates and costs are calculated.

Units and rules (documented in docs/SAP_SYNTHETIC_DATA.md):
  * Quantities are in the item's SAP unit of measure (EA = each, KG = kilogram). EA results are rounded UP to whole units;
    KG results are rounded to 3 decimals. Money is EUR rounded to 2 decimals. Days are whole calendar days.
  * Usable stock = batches with status "released", not expired on the as-of date, not reserved for an order.
    Excluded: blocked, quality_inspection (not released), reserved, expired. Near expiry (<= NEAR_EXPIRY_DAYS left) stays
    usable locally but is flagged for FEFO review and is never transferred if the remaining shelf life on arrival is below
    MIN_SHELF_LIFE_AT_ARRIVAL_DAYS.
  * Inbound supply counts only if the purchase order is confirmed (or already received) and promised on/before the need date.
  * Duplicate records (same batch id / PO id / sales day) are counted once.
These functions never call an LLM; missing data produces explicit "missing" results, never invented values.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

NEAR_EXPIRY_DAYS = 30
MIN_SHELF_LIFE_AT_ARRIVAL_DAYS = 60
DEMAND_WINDOW_DAYS = 28
UNUSABLE_STATUSES = {"blocked": "QA blocked", "quality_inspection": "not released by quality (inspection)", "reserved": "reserved for a customer order"}


class BusinessRuleError(ValueError):
    """A request that cannot be answered safely (invalid BOM, unit mismatch, missing master data)."""


def _d(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def round_qty(value: float, uom: str) -> float:
    return float(math.ceil(value - 1e-9)) if uom == "EA" else round(value, 3)


def _dedupe(rows: list[dict], key: str) -> list[dict]:
    seen: dict = {}
    for row in rows:
        seen[row[key]] = row  # later record wins (latest extract)
    return list(seen.values())


# ------------------------------------------------------------------------------------------------ stock
def calculate_usable_stock(batches: list[dict], as_of: date, transfer_arrival: date | None = None) -> dict:
    """Usable quantity from SAP batches with an itemised exclusion list. With transfer_arrival, also enforce the minimum
    remaining shelf life on arrival (stock about to expire stays where it is: FEFO)."""
    usable, excluded, near_expiry, used = 0.0, [], [], []
    for b in _dedupe(batches, "batch_id"):
        qty, expiry = float(b["quantity"]), _d(b.get("expiry_date"))
        if b["status"] in UNUSABLE_STATUSES:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": UNUSABLE_STATUSES[b["status"]]})
            continue
        if b["status"] != "released":
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"unknown status {b['status']}"})
            continue
        if b.get("reserved_for"):
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"reserved for {b['reserved_for']}"})
            continue
        if expiry is not None and expiry <= as_of:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"expired {expiry.isoformat()}"})
            continue
        days_left = (expiry - as_of).days if expiry else None
        if transfer_arrival and expiry is not None and (expiry - transfer_arrival).days < MIN_SHELF_LIFE_AT_ARRIVAL_DAYS:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty,
                             "reason": f"only {(expiry - transfer_arrival).days} days shelf life on arrival (< {MIN_SHELF_LIFE_AT_ARRIVAL_DAYS}); sell locally (FEFO)"})
            continue
        if days_left is not None and days_left <= NEAR_EXPIRY_DAYS:
            near_expiry.append({"batch_id": b["batch_id"], "quantity": qty, "expiry_date": expiry.isoformat(), "days_left": days_left})
        usable += qty
        used.append({"batch_id": b["batch_id"], "quantity": qty, "expiry_date": expiry.isoformat() if expiry else None})
    return {"usable": usable, "used_batches": sorted(used, key=lambda x: x["expiry_date"] or "9999"), "excluded": excluded,
            "near_expiry": near_expiry, "rules": "released, not expired, not reserved; blocked / inspection / reserved / expired excluded"}


def average_daily_demand(sales: list[dict], as_of: date, window_days: int = DEMAND_WINDOW_DAYS) -> float:
    """Mean units/day over the last `window_days` days (missing days count as zero demand; duplicate days counted once)."""
    start = as_of - timedelta(days=window_days)
    by_day = {r["day"]: float(r["quantity"]) for r in sales if start <= _d(r["day"]) < as_of}
    return round(sum(by_day.values()) / window_days, 2)


def calculate_days_of_cover(usable: float, daily_demand: float) -> float | None:
    """Days the usable stock lasts at the given demand. None when there is no demand (cover is unbounded)."""
    if daily_demand <= 0:
        return None
    return round(usable / daily_demand, 1)


def calculate_replenishment_quantity(daily_demand: float, usable: float, target_cover_days: int, lead_days: int, uom: str = "EA") -> float:
    """Quantity needed so that stock covers lead time + target cover. Zero demand -> 0."""
    if daily_demand <= 0:
        return 0.0
    return max(0.0, round_qty(daily_demand * (target_cover_days + lead_days) - usable, uom))


def detect_expiry_risk(batches: list[dict], as_of: date, horizon_days: int = 90) -> list[dict]:
    """Released batches expired or expiring within the horizon, most urgent first."""
    out = []
    for b in _dedupe(batches, "batch_id"):
        expiry = _d(b.get("expiry_date"))
        if expiry is None or (expiry - as_of).days > horizon_days:
            continue
        days = (expiry - as_of).days
        out.append({"batch_id": b["batch_id"], "item_id": b["item_id"], "location": b["location"], "quantity": float(b["quantity"]),
                    "status": b["status"], "expiry_date": expiry.isoformat(), "days_left": days,
                    "risk": "expired" if days <= 0 else "near_expiry" if days <= NEAR_EXPIRY_DAYS else "watch"})
    return sorted(out, key=lambda x: x["days_left"])


# ------------------------------------------------------------------------------------------------ BOM / readiness
def calculate_bom_requirements(bom_rows: list[dict], quantity: float, need_date: date, material_uoms: dict[str, str]) -> dict:
    """Material requirements for `quantity` finished units from the approved BOM version valid on `need_date`."""
    if quantity <= 0:
        raise BusinessRuleError("production quantity must be positive")
    valid = [r for r in bom_rows if r["status"] == "approved" and _d(r["valid_from"]) <= need_date and (r.get("valid_to") is None or need_date <= _d(r["valid_to"]))]
    versions = sorted({r["bom_version"] for r in valid})
    if not versions:
        drafts = sorted({r["bom_version"] for r in bom_rows if r["status"] != "approved"})
        raise BusinessRuleError(f"no approved BOM valid on {need_date.isoformat()}" + (f" (draft versions {', '.join(drafts)} cannot be used)" if drafts else ""))
    version = versions[-1]
    lines = []
    for r in (r for r in valid if r["bom_version"] == version):
        stock_uom = material_uoms.get(r["material_id"])
        if stock_uom is None:
            raise BusinessRuleError(f"material {r['material_id']} in BOM {version} has no material master")
        if stock_uom != r["uom"]:
            raise BusinessRuleError(f"unit of measure mismatch for {r['material_id']}: BOM uses {r['uom']}, stock is kept in {stock_uom}")
        required = round_qty(quantity * float(r["qty_per_unit"]) * (1 + float(r["scrap_pct"]) / 100), r["uom"])
        lines.append({"material_id": r["material_id"], "qty_per_unit": float(r["qty_per_unit"]), "scrap_pct": float(r["scrap_pct"]),
                      "required_quantity": required, "uom": r["uom"]})
    return {"bom_version": version, "quantity": quantity, "need_date": need_date.isoformat(), "lines": lines}


def calculate_material_shortage(required: float, usable: float, purchase_orders: list[dict], need_date: date, uom: str) -> dict:
    """Missing quantity on the need date. Inbound counts only if confirmed (or received) and promised on/before need_date."""
    timely, late, unconfirmed = [], [], []
    for po in _dedupe(purchase_orders, "po_id"):
        if po["status"] in ("cancelled", "received"):
            continue
        open_qty = float(po["quantity"]) - float(po.get("received_quantity") or 0)
        entry = {"po_id": po["po_id"], "supplier_id": po["supplier_id"], "quantity": open_qty, "promised_date": po["promised_date"], "status": po["status"]}
        if po["status"] != "confirmed":
            unconfirmed.append(entry)
        elif _d(po["promised_date"]) <= need_date:
            timely.append(entry)
        else:
            late.append(entry)
    inbound = sum(p["quantity"] for p in timely)
    missing = max(0.0, round_qty(required - usable - inbound, uom))
    return {"required": required, "usable": usable, "confirmed_timely_inbound": inbound, "missing": missing, "need_date": need_date.isoformat(),
            "timely_purchase_orders": timely, "late_purchase_orders": late, "unconfirmed_purchase_orders": unconfirmed, "uom": uom,
            "status": "short" if missing > 0 else "covered"}


# ------------------------------------------------------------------------------------------------ transfers / supply options
@dataclass
class Site:
    code: str
    usable_transferable: float  # usable and eligible for transfer (shelf life on arrival respected)
    usable_total: float
    daily_demand: float
    target_cover_days: int


def generate_transfer_candidates(receiver: str, sites: dict[str, Site]) -> list[dict]:
    """Donor warehouses with surplus = transferable stock above their own target cover (FEFO: near-expiry stock is used locally first)."""
    out = []
    for code, s in sites.items():
        if code == receiver:
            continue
        keep = s.daily_demand * s.target_cover_days
        local_only = s.usable_total - s.usable_transferable  # stock that cannot travel covers local demand first
        surplus = max(0.0, s.usable_transferable - max(0.0, keep - local_only))
        surplus = float(math.floor(surplus + 1e-9))  # whole units, rounded DOWN: never promise stock that is not there
        if surplus > 0:
            out.append({"donor": code, "surplus": surplus, "donor_keeps_days": s.target_cover_days})
    return sorted(out, key=lambda c: -c["surplus"])


def evaluate_transfer_feasibility(candidate: dict, need: float, lane: dict | None, as_of: date, stockout_date: date | None) -> dict:
    """Is the transfer possible and in time? Reasons are listed; costs come only from the lane master data."""
    reasons = []
    if lane is None:
        return {**candidate, "feasible": False, "reasons": ["no transport lane in SAP master data"], "quantity": 0}
    qty = min(need, candidate["surplus"], float(lane["capacity_units"]))
    if qty <= 0:
        reasons.append("no transferable surplus")
    if candidate["surplus"] < need:
        reasons.append(f"donor surplus {candidate['surplus']:.0f} covers only part of the need {need:.0f}")
    if float(lane["capacity_units"]) < need:
        reasons.append(f"lane capacity {lane['capacity_units']} per shipment")
    arrival = as_of + timedelta(days=int(lane["lead_days"]))
    in_time = stockout_date is None or arrival <= stockout_date
    if not in_time:
        reasons.append(f"arrives {arrival.isoformat()}, after the stock-out on {stockout_date.isoformat()}")
    cost = round(qty * float(lane["cost_per_unit_eur"]) + float(lane["fixed_cost_eur"]), 2) if qty > 0 else 0.0
    return {**candidate, "lane_id": lane["lane_id"], "mode": lane["mode"], "lead_days": int(lane["lead_days"]), "quantity": qty,
            "arrival_date": arrival.isoformat(), "in_time": in_time, "cost_eur": cost, "cost_per_unit_eur": float(lane["cost_per_unit_eur"]),
            "covers_need": qty >= need, "feasible": qty > 0 and in_time, "reasons": reasons}


def compare_supply_options(options: list[dict]) -> list[dict]:
    """Rank options: feasible and in time first, then full coverage, then lowest cost, then fastest. Adds rank + recommended.
    An option is recommended only if it is feasible AND arrives in time; otherwise nothing is recommended (no false comfort)."""
    ranked = sorted(options, key=lambda o: (not o.get("feasible"), not o.get("in_time", True), not o.get("covers_need"),
                                            o.get("cost_eur") if o.get("cost_eur") is not None else 1e12,
                                            o.get("lead_days") if o.get("lead_days") is not None else 999))
    for i, o in enumerate(ranked, 1):
        o["rank"] = i
        o["recommended"] = i == 1 and bool(o.get("feasible")) and bool(o.get("in_time", True))
    return ranked


# ------------------------------------------------------------------------------------------------ lead time / learning
def estimate_supplier_lead_time(receipts: list[dict], contract_lead_days: int | None) -> dict:
    """Empirical lead time from received purchase orders (order date -> goods receipt). Duplicate receipts counted once."""
    rows = [r for r in _dedupe(receipts, "po_id") if r.get("received_date")]
    leads = sorted((_d(r["received_date"]) - _d(r["order_date"])).days for r in rows)
    if not leads:
        return {"receipts": 0, "estimate_days": None, "p90_days": None, "contract_days": contract_lead_days,
                "status": "insufficient_history", "basis": "no goods receipts in the SAP history"}
    mean = sum(leads) / len(leads)
    p90 = leads[min(len(leads) - 1, math.ceil(0.9 * len(leads)) - 1)]
    on_time = sum((_d(r["received_date"]) <= _d(r["promised_date"])) for r in rows) / len(rows)
    return {"receipts": len(leads), "estimate_days": round(mean, 1), "p90_days": p90, "min_days": leads[0], "max_days": leads[-1],
            "contract_days": contract_lead_days, "on_time_rate": round(on_time, 3), "status": "ok" if len(leads) >= 3 else "low_confidence",
            "basis": f"mean of {len(leads)} goods receipts (order date -> receipt date)"}


def calculate_prediction_error(predicted: float, actual: float) -> dict:
    """Signed error = actual - predicted (positive = later/higher than predicted)."""
    signed = actual - predicted
    return {"predicted": predicted, "actual": actual, "signed_error": signed, "absolute_error": abs(signed),
            "percentage_error": round(100 * signed / predicted, 1) if predicted else None}


def reconcile_actual_outcome(prediction: dict, purchase_order: dict | None, completeness_threshold: float = 0.98) -> dict:
    """Match a lead-time prediction with the SAP goods receipt of its purchase order."""
    if purchase_order is None:
        return {"status": "missing", "reason": "no SAP purchase order record for the prediction"}
    if not purchase_order.get("received_date"):
        return {"status": "pending", "reason": f"{purchase_order['po_id']} has no goods receipt yet"}
    actual = (_d(purchase_order["received_date"]) - _d(purchase_order["order_date"])).days
    ratio = float(purchase_order.get("received_quantity") or 0) / float(purchase_order["quantity"])
    flags = [] if ratio >= completeness_threshold else [f"partial delivery {ratio:.0%} of ordered quantity"]
    return {"status": "verified" if not flags else "incomplete", "metric": "lead_time_days", "actual": actual,
            "error": calculate_prediction_error(float(prediction["predicted"]), float(actual)), "received_ratio": round(ratio, 3),
            "quality_flags": flags, "source_document": purchase_order["po_id"], "received_date": purchase_order["received_date"]}
