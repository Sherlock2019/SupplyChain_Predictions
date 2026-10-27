# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/business.py
# What this module is: the deterministic supply-chain calculations of SCInsight — usable stock, demand, days of
# cover, replenishment quantity, expiry risk, BOM requirements, material shortage, transfer candidates and
# feasibility, supply-option ranking, supplier lead time, prediction error and outcome reconciliation.
# Pure functions: no database, no HTTP, no LLM. Service (service.py) feeds them SAP rows and stores the results.
# Only comment lines were added (AST-verified).
# ======================================================================================================

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

# math.ceil / math.floor for unit rounding.
import math
# @dataclass for the small Site record used by transfer planning.
from dataclasses import dataclass
# date arithmetic: date - date -> timedelta; date + timedelta(days=n) -> date.
from datetime import date, timedelta

# Business constants (one place to change a rule):
NEAR_EXPIRY_DAYS = 30                 # <= 30 days of shelf life left -> flagged "near expiry" (FEFO review)
MIN_SHELF_LIFE_AT_ARRIVAL_DAYS = 60   # a transferred batch must still have >= 60 days when it arrives (POL-WH-020)
DEMAND_WINDOW_DAYS = 28               # average demand = last 28 days
# SAP batch statuses that are never usable, with the human-readable reason shown to planners.
UNUSABLE_STATUSES = {"blocked": "QA blocked", "quality_inspection": "not released by quality (inspection)", "reserved": "reserved for a customer order"}


# ===== CLASS: BusinessRuleError =====
# ID: F0293 · class · used
# ORIGINAL FILE: backend/scinsight/business.py:26-27
# ROLE: Exception for requests that cannot be answered safely (invalid BOM, unit mismatch, missing master data).
#       Service converts it into HTTP 422 with the message, so the agent sees WHY instead of a guessed number.
# FIELDS:
#   (inherits ValueError: message only).
# CALLED BY:
#   <- F0302 calculate_bom_requirements() (calls)
#   <- F0320 Service.bom() (references)
#   <- F0325 Service.material_readiness() (references)
#   <- F0916 test_bom_requirements_units_rounding_and_invalid_versions() (references)
# CALLS:
#   (none found)
class BusinessRuleError(ValueError):
    """A request that cannot be answered safely (invalid BOM, unit mismatch, missing master data)."""


