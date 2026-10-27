# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/service.py
# What this module is: the use-case layer of SCInsight. Each FastAPI route calls ONE Service method, which
#   1. checks the tenant's SAP snapshot is fresh, 2. reads SAP rows with parameterised SQL,
#   3. calls the pure functions of business.py (alias `bz`), 4. stores the result as a calculation (CALC-...)
#   with provenance and an audit entry. It also implements recommendations, human review, SAP execution records,
#   outcome reconciliation and learning metrics.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Use cases of the SupplyChain Insight AI business-tool service (called by the FastAPI routes and the tests).

Every calculation reads the tenant's current SAP snapshot, runs the deterministic functions in business.py, and is stored
in agent_runs with a calculation_id. Recommendations are created only FROM a stored calculation (the server copies the
quantities; nothing numeric is accepted from an LLM), stay pending until an authorised human reviews them, and are never
written to SAP: an approved action waits for a separately recorded SAP execution event.
"""
from __future__ import annotations

# json: results / actions are stored as JSON text columns. uuid: random ids (CALC-..., REC-..., HD-..., SX-...).
import json
import uuid
from datetime import date, timedelta

# Raising HTTPException here makes the route answer with that status code + {"detail": ...}.
from fastapi import HTTPException

# The deterministic calculations, imported as the short alias `bz`.
from backend.scinsight import business as bz
from backend.scinsight.db import Database, now_iso
from backend.scinsight.security import REVIEW_AUTHORITY, Principal, Security
from backend.scinsight.settings import SciSettings

# Which review domain (and therefore which reviewer role) each calculation kind belongs to.
DOMAIN_OF = {"material_readiness": "factory", "warehouse_balancing": "warehouse", "replenishment": "inventory",
             "lead_time_estimate": "procurement", "quality_check": "quality", "demand_forecast": "inventory"}
# Reviewer verb -> recommendation status after the review.
REVIEW_DECISIONS = {"approve": "approved", "reject": "rejected", "modify": "modified", "defer": "deferred"}


# ===== CLASS: Service =====
# ID: F0311 · class · used
# ORIGINAL FILE: backend/scinsight/service.py:26-529
# ROLE: All SCInsight use cases. One instance per app, created in create_app() and captured by the routes.
# FIELDS:
#   db: Database, settings: SciSettings, security: Security.
# CALLED BY:
#   <- F0112 create_app() (calls)
# CALLS:
#   (none found)
class Service:
    # ===== FUNCTION: Service.__init__() =====
    # ID: F0312 · method · used (framework)
    # ORIGINAL FILE: backend/scinsight/service.py:27-28
    # ROLE: Store the three collaborators.
    # INPUTS:
    #   db: Database, settings: SciSettings, security: Security.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0418 Database (references)
    #   -> F0013 SciSettings (references)
    #   -> F0774 Security (references)
    def __init__(self, db: Database, settings: SciSettings, security: Security):
        self.db, self.settings, self.security = db, settings, security

    # ------------------------------------------------------------------ snapshot + helpers
    # ===== FUNCTION: Service.snapshot() =====
    # ID: F0313 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:31-40
    # ROLE: The tenant's newest VALID SAP snapshot, refused (409) when missing or older than SCI_SNAPSHOT_MAX_AGE_DAYS.
    # INPUTS:
    #   tenant: str -> tenant id.
    # OUTPUT:
    #   dict -> the sap_snapshots row + "as_of" (date) + "age_days" (int).
    # CALLED BY:
    #   <- F0115 create_app.biz_date() (calls)
    #   <- F0117 create_app.context() (calls)
    #   <- F0118 create_app.validate_context() (calls)
    #   <- F0319 Service.inventory() (calls)
    #   <- F0320 Service.bom() (calls)
    #   <- F0321 Service.table() (calls)
    #   <- F0323 Service.suppliers() (calls)
    #   <- F0325 Service.material_readiness() (calls)
    #   <- F0327 Service.warehouse_balancing() (calls)
    #   <- F0328 Service.replenishment() (calls)
    #   <- F0329 Service.quality_check() (calls)
    #   <- F0330 Service.forecast_demand() (calls)
    # CALLS:
    #   -> F0422 Database.one() (calls)
    def snapshot(self, tenant: str) -> dict:
        snap = self.db.one("select * from sap_snapshots where tenant_id=? and status='valid' order by extracted_at desc limit 1", (tenant,))
        # 409 Conflict: the request is valid but the data state does not allow planning.
        if snap is None:
            raise HTTPException(status_code=409, detail="No valid SAP snapshot for this tenant — refresh the SAP extract before planning")
        as_of = date.fromisoformat(snap["as_of_date"])
        # "Today" = configured business date, or the snapshot date itself (synthetic data is frozen in time).
        today = self.settings.sci_business_date or as_of
        age = (today - as_of).days
        # BUSINESS RULE: never plan on stale SAP data.
        if age > self.settings.sci_snapshot_max_age_days:
            raise HTTPException(status_code=409, detail=f"SAP snapshot {snap['id']} is {age} days old (max {self.settings.sci_snapshot_max_age_days}) — refresh the SAP extract")
        # {**snap, ...}: copy of the row with two extra keys.
        return {**snap, "as_of": as_of, "age_days": age}

    # ===== FUNCTION: Service._save_run() =====
    # ID: F0314 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:42-50
    # ROLE: Persist a calculation result with a new CALC id and SAP provenance, and audit it. Every calculation ends here.
    # INPUTS:
    #   p: Principal, kind: str (e.g. "material_readiness"), request: dict (validated input), result: dict, snap: dict (snapshot row).
    # OUTPUT:
    #   dict -> {"calculation_id", "kind", **result, "provenance": {snapshot_id, source_system, extracted_at, as_of_date, synthetic}}.
    # CALLED BY:
    #   <- F0325 Service.material_readiness() (calls)
    #   <- F0327 Service.warehouse_balancing() (calls)
    #   <- F0328 Service.replenishment() (calls)
    #   <- F0329 Service.quality_check() (calls)
    #   <- F0330 Service.forecast_demand() (calls)
    #   <- F0332 Service.lead_time() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0423 Database.execute() (calls)
    #   -> F0416 now_iso() (calls)
    #   -> F0779 Security.audit() (calls)
    def _save_run(self, p: Principal, kind: str, request: dict, result: dict, snap: dict) -> dict:
        # uuid4().hex = 32 random hex chars; first 12, uppercase -> e.g. CALC-4DC2A103412B.
        calc_id = f"CALC-{uuid.uuid4().hex[:12].upper()}"
        provenance = {"snapshot_id": snap["id"], "source_system": snap["source_system"], "extracted_at": snap["extracted_at"],
                      "as_of_date": snap["as_of_date"], "synthetic": bool(snap["synthetic"])}
        body = {"calculation_id": calc_id, "kind": kind, **result, "provenance": provenance}
        # Stored in agent_runs: later the recommendation copies its quantities from HERE (never from LLM text).
        self.db.execute("insert into agent_runs(id,tenant_id,user_id,kind,request,result,snapshot_id,created_at) values(?,?,?,?,?,?,?,?)",
                        (calc_id, p.tenant_id, p.user_id, kind, json.dumps(request, default=str), json.dumps(body, default=str), snap["id"], now_iso()))
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), f"calc.{kind}", {"calculation_id": calc_id})
        return body

    # ===== FUNCTION: Service.calculation() =====
    # ID: F0315 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:52-56
    # ROLE: Read a stored calculation of the caller's tenant.
    # INPUTS:
    #   p: Principal, calc_id: str.
    # OUTPUT:
    #   dict -> the stored body (404 when unknown or owned by another tenant).
    # CALLED BY:
    #   <- F0132 create_app.calculation() (calls)
    #   <- F0333 Service.create_decision() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0422 Database.one() (calls)
    def calculation(self, p: Principal, calc_id: str) -> dict:
        row = self.db.one("select * from agent_runs where id=? and tenant_id=?", (calc_id, p.tenant_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"calculation {calc_id} not found for this tenant")
        # The result column holds JSON text -> parse back into a dict.
        return json.loads(row["result"])

    # ===== FUNCTION: Service._batches() =====
    # ID: F0316 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:58-63
    # ROLE: Inventory batches of one item, optionally at one location (the input of calculate_usable_stock).
    # INPUTS:
    #   tenant: str, item: str, location: str | None.
    # OUTPUT:
    #   list[dict] -> inventory_batches rows.
    # CALLED BY:
    #   <- F0325 Service.material_readiness() (calls)
    #   <- F0326 Service._sites() (calls)
    #   <- F0328 Service.replenishment() (calls)
    #   <- F0329 Service.quality_check() (calls)
    # CALLS:
    #   -> F0421 Database.query() (calls)
    def _batches(self, tenant: str, item: str, location: str | None = None) -> list[dict]:
        # The SQL is extended with fixed text; values always go through bound parameters.
        sql, params = "select * from inventory_batches where tenant_id=? and item_id=?", [tenant, item]
        if location:
            sql += " and location=?"
            params.append(location)
        return self.db.query(sql, params)

    # ===== FUNCTION: Service._demand() =====
    # ID: F0317 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:65-66
    # ROLE: Average daily demand of a SKU at a warehouse (28-day window).
    # INPUTS:
    #   tenant, sku, wh: str; as_of: date.
    # OUTPUT:
    #   float -> units per day.
    # CALLED BY:
    #   <- F0326 Service._sites() (calls)
    # CALLS:
    #   -> F0298 average_daily_demand() (calls)
    #   -> F0421 Database.query() (calls)
    def _demand(self, tenant: str, sku: str, wh: str, as_of: date) -> float:
        return bz.average_daily_demand(self.db.query("select day, quantity from sales_history where tenant_id=? and sku=? and warehouse=?", (tenant, sku, wh)), as_of)

    # ===== FUNCTION: Service._require_item() =====
    # ID: F0318 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:68-75
    # ROLE: Is the code a product or a material of this tenant? Returns its kind and unit (404 otherwise).
    # INPUTS:
    #   tenant: str, item: str.
    # OUTPUT:
    #   tuple[str, str] -> ("product" | "material", uom).
    # CALLED BY:
    #   <- F0327 Service.warehouse_balancing() (calls)
    #   <- F0328 Service.replenishment() (calls)
    #   <- F0329 Service.quality_check() (calls)
    # CALLS:
    #   -> F0422 Database.one() (calls)
    def _require_item(self, tenant: str, item: str) -> tuple[str, str]:
        prod = self.db.one("select sku, uom from products where tenant_id=? and sku=?", (tenant, item))
        if prod:
            return "product", prod["uom"]
        mat = self.db.one("select material_id, uom from materials where tenant_id=? and material_id=?", (tenant, item))
        if mat:
            return "material", mat["uom"]
        raise HTTPException(status_code=404, detail=f"{item} is not a product or material of this tenant")

    # ------------------------------------------------------------------ SAP reads (read-only)
    # ===== FUNCTION: Service.inventory() =====
    # ID: F0319 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:78-97
    # ROLE: GET /api/v1/sap/inventory: batches + per (location, item) summary of on-hand, usable, excluded, near expiry.
    # INPUTS:
    #   p: Principal, location: str | None, item: str | None, include_unusable: bool.
    # OUTPUT:
    #   dict -> {"snapshot", "as_of", "items": [summaries], "batches": [rows], "rules"}.
    # CALLED BY:
    #   <- F0119 create_app.sap_inventory() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0297 calculate_usable_stock() (calls)
    def inventory(self, p: Principal, location: str | None, item: str | None, include_unusable: bool) -> dict:
        snap = self.snapshot(p.tenant_id)
        sql, params = "select * from inventory_batches where tenant_id=?", [p.tenant_id]
        if location:
            sql += " and location=?"
            params.append(location)
        if item:
            sql += " and item_id=?"
            params.append(item)
        rows = self.db.query(sql + " order by location, item_id, batch_id", params)
        # Group rows by (location, item) — dict.setdefault creates the list the first time a key is seen.
        groups: dict[tuple, list] = {}
        for r in rows:
            groups.setdefault((r["location"], r["item_id"]), []).append(r)
        summary = []
        for (loc, it), batches in groups.items():
            u = bz.calculate_usable_stock(batches, snap["as_of"])
            summary.append({"location": loc, "item_id": it, "uom": batches[0]["uom"], "on_hand": sum(float(b["quantity"]) for b in batches),
                            "usable": u["usable"], "excluded": u["excluded"], "near_expiry": u["near_expiry"]})
        # include_unusable=False -> only released batches in the raw list.
        return {"snapshot": snap["id"], "as_of": snap["as_of_date"], "items": summary, "batches": rows if include_unusable else
                [r for r in rows if r["status"] == "released"], "rules": "usable = released, not expired, not reserved"}

    # ===== FUNCTION: Service.bom() =====
    # ID: F0320 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:99-109
    # ROLE: GET /api/v1/sap/bom/{sku}: all BOM rows + the requirements of ONE unit from the version valid on the date.
    # INPUTS:
    #   p: Principal, sku: str, on: date | None (None = snapshot date).
    # OUTPUT:
    #   dict -> {"sku", "snapshot", "current_for_one_unit" (or {"error"}), "versions"}.
    # CALLED BY:
    #   <- F0120 create_app.sap_bom() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0302 calculate_bom_requirements() (calls)
    #   -> F0293 BusinessRuleError (references)
    def bom(self, p: Principal, sku: str, on: date | None) -> dict:
        snap = self.snapshot(p.tenant_id)
        rows = self.db.query("select * from bom_components where tenant_id=? and sku=? order by bom_version, material_id", (p.tenant_id, sku))
        if not rows:
            raise HTTPException(status_code=404, detail=f"No BOM for {sku}")
        # material_id -> stock unit, for the unit-of-measure check.
        uoms = {m["material_id"]: m["uom"] for m in self.db.query("select material_id, uom from materials where tenant_id=?", (p.tenant_id,))}
        try:
            current = bz.calculate_bom_requirements(rows, 1, on or snap["as_of"], uoms)
        # A business-rule problem is SHOWN (e.g. unit mismatch) rather than failing the whole read.
        except bz.BusinessRuleError as exc:
            current = {"error": str(exc)}
        return {"sku": sku, "snapshot": snap["id"], "current_for_one_unit": current, "versions": rows}

    # ===== FUNCTION: Service.table() =====
    # ID: F0321 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:111-118
    # ROLE: Generic read of a SAP table with equality filters (production_orders, purchase_orders, warehouses).
    # INPUTS:
    #   p: Principal, table: str (fixed by the route), filters: dict column -> value (None = no filter).
    # OUTPUT:
    #   dict -> {"snapshot", "as_of", "items": [rows]}.
    # CALLED BY:
    #   <- F0121 create_app.sap_production_orders() (calls)
    #   <- F0122 create_app.sap_purchase_orders() (calls)
    #   <- F0123 create_app.sap_warehouses() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0421 Database.query() (calls)
    def table(self, p: Principal, table: str, filters: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        sql, params = f"select * from {table} where tenant_id=?", [p.tenant_id]  # noqa: S608 - table is chosen by the route, never by the client
        for column, value in filters.items():
            if value is not None:
                # Column names come from the route's code (fixed keys); the value is bound as a parameter.
                sql += f" and {column}=?"
                params.append(value)
        return {"snapshot": snap["id"], "as_of": snap["as_of_date"], "items": self.db.query(sql, params)}

    # ===== FUNCTION: Service.catalog() =====
    # ID: F0322 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:120-131
    # ROLE: Identifier catalog (codes + names, NO quantities) so an agent can map "vitamin C serum" to SER-VITC-30.
    # INPUTS:
    #   tenant: str.
    # OUTPUT:
    #   dict -> {"products", "materials", "locations", "suppliers", "production_orders"}: lists of "CODE = name" strings.
    # CALLED BY:
    #   <- F0118 create_app.validate_context() (calls)
    # CALLS:
    #   -> F0421 Database.query() (references)
    def catalog(self, tenant: str) -> dict:
        """Identifiers and names only (no quantities): lets an agent map 'vitamin C serum' to SER-VITC-30. Every code the agent
        then sends is validated again by the calculation endpoints."""
        # Local alias of the bound method to keep the lines short.
        q = self.db.query
        return {
            "products": [f"{r['sku']} = {r['name']}" for r in q("select sku, name from products where tenant_id=? order by sku", (tenant,))],
            "materials": [f"{r['material_id']} = {r['name']}" for r in q("select material_id, name from materials where tenant_id=? order by material_id", (tenant,))],
            "locations": [f"{r['code']} = {r['name']} ({r['kind']})" for r in q("select code, name, kind from warehouses where tenant_id=? order by code", (tenant,))],
            "suppliers": [f"{r['supplier_id']} = {r['name']}" for r in q("select supplier_id, name from suppliers where tenant_id=? order by supplier_id", (tenant,))],
            "production_orders": [f"{r['order_id']} = {r['sku']} starting {r['start_date']}" for r in
                                  q("select order_id, sku, start_date from production_orders where tenant_id=? order by order_id", (tenant,))],
        }

    # ===== FUNCTION: Service.suppliers() =====
    # ID: F0323 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:133-139
    # ROLE: GET /api/v1/sap/suppliers: suppliers with their supplier items nested.
    # INPUTS:
    #   p: Principal.
    # OUTPUT:
    #   dict -> {"snapshot", "items": [supplier rows with "items"]}.
    # CALLED BY:
    #   <- F0124 create_app.sap_suppliers() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0421 Database.query() (calls)
    def suppliers(self, p: Principal) -> dict:
        snap = self.snapshot(p.tenant_id)
        sups = self.db.query("select * from suppliers where tenant_id=? order by supplier_id", (p.tenant_id,))
        items = self.db.query("select * from supplier_items where tenant_id=?", (p.tenant_id,))
        # Nest the items of each supplier (in-memory join).
        for s in sups:
            s["items"] = [i for i in items if i["supplier_id"] == s["supplier_id"]]
        return {"snapshot": snap["id"], "items": sups}

    # ------------------------------------------------------------------ material readiness (factory)
    # ===== FUNCTION: Service._supplier_options() =====
    # ID: F0324 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:142-158
    # ROLE: Purchase options for a missing material from every supplier item: demonstrated lead time (>= 3 receipts) or contract,
    #       MOQ-adjusted quantity, arrival vs need date, cost; unapproved suppliers are listed but infeasible.
    # INPUTS:
    #   tenant: str, material: str, qty: float (missing quantity), need: date, as_of: date.
    # OUTPUT:
    #   list[dict] -> options {option, supplier_id, approved, quantity, lead_days, lead_time_basis, contract_lead_days,
    #                 arrival_date, in_time, cost_eur, unit_price_eur, covers_need, feasible, reasons}.
    # CALLED BY:
    #   <- F0325 Service.material_readiness() (calls)
    #   <- F0328 Service.replenishment() (calls)
    # CALLS:
    #   -> F0421 Database.query() (calls)
    #   -> F0308 estimate_supplier_lead_time() (calls)
    def _supplier_options(self, tenant: str, material: str, qty: float, need: date, as_of: date) -> list[dict]:
        options = []
        # SQL JOIN supplier_items x suppliers to get the name and the approval flag (two adjacent strings are concatenated by Python).
        for si in self.db.query("select si.*, s.name, s.approved from supplier_items si join suppliers s on s.tenant_id=si.tenant_id and s.supplier_id=si.supplier_id "
                                "where si.tenant_id=? and si.material_id=?", (tenant, material)):
            receipts = self.db.query("select * from purchase_orders where tenant_id=? and supplier_id=? and received_date is not null", (tenant, si["supplier_id"]))
            est = bz.estimate_supplier_lead_time(receipts, si["contract_lead_time_days"])
            # BUSINESS RULE: trust the demonstrated lead time only with at least 3 receipts; otherwise use the contract.
            lead = est["estimate_days"] if est["receipts"] >= 3 else si["contract_lead_time_days"]
            # Order at least the supplier's minimum order quantity.
            order_qty = max(qty, float(si["moq"]))
            arrival = as_of + timedelta(days=int(round(lead)))
            options.append({"option": f"order from {si['name']}", "supplier_id": si["supplier_id"], "approved": bool(si["approved"]),
                            "quantity": order_qty, "lead_days": round(lead, 1), "lead_time_basis": "demonstrated (goods receipts)" if est["receipts"] >= 3 else "contract",
                            "contract_lead_days": si["contract_lead_time_days"], "arrival_date": arrival.isoformat(), "in_time": arrival <= need,
                            "cost_eur": round(order_qty * float(si["unit_price_eur"]), 2), "unit_price_eur": float(si["unit_price_eur"]),
                            # POLICY POL-PROC-001: an unapproved supplier is never feasible.
                            "covers_need": True, "feasible": bool(si["approved"]),
                            # List concatenation builds the reasons from two optional parts.
                            "reasons": ([] if si["approved"] else ["supplier is not approved (procurement policy POL-PROC-001)"])
                            + ([] if arrival <= need else [f"arrives {arrival.isoformat()}, after the need date {need.isoformat()}"])})
        return options

    # ===== FUNCTION: Service.material_readiness() =====
    # ID: F0325 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:160-229
    # ROLE: POST /api/v1/optimizer/material-readiness — can this production run? BOM explosion, usable stock, PO netting,
    #       shortages, ranked supply options, partial production, alternatives and proposed actions; stored as a CALC.
    # INPUTS:
    #   p: Principal; req: dict {"production_order_id"} or {"sku", "quantity", "need_date", optional "plant"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "material_readiness") with status "ready" | "short".
    # EXAMPLE: {"production_order_id": "PRD-1001"} -> status "short", PUMP-DISP-24 missing 20,000 EA (planted scenario 1).
    # CALLED BY:
    #   <- F0126 create_app.material_readiness() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0302 calculate_bom_requirements() (calls)
    #   -> F0293 BusinessRuleError (references)
    #   -> F0297 calculate_usable_stock() (calls)
    #   -> F0316 Service._batches() (calls)
    #   -> F0303 calculate_material_shortage() (calls)
    #   -> F0324 Service._supplier_options() (calls)
    #   -> F0307 compare_supply_options() (calls)
    #   -> F0314 Service._save_run() (calls)
    def material_readiness(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of = snap["as_of"]
        if req.get("production_order_id"):
            # Order path: SKU, quantity, plant and date come from SAP — not from the caller.
            po = self.db.one("select * from production_orders where tenant_id=? and order_id=?", (p.tenant_id, req["production_order_id"]))
            if po is None:
                raise HTTPException(status_code=404, detail=f"production order {req['production_order_id']} not found")
            sku, qty, plant, need = po["sku"], float(po["quantity"]), po["plant"], date.fromisoformat(po["start_date"])
        else:
            # Planning path (double check of the Pydantic rule, for direct callers such as tests).
            if not (req.get("sku") and req.get("quantity") and req.get("need_date")):
                raise HTTPException(status_code=422, detail="give production_order_id, or sku + quantity + need_date")
            sku, qty, plant, need = req["sku"], float(req["quantity"]), req.get("plant") or "FAC-1", date.fromisoformat(str(req["need_date"]))
            po = None
        bom_rows = self.db.query("select * from bom_components where tenant_id=? and sku=?", (p.tenant_id, sku))
        uoms = {m["material_id"]: m["uom"] for m in self.db.query("select material_id, uom from materials where tenant_id=?", (p.tenant_id,))}
        try:
            req_lines = bz.calculate_bom_requirements(bom_rows, qty, need, uoms)
        # `raise ... from exc` keeps the original exception as the cause (useful in logs).
        except bz.BusinessRuleError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        lines, short = [], []
        # One line per BOM component.
        for line in req_lines["lines"]:
            m = line["material_id"]
            # Usable stock of the component AT THE PLANT.
            stock = bz.calculate_usable_stock(self._batches(p.tenant_id, m, plant), as_of)
            pos = self.db.query("select * from purchase_orders where tenant_id=? and material_id=? and plant=? and status in ('open','confirmed')", (p.tenant_id, m, plant))
            shortage = bz.calculate_material_shortage(line["required_quantity"], stock["usable"], pos, need, line["uom"])
            # Merge the BOM line, stock and selected shortage keys; `**{k: shortage[k] for k in (...)}` picks a subset of keys.
            entry = {**line, "usable": stock["usable"], "excluded_stock": stock["excluded"], **{k: shortage[k] for k in
                     ("confirmed_timely_inbound", "missing", "status", "timely_purchase_orders", "late_purchase_orders", "unconfirmed_purchase_orders")},
                     # Lineage: which SAP batches and POs produced these numbers (stripped by the Flowise tools to save context).
                     "required_date": need.isoformat(), "source_records": {"batches": [b["batch_id"] for b in stock["used_batches"]],
                                                                          "purchase_orders": [x["po_id"] for x in pos]}}
            if shortage["missing"] > 0:
                # Options: approved/unapproved suppliers ...
                options = self._supplier_options(p.tenant_id, m, shortage["missing"], need, as_of)
                # ... plus "expedite" each late PO, marked infeasible: a new date needs written supplier confirmation.
                for late in shortage["late_purchase_orders"]:
                    options.append({"option": f"expedite {late['po_id']}", "supplier_id": late["supplier_id"], "quantity": late["quantity"],
                                    "arrival_date": late["promised_date"], "in_time": False, "covers_need": late["quantity"] >= shortage["missing"],
                                    "cost_eur": None, "feasible": False, "lead_days": None,
                                    "reasons": [f"currently promised {late['promised_date']}; a new date needs written supplier confirmation (no date is assumed)"]})
                entry["supply_options"] = bz.compare_supply_options(options)
                short.append(entry)
            lines.append(entry)
        # Partial production: the most units the short materials allow with usable + timely inbound stock.
        producible = qty
        for e in lines:
            if e["missing"] > 0:
                per_unit = e["qty_per_unit"] * (1 + e["scrap_pct"] / 100)
                # `//` = floor division (whole units only). Guard against per_unit == 0.
                producible = min(producible, float((e["usable"] + e["confirmed_timely_inbound"]) // per_unit) if per_unit else producible)
        actions, alternatives = [], []
        for e in short:
            # Best FEASIBLE supplier option (ranking already applied); expedite options have feasible=False.
            approved = [o for o in e["supply_options"] if o.get("feasible") and o.get("supplier_id")]
            best = approved[0] if approved else None
            if best:  # still needed even when late: the missing quantity must be bought
                actions.append({"action": "purchase_request", "material_id": e["material_id"], "supplier_id": best["supplier_id"], "quantity": best["quantity"],
                                "uom": e["uom"], "expected_arrival": best["arrival_date"], "arrives_in_time": best["in_time"], "cost_eur": best["cost_eur"],
                                "lead_days": best["lead_days"], "lead_time_basis": best["lead_time_basis"]})
            else:
                actions.append({"action": "source_new_supplier", "material_id": e["material_id"], "quantity": e["missing"], "uom": e["uom"],
                                "note": "no approved supplier in the SAP master data"})
        if short:
            # all(...) over a generator: True when NO purchase arrives in time.
            late_all = all(not a.get("arrives_in_time") for a in actions)
            # Earliest date ALL short materials are available = the latest expected arrival; default=None if there is none.
            earliest = max((a["expected_arrival"] for a in actions if a.get("expected_arrival")), default=None)
            alternatives = [{"option": "partial production", "quantity": int(producible), "on": need.isoformat(),
                             "remaining": int(qty - producible), "remaining_after": earliest},
                            {"option": "move production start", "earliest_full_start": earliest,
                             "note": "earliest date all short materials are expected from approved suppliers"}]
            if late_all:
                actions.append({"action": "replan_production", "production_order_id": po["order_id"] if po else None, "produce_now": int(producible),
                                "earliest_full_start": earliest, "note": "no approved supply arrives before the need date"})
        result = {"sku": sku, "production_order_id": po["order_id"] if po else None, "plant": plant, "quantity": qty, "need_date": need.isoformat(),
                  "bom_version": req_lines["bom_version"], "status": "short" if short else "ready", "lines": lines,
                  "shortages": [{"material_id": e["material_id"], "missing": e["missing"], "uom": e["uom"], "required_date": e["required_date"]} for e in short],
                  "partial_production_possible": int(producible), "alternatives": alternatives, "proposed_actions": actions}
        return self._save_run(p, "material_readiness", req, result, snap)

    # ------------------------------------------------------------------ warehouse balancing / quality
    # ===== FUNCTION: Service._sites() =====
    # ID: F0326 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:232-238
    # ROLE: For each warehouse: its row, the SKU's batches there, local usable stock and daily demand.
    # INPUTS:
    #   tenant: str, sku: str, as_of: date.
    # OUTPUT:
    #   dict -> {wh_code: {"warehouse", "batches", "local", "demand"}}.
    # CALLED BY:
    #   <- F0327 Service.warehouse_balancing() (calls)
    # CALLS:
    #   -> F0421 Database.query() (calls)
    #   -> F0316 Service._batches() (calls)
    #   -> F0297 calculate_usable_stock() (calls)
    #   -> F0317 Service._demand() (calls)
    def _sites(self, tenant: str, sku: str, as_of: date) -> dict:
        sites = {}
        # Only kind='warehouse' rows (the factory FAC-1 is not a balancing site).
        for wh in self.db.query("select * from warehouses where tenant_id=? and kind='warehouse'", (tenant,)):
            batches = self._batches(tenant, sku, wh["code"])
            local = bz.calculate_usable_stock(batches, as_of)
            sites[wh["code"]] = {"warehouse": wh, "batches": batches, "local": local, "demand": self._demand(tenant, sku, wh["code"], as_of)}
        return sites

    # ===== FUNCTION: Service.warehouse_balancing() =====
    # ID: F0327 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:240-289
    # ROLE: POST /api/v1/optimizer/warehouse-balancing — cover per warehouse, receiver (given or lowest cover), transfer options
    #       from each donor (shelf life on arrival enforced), allocation from production orders, ranking, proposed stock transfer.
    # INPUTS:
    #   p: Principal; req: dict {"sku", optional "target_warehouse"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "warehouse_balancing"): positions, options, status, proposed_actions.
    # EXAMPLE: {"sku": "SUN-SPF50-100"} -> receiver WH-B (~6 days cover); donors WH-C / WH-A evaluated with lane cost and lead time.
    # CALLED BY:
    #   <- F0127 create_app.warehouse_balancing() (calls)
    #   <- F0328 Service.replenishment() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0318 Service._require_item() (calls)
    #   -> F0326 Service._sites() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0299 calculate_days_of_cover() (calls)
    #   -> F0297 calculate_usable_stock() (calls)
    #   -> F0304 Site (calls)
    #   -> F0300 calculate_replenishment_quantity() (calls)
    #   -> F0305 generate_transfer_candidates() (calls)
    #   -> F0306 evaluate_transfer_feasibility() (calls)
    #   -> F0307 compare_supply_options() (calls)
    def warehouse_balancing(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of, sku = snap["as_of"], req["sku"]
        kind, uom = self._require_item(p.tenant_id, sku)
        if kind != "product":
            raise HTTPException(status_code=422, detail="warehouse balancing is for finished products")
        sites = self._sites(p.tenant_id, sku, as_of)
        # Lanes keyed by (origin, destination) for O(1) lookup.
        lanes = {(lane["origin"], lane["destination"]): lane for lane in self.db.query("select * from transport_lanes where tenant_id=?", (p.tenant_id,))}
        positions = []
        for code, s in sites.items():
            cover = bz.calculate_days_of_cover(s["local"]["usable"], s["demand"])
            # Projected stock-out = today + whole days of cover (None when demand is 0).
            stockout = as_of + timedelta(days=int(cover)) if cover is not None else None
            positions.append({"warehouse": code, "name": s["warehouse"]["name"], "usable": s["local"]["usable"], "daily_demand": s["demand"],
                              "days_of_cover": cover, "projected_stockout": stockout.isoformat() if stockout else None,
                              "target_cover_days": s["warehouse"]["target_cover_days"], "excluded_stock": s["local"]["excluded"], "near_expiry": s["local"]["near_expiry"]})
        # Receiver: requested warehouse, else the one with the LOWEST cover (min over a generator with key=...).
        target = req.get("target_warehouse") or min((x for x in positions if x["days_of_cover"] is not None), key=lambda x: x["days_of_cover"])["warehouse"]
        if target not in sites:
            raise HTTPException(status_code=404, detail=f"warehouse {target} not found")
        # next(generator): first (only) position of the receiver.
        tpos = next(x for x in positions if x["warehouse"] == target)
        options = []
        for donor_code, s in sites.items():
            if donor_code == target:
                continue
            lane = lanes.get((donor_code, target))
            arrival = as_of + timedelta(days=int(lane["lead_days"])) if lane else None
            # Transferable stock = usable AND still >= 60 days shelf life on arrival.
            movable = bz.calculate_usable_stock(s["batches"], as_of, transfer_arrival=arrival) if arrival else {"usable": 0.0, "excluded": []}
            site = bz.Site(donor_code, movable["usable"], s["local"]["usable"], s["demand"], s["warehouse"]["target_cover_days"])
            lead = int(lane["lead_days"]) if lane else 0
            # Receiver need = demand x (target cover + lane lead time) - usable.
            need = bz.calculate_replenishment_quantity(tpos["daily_demand"], tpos["usable"], sites[target]["warehouse"]["target_cover_days"], lead, uom)
            # Evaluate this single donor (the receiver is passed as an empty Site so it is skipped).
            cands = bz.generate_transfer_candidates(target, {donor_code: site, target: bz.Site(target, 0, 0, 0, 0)})
            cand = cands[0] if cands else {"donor": donor_code, "surplus": 0.0, "donor_keeps_days": site.target_cover_days}
            ev = bz.evaluate_transfer_feasibility(cand, need, lane, as_of, date.fromisoformat(tpos["projected_stockout"]) if tpos["projected_stockout"] else None)
            # dict.update adds explanatory keys, incl. the batches that may NOT move and why.
            ev.update({"option": f"transfer from {donor_code}", "need": need, "not_transferable": movable["excluded"]})
            options.append(ev)
        # Alternative: allocate output of planned/released production orders of the SKU.
        prod = self.db.query("select * from production_orders where tenant_id=? and sku=? and status in ('planned','released') order by due_date", (p.tenant_id, sku))
        for o in prod:
            lane = lanes.get((o["plant"], target))
            if lane:
                arrival = date.fromisoformat(o["due_date"]) + timedelta(days=int(lane["lead_days"]))
                in_time = tpos["projected_stockout"] is None or arrival <= date.fromisoformat(tpos["projected_stockout"])
                options.append({"option": f"allocate from production order {o['order_id']}", "quantity": float(o["quantity"]), "arrival_date": arrival.isoformat(),
                                "in_time": in_time, "covers_need": True, "feasible": in_time, "cost_eur": None, "lead_days": (arrival - as_of).days,
                                "reasons": ([] if in_time else [f"output lands {arrival.isoformat()}, after the stock-out"]) + ["production cost not in SAP extract (not estimated)"]})
        ranked = bz.compare_supply_options(options)
        # The top option is used only when it is feasible.
        best = ranked[0] if ranked and ranked[0].get("feasible") else None
        result = {"sku": sku, "target_warehouse": target, "positions": positions, "options": ranked,
                  "status": "transfer_recommended" if best and best.get("donor") else "no_feasible_transfer" if not best else "other_option",
                  # A proposed stock_transfer only when the best option is a donor transfer.
                  "proposed_actions": ([{"action": "stock_transfer", "sku": sku, "from": best["donor"], "to": target, "quantity": best["quantity"], "uom": uom,
                                         "lane_id": best["lane_id"], "arrival_date": best["arrival_date"], "cost_eur": best["cost_eur"]}] if best and best.get("donor") else [])}
        return self._save_run(p, "warehouse_balancing", req, result, snap)

    # ===== FUNCTION: Service.replenishment() =====
    # ID: F0328 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:291-310
    # ROLE: POST /api/v1/optimizer/replenishment — product -> warehouse_balancing; material -> ranked approved supplier options + purchase request.
    # INPUTS:
    #   p: Principal; req: dict {"item_id", optional "location", "quantity", "need_date"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "replenishment", or the balancing result for products).
    # CALLED BY:
    #   <- F0128 create_app.replenishment() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0318 Service._require_item() (calls)
    #   -> F0327 Service.warehouse_balancing() (calls)
    #   -> F0297 calculate_usable_stock() (calls)
    #   -> F0316 Service._batches() (calls)
    #   -> F0307 compare_supply_options() (calls)
    #   -> F0324 Service._supplier_options() (calls)
    #   -> F0314 Service._save_run() (calls)
    def replenishment(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        kind, uom = self._require_item(p.tenant_id, req["item_id"])
        if kind == "product":
            # Delegation: finished goods are replenished by moving stock between warehouses.
            res = self.warehouse_balancing(p, {"sku": req["item_id"], "target_warehouse": req.get("location")})
            return res
        as_of = snap["as_of"]
        location = req.get("location") or "FAC-1"
        # Default need date: two weeks after the business date.
        need_date = date.fromisoformat(str(req["need_date"])) if req.get("need_date") else as_of + timedelta(days=14)
        usable = bz.calculate_usable_stock(self._batches(p.tenant_id, req["item_id"], location), as_of)["usable"]
        qty = float(req.get("quantity") or 0)
        # Never invent a purchase quantity: it must be given.
        if qty <= 0:
            raise HTTPException(status_code=422, detail="quantity must be positive for material replenishment")
        options = bz.compare_supply_options(self._supplier_options(p.tenant_id, req["item_id"], qty, need_date, as_of))
        result = {"item_id": req["item_id"], "location": location, "usable": usable, "quantity": qty, "need_date": need_date.isoformat(), "options": options,
                  # Propose a purchase request from the top option only if it is feasible (approved supplier).
                  "proposed_actions": [{"action": "purchase_request", "material_id": req["item_id"], "quantity": options[0]["quantity"], "uom": uom,
                                        "supplier_id": options[0]["supplier_id"], "arrival_date": options[0]["arrival_date"], "cost_eur": options[0]["cost_eur"],
                                        "lead_days": options[0]["lead_days"], "lead_time_basis": options[0].get("lead_time_basis")}]
                  if options and options[0].get("feasible") else []}
        return self._save_run(p, "replenishment", req, result, snap)

    # ===== FUNCTION: Service.quality_check() =====
    # ID: F0329 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:312-323
    # ROLE: POST /api/v1/quality/check-stock — usable vs excluded batches, near expiry, expiry risks, FEFO order;
    #       proposes a destruction review for released batches that are already expired.
    # INPUTS:
    #   p: Principal; req: dict {"item_id", optional "location", "horizon_days"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "quality_check").
    # CALLED BY:
    #   <- F0131 create_app.quality_check() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0318 Service._require_item() (calls)
    #   -> F0316 Service._batches() (calls)
    #   -> F0297 calculate_usable_stock() (calls)
    #   -> F0301 detect_expiry_risk() (calls)
    #   -> F0314 Service._save_run() (calls)
    def quality_check(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        # 404 when the item is unknown (return value not needed).
        self._require_item(p.tenant_id, req["item_id"])
        batches = self._batches(p.tenant_id, req["item_id"], req.get("location"))
        stock = bz.calculate_usable_stock(batches, snap["as_of"])
        risks = bz.detect_expiry_risk(batches, snap["as_of"], int(req.get("horizon_days") or 90))
        result = {"item_id": req["item_id"], "location": req.get("location"), "on_hand": sum(float(b["quantity"]) for b in batches),
                  "usable": stock["usable"], "excluded": stock["excluded"], "near_expiry": stock["near_expiry"], "expiry_risks": risks,
                  "fefo_order": stock["used_batches"], "proposed_actions": [
                      {"action": "block_for_destruction_review", "batch_id": r["batch_id"], "quantity": r["quantity"]} for r in risks if r["risk"] == "expired" and r["status"] == "released"],
                  "note": "Business-rule validation only; quality usage decisions remain with the quality manager in SAP."}
        return self._save_run(p, "quality_check", req, result, snap)

    # ------------------------------------------------------------------ forecasting
    # ===== FUNCTION: Service.forecast_demand() =====
    # ID: F0330 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:326-349
    # ROLE: POST /api/v1/forecast/demand — baseline forecast (28-day mean x weekday index) with a 14-day back-test vs a naive
    #       same-weekday forecast (WAPE %).
    # INPUTS:
    #   p: Principal; req: dict {"sku", "warehouse", "horizon_days"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "demand_forecast"): forecast [{date, units}], total, backtest {holdout_days, wape_pct, naive_same_weekday_wape_pct}.
    # CALLED BY:
    #   <- F0129 create_app.forecast_demand() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0331 Service.forecast_demand.predict() (calls)
    #   -> F0314 Service._save_run() (calls)
    def forecast_demand(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of, sku, wh, horizon = snap["as_of"], req["sku"], req["warehouse"], int(req.get("horizon_days") or 14)
        # Sales history as {date: units}.
        rows = {date.fromisoformat(r["day"]): float(r["quantity"]) for r in self.db.query("select day, quantity from sales_history where tenant_id=? and sku=? and warehouse=?", (p.tenant_id, sku, wh))}
        if not rows:
            raise HTTPException(status_code=404, detail=f"no sales history for {sku} at {wh}")

        # ===== FUNCTION: Service.forecast_demand.predict() =====
        # ID: F0331 · nested · used
        # ORIGINAL FILE: backend/scinsight/service.py:333-338
        # ROLE: Baseline prediction for one day using only data BEFORE the cutoff (no look-ahead).
        # INPUTS:
        #   day: date -> the day to predict; cutoff: date -> last known day + 1.
        # OUTPUT:
        #   float -> mean of the last 28 days x (same-weekday mean over 56 days / overall mean), 1 decimal.
        # CALLED BY:
        #   <- F0330 Service.forecast_demand() (calls)
        # CALLS:
        #   (none found)
        def predict(day: date, cutoff: date) -> float:  # baseline: 28-day mean x weekday index (from the 56 days before cutoff)
            window = [rows.get(cutoff - timedelta(days=i), 0.0) for i in range(1, 29)]
            # `/ 28 or 0.0`: a mean of 0 stays 0.0.
            mean = sum(window) / 28 or 0.0
            same = [rows.get(cutoff - timedelta(days=i), 0.0) for i in range(1, 57) if (cutoff - timedelta(days=i)).weekday() == day.weekday()]
            # Weekday index (e.g. Fridays sell 8% more) — 1.0 when it cannot be computed.
            idx = (sum(same) / len(same)) / mean if mean and same else 1.0
            return round(mean * idx, 1)
        # Back-test: the last 14 known days, predicted as if we were 14 days ago.
        holdout = [as_of - timedelta(days=i) for i in range(14, 0, -1)]
        cutoff = as_of - timedelta(days=14)
        actual = [rows.get(d, 0.0) for d in holdout]
        pred = [predict(d, cutoff) for d in holdout]
        # Naive benchmark: same weekday one week earlier.
        naive = [rows.get(d - timedelta(days=7), 0.0) for d in holdout]
        # WAPE = 100 x sum|actual - forecast| / sum(actual). zip(strict=True) raises if the lists differ in length.
        wape = lambda f: round(100 * sum(abs(a - b) for a, b in zip(actual, f, strict=True)) / (sum(actual) or 1), 2)  # noqa: E731
        forecast = [{"date": (as_of + timedelta(days=i)).isoformat(), "units": predict(as_of + timedelta(days=i), as_of)} for i in range(horizon)]
        result = {"sku": sku, "warehouse": wh, "method": "baseline: 28-day mean x weekday index", "model_version": "demand-baseline-v1",
                  "forecast": forecast, "total": round(sum(f["units"] for f in forecast), 1),
                  "backtest": {"holdout_days": 14, "wape_pct": wape(pred), "naive_same_weekday_wape_pct": wape(naive)}, "proposed_actions": []}
        return self._save_run(p, "demand_forecast", req, result, snap)

    # ===== FUNCTION: Service.lead_time() =====
    # ID: F0332 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:351-371
    # ROLE: POST /api/v1/forecast/lead-time — empirical lead time of a supplier (optionally per material); when a promoted ML model
    #       exists AND a quantity is given, its prediction is used instead.
    # INPUTS:
    #   p: Principal; req: dict {"supplier_id", optional "material_id", "quantity"}.
    # OUTPUT:
    #   dict -> stored calculation (kind "lead_time_estimate"): estimate, predicted_lead_time_days, model_version, basis.
    # CALLED BY:
    #   <- F0130 create_app.forecast_lead_time() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0308 estimate_supplier_lead_time() (calls)
    #   -> F0536 predict_lead_time() (calls)
    #   -> F0314 Service._save_run() (calls)
    def lead_time(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        sup = self.db.one("select * from suppliers where tenant_id=? and supplier_id=?", (p.tenant_id, req["supplier_id"]))
        if sup is None:
            raise HTTPException(status_code=404, detail=f"supplier {req['supplier_id']} not found")
        material = req.get("material_id")
        # The SQL and its parameter tuple are both chosen by the same condition (with or without the material filter).
        item = self.db.one("select * from supplier_items where tenant_id=? and supplier_id=?" + (" and material_id=?" if material else ""),
                           (p.tenant_id, req["supplier_id"], material) if material else (p.tenant_id, req["supplier_id"]))
        receipts = self.db.query("select * from purchase_orders where tenant_id=? and supplier_id=? and received_date is not null" + (" and material_id=?" if material else ""),
                                 (p.tenant_id, req["supplier_id"], material) if material else (p.tenant_id, req["supplier_id"]))
        est = bz.estimate_supplier_lead_time(receipts, item["contract_lead_time_days"] if item else None)
        promoted = self.db.one("select * from model_versions where tenant_id=? and model_name='supplier_lead_time' and status='promoted' order by promoted_at desc limit 1", (p.tenant_id,))
        model_pred = None
        if promoted and req.get("quantity"):
            # Local import: scikit-learn is loaded only when a promoted model is actually used.
            from backend.scinsight.learning import predict_lead_time
            model_pred = predict_lead_time(self.db, p.tenant_id, promoted, req["supplier_id"], float(req["quantity"]), snap["as_of"])
        predicted = model_pred if model_pred is not None else est["estimate_days"]
        result = {"supplier_id": req["supplier_id"], "supplier": sup["name"], "material_id": material, "estimate": est,
                  "predicted_lead_time_days": predicted, "model_version": promoted["version"] if (promoted and model_pred is not None) else "lead-time-empirical-v1",
                  "basis": "promoted ML model" if model_pred is not None else est["basis"], "proposed_actions": []}
        return self._save_run(p, "lead_time_estimate", req, result, snap)

    # ------------------------------------------------------------------ decisions + human review
    # ===== FUNCTION: Service.create_decision() =====
    # ID: F0333 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:374-398
    # ROLE: POST /api/v1/decisions — create a recommendation (pending_review) FROM a stored calculation. Quantities are copied
    #       from the calculation; idempotent per key; a purchase request's lead time becomes a prediction to verify later.
    # INPUTS:
    #   p: Principal; req: dict {"calculation_id", optional "title", "idempotency_key", "po_id"}.
    # OUTPUT:
    #   dict -> the recommendation (get_decision view), or the existing one + {"idempotent_replay": True}.
    # CALLED BY:
    #   <- F0135 create_app.create_decision() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0315 Service.calculation() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0334 Service._rec() (calls)
    #   -> F0423 Database.execute() (calls)
    #   -> F0416 now_iso() (calls)
    #   -> F0779 Security.audit() (calls)
    #   -> F0335 Service.get_decision() (calls)
    def create_decision(self, p: Principal, req: dict) -> dict:
        calc = self.calculation(p, req["calculation_id"])
        actions = calc.get("proposed_actions") or []
        # Nothing to approve -> 422 (allow_no_action is not exposed by the API schema).
        if not actions and not req.get("allow_no_action"):
            raise HTTPException(status_code=422, detail="the calculation proposes no action; nothing to review")
        key = req.get("idempotency_key") or calc["calculation_id"]
        existing = self.db.one("select * from recommendations where tenant_id=? and idempotency_key=?", (p.tenant_id, key))
        if existing:
            # `|` on dicts (Python 3.9+) merges: a retried Flowise call returns the same recommendation instead of a duplicate.
            return self._rec(existing) | {"idempotent_replay": True}
        rec_id = f"REC-{uuid.uuid4().hex[:10].upper()}"
        prediction = None
        # First purchase request with a lead time (next(..., None) = None when there is none).
        purchase = next((a for a in actions if a.get("action") == "purchase_request" and a.get("lead_days") is not None), None)
        if purchase:  # the lead time behind the purchase request is a prediction that the goods receipt later verifies
            prediction = {"metric": "lead_time_days", "predicted": purchase["lead_days"], "supplier_id": purchase["supplier_id"],
                          "material_id": purchase["material_id"], "basis": purchase.get("lead_time_basis"), "po_id": req.get("po_id")}
        # A material replenishment with a purchase is a procurement decision; otherwise use DOMAIN_OF.
        domain = "procurement" if calc["kind"] == "replenishment" and purchase else DOMAIN_OF.get(calc["kind"], "inventory")
        title = req.get("title") or f"{calc['kind'].replace('_', ' ')} — {len(actions)} proposed action(s)"
        # Risk: high when the plan is short or the best option is late; otherwise medium.
        risk = "high" if calc.get("status") in ("short",) or any(o.get("in_time") is False for o in calc.get("options", [])[:1]) else "medium"
        self.db.execute("insert into recommendations(id,tenant_id,calculation_id,domain,title,proposed_actions,evidence,prediction,risk_level,status,idempotency_key,"
                        "model_version,created_by,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (rec_id, p.tenant_id, calc["calculation_id"], domain, title[:300], json.dumps(actions, default=str),
                         json.dumps({"calculation_id": calc["calculation_id"], "provenance": calc["provenance"]}), json.dumps(prediction) if prediction else None,
                         risk, "pending_review", key, calc.get("model_version"), p.user_id, now_iso(), now_iso()))
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.created", {"recommendation_id": rec_id, "calculation_id": calc["calculation_id"]})
        return self.get_decision(p, rec_id)

    # ===== FUNCTION: Service._rec() =====
    # ID: F0334 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:400-404
    # ROLE: Turn a recommendations row into the API shape (JSON columns parsed, who may review it).
    # INPUTS:
    #   row: dict -> recommendations row.
    # OUTPUT:
    #   dict -> row with proposed_actions/evidence/prediction parsed and review_authority (sorted role list).
    # CALLED BY:
    #   <- F0333 Service.create_decision() (calls)
    #   <- F0335 Service.get_decision() (calls)
    #   <- F0336 Service.list_decisions() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _rec(row: dict) -> dict:
        return {**row, "proposed_actions": json.loads(row["proposed_actions"]), "evidence": json.loads(row["evidence"]),
                "prediction": json.loads(row["prediction"]) if row.get("prediction") else None,
                "review_authority": sorted(REVIEW_AUTHORITY.get(row["domain"], set()))}

    # ===== FUNCTION: Service.get_decision() =====
    # ID: F0335 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:406-416
    # ROLE: GET /api/v1/decisions/{id} — recommendation + human reviews + SAP execution refs + observed outcomes + verified_review.
    # INPUTS:
    #   p: Principal, rec_id: str.
    # OUTPUT:
    #   dict -> full recommendation view (404 when unknown for this tenant).
    # CALLED BY:
    #   <- F0137 create_app.get_decision() (calls)
    #   <- F0333 Service.create_decision() (calls)
    #   <- F0337 Service.review() (calls)
    #   <- F0339 Service.withdraw() (calls)
    #   <- F0340 Service.record_sap_execution() (calls)
    #   <- F0341 Service.reconcile() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0422 Database.one() (calls)
    #   -> F0334 Service._rec() (calls)
    #   -> F0421 Database.query() (calls)
    def get_decision(self, p: Principal, rec_id: str) -> dict:
        row = self.db.one("select * from recommendations where id=? and tenant_id=?", (rec_id, p.tenant_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"recommendation {rec_id} not found for this tenant")
        out = self._rec(row)
        out["reviews"] = [{**r, "reviewer_roles": json.loads(r["reviewer_roles"]), "modifications": json.loads(r["modifications"]) if r["modifications"] else None}
                          for r in self.db.query("select * from human_decisions where recommendation_id=? and tenant_id=? order by created_at", (rec_id, p.tenant_id))]
        out["sap_execution"] = self.db.query("select * from sap_execution_refs where recommendation_id=? and tenant_id=?", (rec_id, p.tenant_id))
        out["outcomes"] = self.db.query("select * from observed_outcomes where recommendation_id=? and tenant_id=?", (rec_id, p.tenant_id))
        # Flowise "Show the verified decision" relies on this flag: a decided status AND at least one recorded human review.
        out["verified_review"] = out["status"] in ("approved", "rejected", "modified", "deferred", "executed") and bool(out["reviews"])
        return out

    # ===== FUNCTION: Service.list_decisions() =====
    # ID: F0336 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:418-421
    # ROLE: GET /api/v1/decisions — recommendations of the tenant, newest first, optionally by status.
    # INPUTS:
    #   p: Principal, status: str | None.
    # OUTPUT:
    #   list[dict] -> _rec() views.
    # CALLED BY:
    #   <- F0136 create_app.list_decisions() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0421 Database.query() (calls)
    #   -> F0334 Service._rec() (calls)
    def list_decisions(self, p: Principal, status: str | None) -> list[dict]:
        rows = self.db.query("select * from recommendations where tenant_id=?" + (" and status=?" if status else "") + " order by created_at desc",
                             (p.tenant_id, status) if status else (p.tenant_id,))
        return [self._rec(r) for r in rows]

    # ===== FUNCTION: Service.review() =====
    # ID: F0337 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:423-442
    # ROLE: POST /api/v1/decisions/{id}/review — THE human approval. Checks reviewer authority, then atomically changes the status
    #       (only from pending_review / deferred) and stores the human decision; audited. Nothing is written to SAP.
    # INPUTS:
    #   p: Principal (the reviewer), rec_id: str, req: dict {"decision", "explanation", optional "modifications"}.
    # OUTPUT:
    #   dict -> updated recommendation + {"sap_written": False, "next_step"}.
    # CALLED BY:
    #   <- F0138 create_app.review() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0335 Service.get_decision() (calls)
    #   -> F0778 Security.require_reviewer() (calls)
    #   -> F0426 Database.atomic() (calls)
    #   -> F0338 Service.review.apply() (references)
    #   -> F0779 Security.audit() (calls)
    def review(self, p: Principal, rec_id: str, req: dict) -> dict:
        rec = self.get_decision(p, rec_id)
        # AUTHORIZATION: human + domain reviewer role (403 otherwise; the agent key always fails here).
        self.security.require_reviewer(p, rec["domain"])
        if req["decision"] == "modify" and not req.get("modifications"):
            raise HTTPException(status_code=422, detail="a 'modify' decision must state the modifications")
        new_status = REVIEW_DECISIONS[req["decision"]]

        # ===== FUNCTION: Service.review.apply() =====
        # ID: F0338 · nested · used
        # ORIGINAL FILE: backend/scinsight/service.py:430-438
        # ROLE: Conditional status change + decision record in one locked transaction (two reviewers cannot both decide).
        # INPUTS:
        #   q -> query function from Database.atomic.
        # OUTPUT:
        #   bool -> True when the recommendation was still reviewable and is now decided.
        # CALLED BY:
        #   <- F0337 Service.review() (references)
        # CALLS:
        #   -> F0416 now_iso() (calls)
        def apply(q):
            # The WHERE on status makes the transition safe: 0 rows changed = already decided by someone else.
            changed = q("update recommendations set status=?, updated_at=? where id=? and tenant_id=? and status in ('pending_review','deferred')",
                        (new_status, now_iso(), rec_id, p.tenant_id))
            if not changed:
                return False
            q("insert into human_decisions(id,tenant_id,recommendation_id,reviewer_id,reviewer_roles,decision,explanation,modifications,created_at) values(?,?,?,?,?,?,?,?,?)",
              (f"HD-{uuid.uuid4().hex[:10].upper()}", p.tenant_id, rec_id, p.user_id, json.dumps(sorted(p.roles)), req["decision"], req["explanation"],
               json.dumps(req.get("modifications")) if req.get("modifications") else None, now_iso()))
            return True
        if not self.db.atomic(apply):
            raise HTTPException(status_code=409, detail=f"recommendation {rec_id} is {rec['status']}; only pending or deferred recommendations can be reviewed")
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), f"decision.{req['decision']}", {"recommendation_id": rec_id})
        return self.get_decision(p, rec_id) | {"sap_written": False, "next_step": "An authorised SAP user executes approved actions in SAP; record it with /sap-execution."}

    # ===== FUNCTION: Service.withdraw() =====
    # ID: F0339 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:444-451
    # ROLE: POST /api/v1/decisions/{id}/withdraw — the creator (or the director) withdraws a PENDING recommendation; kept in the audit trail.
    # INPUTS:
    #   p: Principal, rec_id: str.
    # OUTPUT:
    #   dict -> recommendation with status "withdrawn".
    # CALLED BY:
    #   <- F0139 create_app.withdraw() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0335 Service.get_decision() (calls)
    #   -> F0423 Database.execute() (calls)
    #   -> F0416 now_iso() (calls)
    #   -> F0779 Security.audit() (calls)
    def withdraw(self, p: Principal, rec_id: str) -> dict:
        rec = self.get_decision(p, rec_id)
        if rec["created_by"] != p.user_id and "supply_chain_director" not in p.roles:
            raise HTTPException(status_code=403, detail="only the creator or the director can withdraw a recommendation")
        # execute() returns the rowcount: 0 when the status was not pending_review.
        if not self.db.execute("update recommendations set status='withdrawn', updated_at=? where id=? and tenant_id=? and status='pending_review'", (now_iso(), rec_id, p.tenant_id)):
            raise HTTPException(status_code=409, detail="only a pending recommendation can be withdrawn")
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.withdrawn", {"recommendation_id": rec_id})
        return self.get_decision(p, rec_id)

    # ===== FUNCTION: Service.record_sap_execution() =====
    # ID: F0340 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:453-466
    # ROLE: POST /api/v1/decisions/{id}/sap-execution — record the SAP document created MANUALLY by an authorised SAP user for an
    #       approved recommendation (status -> executed). One SAP document can be linked to only one recommendation.
    # INPUTS:
    #   p: Principal (sap_executor or director), rec_id: str, req: dict {"sap_document", "doc_type", "executed_at"}.
    # OUTPUT:
    #   dict -> recommendation with status "executed".
    # CALLED BY:
    #   <- F0140 create_app.sap_execution() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0335 Service.get_decision() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0425 Database.transaction() (calls)
    #   -> F0416 now_iso() (calls)
    #   -> F0779 Security.audit() (calls)
    def record_sap_execution(self, p: Principal, rec_id: str, req: dict) -> dict:
        self.security.require(p, {"sap_executor", "supply_chain_director"}, "Recording an SAP execution")
        rec = self.get_decision(p, rec_id)
        if rec["status"] not in ("approved", "modified"):
            raise HTTPException(status_code=409, detail="only an approved (or approved-with-changes) recommendation can be marked as executed in SAP")
        linked = self.db.one("select recommendation_id from sap_execution_refs where tenant_id=? and sap_document=?", (p.tenant_id, req["sap_document"]))
        if linked:
            raise HTTPException(status_code=409, detail=f"SAP document {req['sap_document']} is already linked to {linked['recommendation_id']}")
        # Both statements in one transaction: the reference and the status change happen together or not at all.
        self.db.transaction([
            ("insert into sap_execution_refs(id,tenant_id,recommendation_id,sap_document,doc_type,executed_at,recorded_by,source) values(?,?,?,?,?,?,?,?)",
             (f"SX-{uuid.uuid4().hex[:10].upper()}", p.tenant_id, rec_id, req["sap_document"], req["doc_type"], str(req["executed_at"]), p.user_id, "manual_sap_execution_record")),
            ("update recommendations set status='executed', updated_at=? where id=? and tenant_id=?", (now_iso(), rec_id, p.tenant_id))])
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.sap_execution_recorded", {"recommendation_id": rec_id, "sap_document": req["sap_document"]})
        return self.get_decision(p, rec_id)

    # ------------------------------------------------------------------ outcome reconciliation + learning
    # ===== FUNCTION: Service.reconcile() =====
    # ID: F0341 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:469-507
    # ROLE: POST /api/v1/outcomes/reconcile — compare an EXECUTED recommendation's lead-time prediction with its SAP goods receipt;
    #       store the observed outcome + learning record once (idempotent), approved for training only when verified.
    # INPUTS:
    #   p: Principal, rec_id: str.
    # OUTPUT:
    #   dict -> outcome with error, ids, approved_for_training — or unsupported_metric / missing / pending / already_reconciled.
    # EXAMPLE: REC-HIST-0001 -> predicted 5 days, actual 9 (PO-4500020950) -> signed error 4, verified.
    # CALLED BY:
    #   <- F0141 create_app.reconcile() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0335 Service.get_decision() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0310 reconcile_actual_outcome() (calls)
    #   -> F0426 Database.atomic() (calls)
    #   -> F0342 Service.reconcile.write() (references)
    #   -> F0779 Security.audit() (calls)
    def reconcile(self, p: Principal, rec_id: str) -> dict:
        self.security.require(p, {"agent_service", "planner", "supply_chain_director", "mlops_engineer"}, "Outcome reconciliation")
        rec = self.get_decision(p, rec_id)
        if rec["status"] != "executed":
            raise HTTPException(status_code=409, detail="only an executed recommendation (with a recorded SAP execution) can be reconciled")
        pred = rec["prediction"]
        if not pred or pred.get("metric") != "lead_time_days":
            return {"recommendation_id": rec_id, "status": "unsupported_metric",
                    "reason": "Phase 1 reconciles supplier lead-time predictions; other outcome types need their SAP result feed."}
        # The PO to check: from the prediction, else the first purchase-order execution record.
        po_id = pred.get("po_id") or next((x["sap_document"] for x in rec["sap_execution"] if x["doc_type"] == "purchase_order"), None)
        po = self.db.one("select * from purchase_orders where tenant_id=? and po_id=?", (p.tenant_id, po_id)) if po_id else None
        outcome = bz.reconcile_actual_outcome(pred, po)
        if outcome["status"] in ("missing", "pending"):
            return {"recommendation_id": rec_id, **outcome}
        # Last human decision on the recommendation (feature of the learning record).
        human = rec["reviews"][-1]["decision"] if rec["reviews"] else "none"
        out_id, lr_id = f"OUT-{uuid.uuid4().hex[:10].upper()}", f"LR-{uuid.uuid4().hex[:10].upper()}"
        verified = outcome["status"] == "verified"
        label = {"metric": "lead_time_days", "actual": outcome["actual"]}
        features = {"supplier_id": po["supplier_id"], "material_id": po["material_id"], "quantity": po["quantity"], "order_date": po["order_date"]}

        # ===== FUNCTION: Service.reconcile.write() =====
        # ID: F0342 · nested · used
        # ORIGINAL FILE: backend/scinsight/service.py:489-499
        # ROLE: Insert outcome + learning record once (check-then-insert under the atomic lock).
        # INPUTS:
        #   q -> query function from Database.atomic.
        # OUTPUT:
        #   bool -> False when a v1 learning record already exists.
        # CALLED BY:
        #   <- F0341 Service.reconcile() (references)
        # CALLS:
        #   -> F0416 now_iso() (calls)
        def write(q):
            if q("select id from learning_records where tenant_id=? and recommendation_id=? and label_version='v1'", (p.tenant_id, rec_id)):
                return False
            q("insert into observed_outcomes(id,tenant_id,recommendation_id,source_document,metric,predicted,actual,unit,observed_at,complete,quality_flags) values(?,?,?,?,?,?,?,?,?,?,?)",
              (out_id, p.tenant_id, rec_id, outcome["source_document"], "lead_time_days", outcome["error"]["predicted"], outcome["actual"], "days",
               outcome["received_date"], int(verified), json.dumps(outcome["quality_flags"])))
            # approved_for_training = int(verified): an incomplete (partial delivery) outcome never trains a model.
            q("insert into learning_records(id,tenant_id,recommendation_id,outcome_id,features,label,signed_error,abs_error,human_decision,outcome_status,"
              "model_version,label_version,approved_for_training,created_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (lr_id, p.tenant_id, rec_id, out_id, json.dumps(features), json.dumps(label), outcome["error"]["signed_error"], outcome["error"]["absolute_error"],
               human, outcome["status"], rec.get("model_version"), "v1", int(verified), now_iso()))
            return True
        created = self.db.atomic(write)
        if not created:
            existing = self.db.one("select * from learning_records where tenant_id=? and recommendation_id=? and label_version='v1'", (p.tenant_id, rec_id))
            return {"recommendation_id": rec_id, "status": "already_reconciled", "learning_record": existing}
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "outcome.reconciled", {"recommendation_id": rec_id, "status": outcome["status"]})
        return {"recommendation_id": rec_id, "outcome_id": out_id, "learning_record_id": lr_id, **outcome, "human_decision": human,
                "model_version": rec.get("model_version"), "approved_for_training": verified,
                "note": "One outcome is evidence, not proof of model improvement; retraining needs enough verified records and a manual promotion gate."}

    # ===== FUNCTION: Service.learning_metrics() =====
    # ID: F0343 · method · used
    # ORIGINAL FILE: backend/scinsight/service.py:509-529
    # ROLE: GET /api/v1/learning/metrics — metrics computed only from verified outcomes and recorded decisions; unavailable metrics
    #       return value None with a reason (never an invented number).
    # INPUTS:
    #   p: Principal.
    # OUTPUT:
    #   dict -> verified_outcome_coverage, supplier_lead_time_mae_days, demand_forecast_wape_pct, acceptance / modification /
    #           execution rates, stockout_warning_accuracy, business_impact_eur, models, learning_records.
    # CALLED BY:
    #   <- F0142 create_app.learning_metrics() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0421 Database.query() (calls)
    def learning_metrics(self, p: Principal) -> dict:
        t = p.tenant_id
        executed = self.db.query("select id from recommendations where tenant_id=? and status='executed'", (t,))
        lr = self.db.query("select * from learning_records where tenant_id=?", (t,))
        verified = [r for r in lr if r["outcome_status"] == "verified"]
        decisions = self.db.query("select decision from human_decisions where tenant_id=?", (t,))
        approved = self.db.query("select id from recommendations where tenant_id=? and status in ('approved','modified','executed')", (t,))
        forecasts = [json.loads(r["result"]) for r in self.db.query("select result from agent_runs where tenant_id=? and kind='demand_forecast'", (t,))]
        # `or None`: 0 decisions -> None, so rates become None instead of dividing by zero.
        n_dec = len(decisions) or None
        return {
            "verified_outcome_coverage": {"value": round(len(verified) / len(executed), 3) if executed else None, "verified": len(verified), "executed": len(executed)},
            "supplier_lead_time_mae_days": {"value": round(sum(r["abs_error"] for r in verified) / len(verified), 2) if verified else None, "records": len(verified)},
            "demand_forecast_wape_pct": {"value": round(sum(f["backtest"]["wape_pct"] for f in forecasts) / len(forecasts), 2) if forecasts else None, "forecasts": len(forecasts)},
            "recommendation_acceptance_rate": {"value": round(sum(d["decision"] == "approve" for d in decisions) / n_dec, 3) if n_dec else None},
            "recommendation_modification_rate": {"value": round(sum(d["decision"] == "modify" for d in decisions) / n_dec, 3) if n_dec else None},
            "stockout_warning_accuracy": {"value": None, "reason": "needs verified stock-out outcomes from SAP (not in the Phase 1 feed)"},
            "recommendation_execution_rate": {"value": round(len(executed) / len(approved), 3) if approved else None},
            "business_impact_eur": {"value": None, "reason": "measured only from verified financial outcomes; none recorded yet"},
            "models": self.db.query("select id, model_name, version, algorithm, status, metrics, baseline_metrics, trained_at, promoted_by from model_versions where tenant_id=? order by trained_at desc", (t,)),
            "learning_records": lr,
        }