# ===== FUNCTION: _d() =====
# ID: F0294 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:30-33
# ROLE: Tolerant date parser for SAP fields that may be a date, an ISO string ("2026-10-21" or a timestamp) or empty.
# INPUTS:
#   value: str | date | None -> raw field value.
# OUTPUT:
#   date | None -> parsed date, or None when empty.
# CALLED BY:
#   <- F0297 calculate_usable_stock() (calls)
#   <- F0298 average_daily_demand() (calls)
#   <- F0301 detect_expiry_risk() (calls)
#   <- F0302 calculate_bom_requirements() (calls)
#   <- F0303 calculate_material_shortage() (calls)
#   <- F0308 estimate_supplier_lead_time() (calls)
#   <- F0310 reconcile_actual_outcome() (calls)
# CALLS:
#   (none found)
def _d(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    # isinstance check: already a date -> return as is; otherwise keep the first 10 characters "YYYY-MM-DD" and parse.
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


# ===== FUNCTION: round_qty() =====
# ID: F0295 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:36-37
# ROLE: Round a quantity according to its unit: EA (pieces) UP to a whole unit, other units (KG) to 3 decimals.
# INPUTS:
#   value: float -> raw quantity.
#   uom: str     -> SAP unit of measure ("EA", "KG", ...).
# OUTPUT:
#   float -> rounded quantity.
# CALLED BY:
#   <- F0300 calculate_replenishment_quantity() (calls)
#   <- F0302 calculate_bom_requirements() (calls)
#   <- F0303 calculate_material_shortage() (calls)
# CALLS:
#   (none found)
def round_qty(value: float, uom: str) -> float:
    # "value - 1e-9" protects against floating-point noise: 20000.0000000001 must stay 20000, not become 20001.
    return float(math.ceil(value - 1e-9)) if uom == "EA" else round(value, 3)


# ===== FUNCTION: _dedupe() =====
# ID: F0296 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:40-44
# ROLE: Remove duplicate SAP records (same batch id / PO id) — the LATER record wins (latest extract).
# INPUTS:
#   rows: list[dict] -> records possibly containing duplicates.
#   key: str         -> the identifying field ("batch_id", "po_id").
# OUTPUT:
#   list[dict] -> one record per key, in first-seen order of the keys.
# CALLED BY:
#   <- F0297 calculate_usable_stock() (calls)
#   <- F0301 detect_expiry_risk() (calls)
#   <- F0303 calculate_material_shortage() (calls)
#   <- F0308 estimate_supplier_lead_time() (calls)
# CALLS:
#   (none found)
def _dedupe(rows: list[dict], key: str) -> list[dict]:
    seen: dict = {}
    for row in rows:
        seen[row[key]] = row  # later record wins (latest extract)
    return list(seen.values())


# ------------------------------------------------------------------------------------------------ stock
# ===== FUNCTION: calculate_usable_stock() =====
# ID: F0297 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:48-76
# ROLE: Usable stock from SAP batches, with an itemised list of every excluded batch and why; optionally enforces the
#       minimum shelf life on arrival for a transfer (stock about to expire stays where it is: FEFO).
# INPUTS:
#   batches: list[dict]          -> inventory_batches rows (batch_id, quantity, status, expiry_date, reserved_for).
#   as_of: date                  -> SAP snapshot business date.
#   transfer_arrival: date | None-> arrival date of a planned transfer (None = local use).
# OUTPUT:
#   dict -> {"usable": float, "used_batches": [FEFO-sorted], "excluded": [{batch_id, quantity, reason}],
#            "near_expiry": [...], "rules": str}.
# EXAMPLE (synthetic fixture, WH-C sunscreen, as_of 2026-10-21): released 3,000 + 1,500 near expiry are usable (4,500);
#   800 expired, 700 blocked, 1,000 reserved, 500 in inspection are excluded with their reasons.
# CALLED BY:
#   <- F0319 Service.inventory() (calls)
#   <- F0325 Service.material_readiness() (calls)
#   <- F0326 Service._sites() (calls)
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0328 Service.replenishment() (calls)
#   <- F0329 Service.quality_check() (calls)
#   <- F0913 test_usable_stock_excludes_blocked_inspection_reserved_expired_and_flags_near_expiry() (calls)
#   <- F0914 test_duplicate_batches_are_counted_once() (calls)
# CALLS:
#   -> F0296 _dedupe() (calls)
#   -> F0294 _d() (calls)
def calculate_usable_stock(batches: list[dict], as_of: date, transfer_arrival: date | None = None) -> dict:
    """Usable quantity from SAP batches with an itemised exclusion list. With transfer_arrival, also enforce the minimum
    remaining shelf life on arrival (stock about to expire stays where it is: FEFO)."""
    # Four accumulators initialised in one tuple assignment.
    usable, excluded, near_expiry, used = 0.0, [], [], []
    for b in _dedupe(batches, "batch_id"):
        qty, expiry = float(b["quantity"]), _d(b.get("expiry_date"))
        # RULE 1: blocked / quality_inspection / reserved status -> excluded with the mapped reason. `continue` skips to the next batch.
        if b["status"] in UNUSABLE_STATUSES:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": UNUSABLE_STATUSES[b["status"]]})
            continue
        # RULE 2: any other non-"released" status is unknown -> excluded (never assume it is usable).
        if b["status"] != "released":
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"unknown status {b['status']}"})
            continue
        # RULE 3: released but allocated to a customer order (reserved_for = sales order) -> excluded.
        if b.get("reserved_for"):
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"reserved for {b['reserved_for']}"})
            continue
        # RULE 4: expired on or before the business date -> excluded.
        if expiry is not None and expiry <= as_of:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty, "reason": f"expired {expiry.isoformat()}"})
            continue
        # Days of shelf life left today (None for materials without expiry). (date - date).days -> int.
        days_left = (expiry - as_of).days if expiry else None
        # RULE 5 (transfers only): fewer than 60 days left ON ARRIVAL -> cannot travel; sell locally first (FEFO).
        if transfer_arrival and expiry is not None and (expiry - transfer_arrival).days < MIN_SHELF_LIFE_AT_ARRIVAL_DAYS:
            excluded.append({"batch_id": b["batch_id"], "quantity": qty,
                             "reason": f"only {(expiry - transfer_arrival).days} days shelf life on arrival (< {MIN_SHELF_LIFE_AT_ARRIVAL_DAYS}); sell locally (FEFO)"})
            continue
        # Still usable, but flagged when 30 days or fewer remain.
        if days_left is not None and days_left <= NEAR_EXPIRY_DAYS:
            near_expiry.append({"batch_id": b["batch_id"], "quantity": qty, "expiry_date": expiry.isoformat(), "days_left": days_left})
        usable += qty
        used.append({"batch_id": b["batch_id"], "quantity": qty, "expiry_date": expiry.isoformat() if expiry else None})
    # used_batches sorted by expiry (FEFO = first expired, first out); batches without expiry sort last ("9999").
    return {"usable": usable, "used_batches": sorted(used, key=lambda x: x["expiry_date"] or "9999"), "excluded": excluded,
            "near_expiry": near_expiry, "rules": "released, not expired, not reserved; blocked / inspection / reserved / expired excluded"}


# ===== FUNCTION: average_daily_demand() =====
# ID: F0298 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:79-83
# ROLE: Average units per day over the last `window_days` days before the business date.
# INPUTS:
#   sales: list[dict]  -> sales_history rows {"day": "YYYY-MM-DD", "quantity": n}.
#   as_of: date        -> business date (excluded: the window is [as_of - window, as_of)).
#   window_days: int   -> default 28.
# OUTPUT:
#   float -> mean daily demand rounded to 2 decimals (days without sales count as 0).
# CALLED BY:
#   <- F0317 Service._demand() (calls)
# CALLS:
#   -> F0294 _d() (calls)
def average_daily_demand(sales: list[dict], as_of: date, window_days: int = DEMAND_WINDOW_DAYS) -> float:
    """Mean units/day over the last `window_days` days (missing days count as zero demand; duplicate days counted once)."""
    start = as_of - timedelta(days=window_days)
    # Dict keyed by day: a duplicate day overwrites instead of being counted twice. Chained comparison start <= d < as_of.
    by_day = {r["day"]: float(r["quantity"]) for r in sales if start <= _d(r["day"]) < as_of}
    # Divide by the window length (not by the number of days found) so missing days count as zero demand.
    return round(sum(by_day.values()) / window_days, 2)


# ===== FUNCTION: calculate_days_of_cover() =====
# ID: F0299 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:86-90
# ROLE: How many days the usable stock lasts at the given daily demand.
# INPUTS:
#   usable: float, daily_demand: float.
# OUTPUT:
#   float | None -> days rounded to 1 decimal; None when demand is 0 (cover is unbounded).
# EXAMPLE: WH-B sunscreen 1,200 usable / ~200 per day -> ~6.0 days.
# CALLED BY:
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0915 test_days_of_cover_and_replenishment_handle_zero_demand() (calls)
# CALLS:
#   (none found)
def calculate_days_of_cover(usable: float, daily_demand: float) -> float | None:
    """Days the usable stock lasts at the given demand. None when there is no demand (cover is unbounded)."""
    if daily_demand <= 0:
        return None
    return round(usable / daily_demand, 1)


# ===== FUNCTION: calculate_replenishment_quantity() =====
# ID: F0300 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:93-97
# ROLE: Quantity needed so stock covers the transport lead time PLUS the target cover days.
# INPUTS:
#   daily_demand: float, usable: float, target_cover_days: int, lead_days: int, uom: str (default "EA").
# OUTPUT:
#   float -> max(0, demand x (target + lead) - usable), rounded by unit; 0 when there is no demand.
# CALLED BY:
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0915 test_days_of_cover_and_replenishment_handle_zero_demand() (calls)
# CALLS:
#   -> F0295 round_qty() (calls)
def calculate_replenishment_quantity(daily_demand: float, usable: float, target_cover_days: int, lead_days: int, uom: str = "EA") -> float:
    """Quantity needed so that stock covers lead time + target cover. Zero demand -> 0."""
    if daily_demand <= 0:
        return 0.0
    # max(0.0, ...) -> never a negative need when the warehouse already has enough.
    return max(0.0, round_qty(daily_demand * (target_cover_days + lead_days) - usable, uom))


# ===== FUNCTION: detect_expiry_risk() =====
# ID: F0301 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:100-111
# ROLE: Batches already expired or expiring within the horizon, most urgent first, classified expired / near_expiry / watch.
# INPUTS:
#   batches: list[dict] -> inventory_batches rows.
#   as_of: date         -> business date.
#   horizon_days: int   -> look-ahead (default 90).
# OUTPUT:
#   list[dict] -> {batch_id, item_id, location, quantity, status, expiry_date, days_left, risk}, sorted by days_left.
# CALLED BY:
#   <- F0329 Service.quality_check() (calls)
#   <- F0921 test_expiry_risk_is_ordered_most_urgent_first() (calls)
# CALLS:
#   -> F0296 _dedupe() (calls)
#   -> F0294 _d() (calls)
def detect_expiry_risk(batches: list[dict], as_of: date, horizon_days: int = 90) -> list[dict]:
    """Released batches expired or expiring within the horizon, most urgent first."""
    out = []
    for b in _dedupe(batches, "batch_id"):
        expiry = _d(b.get("expiry_date"))
        # Skip items without expiry and those expiring after the horizon.
        if expiry is None or (expiry - as_of).days > horizon_days:
            continue
        days = (expiry - as_of).days
        # Conditional expression chain: <= 0 -> expired, <= 30 -> near_expiry, else watch.
        out.append({"batch_id": b["batch_id"], "item_id": b["item_id"], "location": b["location"], "quantity": float(b["quantity"]),
                    "status": b["status"], "expiry_date": expiry.isoformat(), "days_left": days,
                    "risk": "expired" if days <= 0 else "near_expiry" if days <= NEAR_EXPIRY_DAYS else "watch"})
    return sorted(out, key=lambda x: x["days_left"])


# ------------------------------------------------------------------------------------------------ BOM / readiness
# ===== FUNCTION: calculate_bom_requirements() =====
# ID: F0302 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:115-135
# ROLE: BOM explosion: material requirements for `quantity` finished units from the newest APPROVED BOM version valid on need_date,
#       including scrap, with unit-of-measure checks against the material master.
# INPUTS:
#   bom_rows: list[dict]          -> bom_components rows of the SKU (all versions and statuses).
#   quantity: float               -> finished units to produce.
#   need_date: date               -> production / material need date.
#   material_uoms: dict[str, str] -> material_id -> stock unit from the material master.
# OUTPUT:
#   dict -> {"bom_version", "quantity", "need_date", "lines": [{material_id, qty_per_unit, scrap_pct, required_quantity, uom}]}.
# RAISES:
#   BusinessRuleError -> quantity <= 0, no approved valid version (drafts listed), missing material master, unit mismatch.
# EXAMPLE: 50,000 x SER-VITC-30 (BOM v2): PUMP-DISP-24 1/unit, 0% scrap -> 50,000 EA; BTL-GLS-30 0.5% scrap -> 50,250 EA.
# CALLED BY:
#   <- F0320 Service.bom() (calls)
#   <- F0325 Service.material_readiness() (calls)
#   <- F0916 test_bom_requirements_units_rounding_and_invalid_versions() (calls)
# CALLS:
#   -> F0293 BusinessRuleError (calls)
#   -> F0294 _d() (calls)
#   -> F0295 round_qty() (calls)
def calculate_bom_requirements(bom_rows: list[dict], quantity: float, need_date: date, material_uoms: dict[str, str]) -> dict:
    """Material requirements for `quantity` finished units from the approved BOM version valid on `need_date`."""
    if quantity <= 0:
        raise BusinessRuleError("production quantity must be positive")
    # Keep rows that are approved AND valid on need_date (valid_to None = open-ended).
    valid = [r for r in bom_rows if r["status"] == "approved" and _d(r["valid_from"]) <= need_date and (r.get("valid_to") is None or need_date <= _d(r["valid_to"]))]
    # Distinct versions among the valid rows, sorted ("v1" < "v2").
    versions = sorted({r["bom_version"] for r in valid})
    if not versions:
        # Explain the refusal: list draft versions that exist but must not be used for planning.
        drafts = sorted({r["bom_version"] for r in bom_rows if r["status"] != "approved"})
        raise BusinessRuleError(f"no approved BOM valid on {need_date.isoformat()}" + (f" (draft versions {', '.join(drafts)} cannot be used)" if drafts else ""))
    # The newest valid approved version wins.
    version = versions[-1]
    lines = []
    # Generator expression: iterate only the rows of the chosen version.
    for r in (r for r in valid if r["bom_version"] == version):
        stock_uom = material_uoms.get(r["material_id"])
        # Master-data checks: never compute with an unknown material or mixed units (e.g. BOM in ML, stock in KG).
        if stock_uom is None:
            raise BusinessRuleError(f"material {r['material_id']} in BOM {version} has no material master")
        if stock_uom != r["uom"]:
            raise BusinessRuleError(f"unit of measure mismatch for {r['material_id']}: BOM uses {r['uom']}, stock is kept in {stock_uom}")
        # required = quantity x qty_per_unit x (1 + scrap% / 100), rounded per unit.
        required = round_qty(quantity * float(r["qty_per_unit"]) * (1 + float(r["scrap_pct"]) / 100), r["uom"])
        lines.append({"material_id": r["material_id"], "qty_per_unit": float(r["qty_per_unit"]), "scrap_pct": float(r["scrap_pct"]),
                      "required_quantity": required, "uom": r["uom"]})
    return {"bom_version": version, "quantity": quantity, "need_date": need_date.isoformat(), "lines": lines}


# ===== FUNCTION: calculate_material_shortage() =====
# ID: F0303 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:138-156
# ROLE: Missing quantity of ONE material on the need date. Inbound supply counts only if the PO is CONFIRMED and promised
#       on/before the need date; late and unconfirmed POs are listed separately (they do not reduce the shortage).
# INPUTS:
#   required: float               -> quantity needed (from calculate_bom_requirements).
#   usable: float                 -> usable stock (from calculate_usable_stock).
#   purchase_orders: list[dict]   -> open/confirmed PO rows of the material at the plant.
#   need_date: date, uom: str.
# OUTPUT:
#   dict -> required, usable, confirmed_timely_inbound, missing, need_date, timely/late/unconfirmed purchase orders, uom,
#           status "short" | "covered".
# EXAMPLE (planted scenario 1): required 50,000 pumps, usable 30,000, PO 25,000 confirmed but promised after the need date (late),
#   PO 8,000 unconfirmed -> inbound 0 -> missing = 50,000 - 30,000 - 0 = 20,000.
# CALLED BY:
#   <- F0325 Service.material_readiness() (calls)
#   <- F0917 test_shortage_counts_only_confirmed_timely_inbound_and_dedupes_pos() (calls)
# CALLS:
#   -> F0296 _dedupe() (calls)
#   -> F0294 _d() (calls)
#   -> F0295 round_qty() (calls)
def calculate_material_shortage(required: float, usable: float, purchase_orders: list[dict], need_date: date, uom: str) -> dict:
    """Missing quantity on the need date. Inbound counts only if confirmed (or received) and promised on/before need_date."""
    timely, late, unconfirmed = [], [], []
    for po in _dedupe(purchase_orders, "po_id"):
        # Cancelled POs bring nothing; received POs are already in stock (counted in usable).
        if po["status"] in ("cancelled", "received"):
            continue
        # Open quantity = ordered - already received (`or 0` turns None into 0).
        open_qty = float(po["quantity"]) - float(po.get("received_quantity") or 0)
        entry = {"po_id": po["po_id"], "supplier_id": po["supplier_id"], "quantity": open_qty, "promised_date": po["promised_date"], "status": po["status"]}
        # Classify: not confirmed by the supplier / confirmed in time / confirmed but late.
        if po["status"] != "confirmed":
            unconfirmed.append(entry)
        elif _d(po["promised_date"]) <= need_date:
            timely.append(entry)
        else:
            late.append(entry)
    # Only timely confirmed inbound reduces the shortage.
    inbound = sum(p["quantity"] for p in timely)
    missing = max(0.0, round_qty(required - usable - inbound, uom))
    return {"required": required, "usable": usable, "confirmed_timely_inbound": inbound, "missing": missing, "need_date": need_date.isoformat(),
            "timely_purchase_orders": timely, "late_purchase_orders": late, "unconfirmed_purchase_orders": unconfirmed, "uom": uom,
            "status": "short" if missing > 0 else "covered"}


# ------------------------------------------------------------------------------------------------ transfers / supply options
# ===== CLASS: Site =====
# ID: F0304 · class · used
# ORIGINAL FILE: backend/scinsight/business.py:160-166
# ROLE: One warehouse as seen by transfer planning.
# FIELDS:
#   code: str                   -> warehouse code.
#   usable_transferable: float  -> usable AND eligible to travel (shelf life on arrival respected).
#   usable_total: float         -> all usable stock (including near-expiry stock that must stay).
#   daily_demand: float         -> its own demand per day.
#   target_cover_days: int      -> days of cover it must keep for itself.
# CALLED BY:
#   <- F0305 generate_transfer_candidates() (references)
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0918 test_transfer_candidates_feasibility_and_ranking() (calls)
# CALLS:
#   (none found)
@dataclass
class Site:
    code: str
    usable_transferable: float  # usable and eligible for transfer (shelf life on arrival respected)
    usable_total: float
    daily_demand: float
    target_cover_days: int


# ===== FUNCTION: generate_transfer_candidates() =====
# ID: F0305 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:169-181
# ROLE: Donor warehouses and their surplus = transferable stock above what they must keep for their own target cover.
#       Stock that cannot travel (short shelf life) covers local demand first (FEFO).
# INPUTS:
#   receiver: str            -> the warehouse that needs stock (excluded from donors).
#   sites: dict[str, Site]   -> candidate sites by code.
# OUTPUT:
#   list[dict] -> [{"donor", "surplus", "donor_keeps_days"}] sorted by surplus, largest first.
# CALLED BY:
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0918 test_transfer_candidates_feasibility_and_ranking() (calls)
# CALLS:
#   -> F0304 Site (references)
def generate_transfer_candidates(receiver: str, sites: dict[str, Site]) -> list[dict]:
    """Donor warehouses with surplus = transferable stock above their own target cover (FEFO: near-expiry stock is used locally first)."""
    out = []
    for code, s in sites.items():
        if code == receiver:
            continue
        # Stock the donor must keep: its own demand x its target cover days.
        keep = s.daily_demand * s.target_cover_days
        local_only = s.usable_total - s.usable_transferable  # stock that cannot travel covers local demand first
        # Surplus = transferable - (part of `keep` NOT already covered by local-only stock), never negative.
        surplus = max(0.0, s.usable_transferable - max(0.0, keep - local_only))
        surplus = float(math.floor(surplus + 1e-9))  # whole units, rounded DOWN: never promise stock that is not there
        if surplus > 0:
            out.append({"donor": code, "surplus": surplus, "donor_keeps_days": s.target_cover_days})
    # key=lambda c: -c["surplus"] -> descending order by surplus.
    return sorted(out, key=lambda c: -c["surplus"])


# ===== FUNCTION: evaluate_transfer_feasibility() =====
# ID: F0306 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:184-203
# ROLE: Is a transfer from a donor possible and in time? Quantity = min(need, surplus, lane capacity); cost only from lane master data.
# INPUTS:
#   candidate: dict             -> {"donor", "surplus", ...} from generate_transfer_candidates.
#   need: float                 -> quantity the receiver needs.
#   lane: dict | None           -> transport_lanes row donor -> receiver (None = no lane in SAP).
#   as_of: date                 -> business date (shipment leaves today).
#   stockout_date: date | None  -> projected stock-out at the receiver.
# OUTPUT:
#   dict -> candidate + lane_id, mode, lead_days, quantity, arrival_date, in_time, cost_eur, cost_per_unit_eur, covers_need,
#           feasible, reasons[].
# CALLED BY:
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0918 test_transfer_candidates_feasibility_and_ranking() (calls)
# CALLS:
#   (none found)
def evaluate_transfer_feasibility(candidate: dict, need: float, lane: dict | None, as_of: date, stockout_date: date | None) -> dict:
    """Is the transfer possible and in time? Reasons are listed; costs come only from the lane master data."""
    reasons = []
    # No lane in master data -> infeasible (never invent a transport route). {**candidate, ...} copies the dict and adds keys.
    if lane is None:
        return {**candidate, "feasible": False, "reasons": ["no transport lane in SAP master data"], "quantity": 0}
    qty = min(need, candidate["surplus"], float(lane["capacity_units"]))
    if qty <= 0:
        reasons.append("no transferable surplus")
    # Explanations for partial coverage (":.0f" formats a float without decimals).
    if candidate["surplus"] < need:
        reasons.append(f"donor surplus {candidate['surplus']:.0f} covers only part of the need {need:.0f}")
    if float(lane["capacity_units"]) < need:
        reasons.append(f"lane capacity {lane['capacity_units']} per shipment")
    arrival = as_of + timedelta(days=int(lane["lead_days"]))
    # In time when there is no projected stock-out, or the shipment arrives on/before it.
    in_time = stockout_date is None or arrival <= stockout_date
    if not in_time:
        reasons.append(f"arrives {arrival.isoformat()}, after the stock-out on {stockout_date.isoformat()}")
    # Cost = quantity x cost per unit + fixed cost per shipment, EUR to 2 decimals (0 when nothing moves).
    cost = round(qty * float(lane["cost_per_unit_eur"]) + float(lane["fixed_cost_eur"]), 2) if qty > 0 else 0.0
    return {**candidate, "lane_id": lane["lane_id"], "mode": lane["mode"], "lead_days": int(lane["lead_days"]), "quantity": qty,
            "arrival_date": arrival.isoformat(), "in_time": in_time, "cost_eur": cost, "cost_per_unit_eur": float(lane["cost_per_unit_eur"]),
            "covers_need": qty >= need, "feasible": qty > 0 and in_time, "reasons": reasons}


# ===== FUNCTION: compare_supply_options() =====
# ID: F0307 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:206-215
# ROLE: Rank supply options (transfers, suppliers, expedites, production allocation) and mark at most ONE as recommended.
#       Order: feasible first, then in time, then full coverage, then lowest cost, then fastest.
# INPUTS:
#   options: list[dict] -> each with optional feasible, in_time, covers_need, cost_eur, lead_days.
# OUTPUT:
#   list[dict] -> the same dicts sorted, each with "rank" (1..n) and "recommended" (True only for rank 1 if feasible AND in time).
# CALLED BY:
#   <- F0325 Service.material_readiness() (calls)
#   <- F0327 Service.warehouse_balancing() (calls)
#   <- F0328 Service.replenishment() (calls)
#   <- F0918 test_transfer_candidates_feasibility_and_ranking() (calls)
#   <- F0919 test_nothing_is_recommended_when_no_option_is_in_time() (calls)
# CALLS:
#   (none found)
def compare_supply_options(options: list[dict]) -> list[dict]:
    """Rank options: feasible and in time first, then full coverage, then lowest cost, then fastest. Adds rank + recommended.
    An option is recommended only if it is feasible AND arrives in time; otherwise nothing is recommended (no false comfort)."""
    # Tuple sort key: Python compares element by element. `not True` == False sorts first. Missing cost -> 1e12 (last),
    # missing lead time -> 999 (last).
    ranked = sorted(options, key=lambda o: (not o.get("feasible"), not o.get("in_time", True), not o.get("covers_need"),
                                            o.get("cost_eur") if o.get("cost_eur") is not None else 1e12,
                                            o.get("lead_days") if o.get("lead_days") is not None else 999))
    # enumerate(..., 1) numbers from 1. The dicts are modified in place (they are the same objects as in `options`).
    for i, o in enumerate(ranked, 1):
        o["rank"] = i
        o["recommended"] = i == 1 and bool(o.get("feasible")) and bool(o.get("in_time", True))
    return ranked


# ------------------------------------------------------------------------------------------------ lead time / learning
# ===== FUNCTION: estimate_supplier_lead_time() =====
# ID: F0308 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:219-231
# ROLE: Empirical supplier lead time from goods receipts (order date -> receipt date): mean, p90, min, max, on-time rate.
# INPUTS:
#   receipts: list[dict]            -> received purchase_orders rows (order_date, promised_date, received_date).
#   contract_lead_days: int | None  -> contractual lead time for comparison.
# OUTPUT:
#   dict -> receipts, estimate_days, p90_days, min_days, max_days, contract_days, on_time_rate,
#           status "ok" (>= 3 receipts) | "low_confidence" | "insufficient_history", basis.
# CALLED BY:
#   <- F0324 Service._supplier_options() (calls)
#   <- F0332 Service.lead_time() (calls)
#   <- F0920 test_lead_time_estimate_and_prediction_error_and_reconciliation() (calls)
# CALLS:
#   -> F0296 _dedupe() (calls)
#   -> F0294 _d() (calls)
def estimate_supplier_lead_time(receipts: list[dict], contract_lead_days: int | None) -> dict:
    """Empirical lead time from received purchase orders (order date -> goods receipt). Duplicate receipts counted once."""
    rows = [r for r in _dedupe(receipts, "po_id") if r.get("received_date")]
    # Lead time in days for each receipt, sorted ascending (needed for min / max / p90).
    leads = sorted((_d(r["received_date"]) - _d(r["order_date"])).days for r in rows)
    # No history -> explicit "insufficient_history" result instead of a guess.
    if not leads:
        return {"receipts": 0, "estimate_days": None, "p90_days": None, "contract_days": contract_lead_days,
                "status": "insufficient_history", "basis": "no goods receipts in the SAP history"}
    mean = sum(leads) / len(leads)
    # Nearest-rank 90th percentile: index ceil(0.9 n) - 1, capped at the last element.
    p90 = leads[min(len(leads) - 1, math.ceil(0.9 * len(leads)) - 1)]
    # Booleans sum as 0/1: share of receipts that arrived on/before the promised date.
    on_time = sum((_d(r["received_date"]) <= _d(r["promised_date"])) for r in rows) / len(rows)
    return {"receipts": len(leads), "estimate_days": round(mean, 1), "p90_days": p90, "min_days": leads[0], "max_days": leads[-1],
            "contract_days": contract_lead_days, "on_time_rate": round(on_time, 3), "status": "ok" if len(leads) >= 3 else "low_confidence",
            "basis": f"mean of {len(leads)} goods receipts (order date -> receipt date)"}


# ===== FUNCTION: calculate_prediction_error() =====
# ID: F0309 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:234-238
# ROLE: Prediction error of one outcome: signed = actual - predicted (positive = later / higher than predicted).
# INPUTS:
#   predicted: float, actual: float.
# OUTPUT:
#   dict -> {"predicted", "actual", "signed_error", "absolute_error", "percentage_error" (None when predicted is 0)}.
# EXAMPLE (REC-HIST-0001): predicted 5 days, actual 9 -> signed 4, absolute 4, percentage 80.0.
# CALLED BY:
#   <- F0310 reconcile_actual_outcome() (calls)
#   <- F0920 test_lead_time_estimate_and_prediction_error_and_reconciliation() (calls)
# CALLS:
#   (none found)
def calculate_prediction_error(predicted: float, actual: float) -> dict:
    """Signed error = actual - predicted (positive = later/higher than predicted)."""
    signed = actual - predicted
    return {"predicted": predicted, "actual": actual, "signed_error": signed, "absolute_error": abs(signed),
            "percentage_error": round(100 * signed / predicted, 1) if predicted else None}


# ===== FUNCTION: reconcile_actual_outcome() =====
# ID: F0310 · function · used
# ORIGINAL FILE: backend/scinsight/business.py:241-252
# ROLE: Match a lead-time prediction with the SAP goods receipt of its purchase order (decision outcome learning).
# INPUTS:
#   prediction: dict                -> {"predicted": days, ...} stored on the recommendation.
#   purchase_order: dict | None     -> the SAP PO row (None = not found).
#   completeness_threshold: float   -> received/ordered ratio needed for a "verified" outcome (default 98%).
# OUTPUT:
#   dict -> status "missing" | "pending" | "verified" | "incomplete" + metric, actual, error, received_ratio, quality_flags,
#           source_document, received_date.
# CALLED BY:
#   <- F0341 Service.reconcile() (calls)
#   <- F0920 test_lead_time_estimate_and_prediction_error_and_reconciliation() (calls)
# CALLS:
#   -> F0294 _d() (calls)
#   -> F0309 calculate_prediction_error() (calls)
def reconcile_actual_outcome(prediction: dict, purchase_order: dict | None, completeness_threshold: float = 0.98) -> dict:
    """Match a lead-time prediction with the SAP goods receipt of its purchase order."""
    if purchase_order is None:
        return {"status": "missing", "reason": "no SAP purchase order record for the prediction"}
    if not purchase_order.get("received_date"):
        return {"status": "pending", "reason": f"{purchase_order['po_id']} has no goods receipt yet"}
    # Actual lead time in days (goods receipt date - order date).
    actual = (_d(purchase_order["received_date"]) - _d(purchase_order["order_date"])).days
    ratio = float(purchase_order.get("received_quantity") or 0) / float(purchase_order["quantity"])
    # A partial delivery is flagged; ":.0%" formats 0.97 as "97%".
    flags = [] if ratio >= completeness_threshold else [f"partial delivery {ratio:.0%} of ordered quantity"]
    return {"status": "verified" if not flags else "incomplete", "metric": "lead_time_days", "actual": actual,
            "error": calculate_prediction_error(float(prediction["predicted"]), float(actual)), "received_ratio": round(ratio, 3),
            "quality_flags": flags, "source_document": purchase_order["po_id"], "received_date": purchase_order["received_date"]}
