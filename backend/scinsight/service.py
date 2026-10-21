"""Use cases of the SupplyChain Insight AI business-tool service (called by the FastAPI routes and the tests).

Every calculation reads the tenant's current SAP snapshot, runs the deterministic functions in business.py, and is stored
in agent_runs with a calculation_id. Recommendations are created only FROM a stored calculation (the server copies the
quantities; nothing numeric is accepted from an LLM), stay pending until an authorised human reviews them, and are never
written to SAP: an approved action waits for a separately recorded SAP execution event.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta

from fastapi import HTTPException

from backend.scinsight import business as bz
from backend.scinsight.db import Database, now_iso
from backend.scinsight.security import REVIEW_AUTHORITY, Principal, Security
from backend.scinsight.settings import SciSettings

DOMAIN_OF = {"material_readiness": "factory", "warehouse_balancing": "warehouse", "replenishment": "inventory",
             "lead_time_estimate": "procurement", "quality_check": "quality", "demand_forecast": "inventory"}
REVIEW_DECISIONS = {"approve": "approved", "reject": "rejected", "modify": "modified", "defer": "deferred"}


class Service:
    def __init__(self, db: Database, settings: SciSettings, security: Security):
        self.db, self.settings, self.security = db, settings, security

    # ------------------------------------------------------------------ snapshot + helpers
    def snapshot(self, tenant: str) -> dict:
        snap = self.db.one("select * from sap_snapshots where tenant_id=? and status='valid' order by extracted_at desc limit 1", (tenant,))
        if snap is None:
            raise HTTPException(status_code=409, detail="No valid SAP snapshot for this tenant — refresh the SAP extract before planning")
        as_of = date.fromisoformat(snap["as_of_date"])
        today = self.settings.sci_business_date or as_of
        age = (today - as_of).days
        if age > self.settings.sci_snapshot_max_age_days:
            raise HTTPException(status_code=409, detail=f"SAP snapshot {snap['id']} is {age} days old (max {self.settings.sci_snapshot_max_age_days}) — refresh the SAP extract")
        return {**snap, "as_of": as_of, "age_days": age}

    def _save_run(self, p: Principal, kind: str, request: dict, result: dict, snap: dict) -> dict:
        calc_id = f"CALC-{uuid.uuid4().hex[:12].upper()}"
        provenance = {"snapshot_id": snap["id"], "source_system": snap["source_system"], "extracted_at": snap["extracted_at"],
                      "as_of_date": snap["as_of_date"], "synthetic": bool(snap["synthetic"])}
        body = {"calculation_id": calc_id, "kind": kind, **result, "provenance": provenance}
        self.db.execute("insert into agent_runs(id,tenant_id,user_id,kind,request,result,snapshot_id,created_at) values(?,?,?,?,?,?,?,?)",
                        (calc_id, p.tenant_id, p.user_id, kind, json.dumps(request, default=str), json.dumps(body, default=str), snap["id"], now_iso()))
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), f"calc.{kind}", {"calculation_id": calc_id})
        return body

    def calculation(self, p: Principal, calc_id: str) -> dict:
        row = self.db.one("select * from agent_runs where id=? and tenant_id=?", (calc_id, p.tenant_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"calculation {calc_id} not found for this tenant")
        return json.loads(row["result"])

    def _batches(self, tenant: str, item: str, location: str | None = None) -> list[dict]:
        sql, params = "select * from inventory_batches where tenant_id=? and item_id=?", [tenant, item]
        if location:
            sql += " and location=?"
            params.append(location)
        return self.db.query(sql, params)

    def _demand(self, tenant: str, sku: str, wh: str, as_of: date) -> float:
        return bz.average_daily_demand(self.db.query("select day, quantity from sales_history where tenant_id=? and sku=? and warehouse=?", (tenant, sku, wh)), as_of)

    def _require_item(self, tenant: str, item: str) -> tuple[str, str]:
        prod = self.db.one("select sku, uom from products where tenant_id=? and sku=?", (tenant, item))
        if prod:
            return "product", prod["uom"]
        mat = self.db.one("select material_id, uom from materials where tenant_id=? and material_id=?", (tenant, item))
        if mat:
            return "material", mat["uom"]
        raise HTTPException(status_code=404, detail=f"{item} is not a product or material of this tenant")

    # ------------------------------------------------------------------ SAP reads (read-only)
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
        groups: dict[tuple, list] = {}
        for r in rows:
            groups.setdefault((r["location"], r["item_id"]), []).append(r)
        summary = []
        for (loc, it), batches in groups.items():
            u = bz.calculate_usable_stock(batches, snap["as_of"])
            summary.append({"location": loc, "item_id": it, "uom": batches[0]["uom"], "on_hand": sum(float(b["quantity"]) for b in batches),
                            "usable": u["usable"], "excluded": u["excluded"], "near_expiry": u["near_expiry"]})
        return {"snapshot": snap["id"], "as_of": snap["as_of_date"], "items": summary, "batches": rows if include_unusable else
                [r for r in rows if r["status"] == "released"], "rules": "usable = released, not expired, not reserved"}

    def bom(self, p: Principal, sku: str, on: date | None) -> dict:
        snap = self.snapshot(p.tenant_id)
        rows = self.db.query("select * from bom_components where tenant_id=? and sku=? order by bom_version, material_id", (p.tenant_id, sku))
        if not rows:
            raise HTTPException(status_code=404, detail=f"No BOM for {sku}")
        uoms = {m["material_id"]: m["uom"] for m in self.db.query("select material_id, uom from materials where tenant_id=?", (p.tenant_id,))}
        try:
            current = bz.calculate_bom_requirements(rows, 1, on or snap["as_of"], uoms)
        except bz.BusinessRuleError as exc:
            current = {"error": str(exc)}
        return {"sku": sku, "snapshot": snap["id"], "current_for_one_unit": current, "versions": rows}

    def table(self, p: Principal, table: str, filters: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        sql, params = f"select * from {table} where tenant_id=?", [p.tenant_id]  # noqa: S608 - table is chosen by the route, never by the client
        for column, value in filters.items():
            if value is not None:
                sql += f" and {column}=?"
                params.append(value)
        return {"snapshot": snap["id"], "as_of": snap["as_of_date"], "items": self.db.query(sql, params)}

    def catalog(self, tenant: str) -> dict:
        """Identifiers and names only (no quantities): lets an agent map 'vitamin C serum' to SER-VITC-30. Every code the agent
        then sends is validated again by the calculation endpoints."""
        q = self.db.query
        return {
            "products": [f"{r['sku']} = {r['name']}" for r in q("select sku, name from products where tenant_id=? order by sku", (tenant,))],
            "materials": [f"{r['material_id']} = {r['name']}" for r in q("select material_id, name from materials where tenant_id=? order by material_id", (tenant,))],
            "locations": [f"{r['code']} = {r['name']} ({r['kind']})" for r in q("select code, name, kind from warehouses where tenant_id=? order by code", (tenant,))],
            "suppliers": [f"{r['supplier_id']} = {r['name']}" for r in q("select supplier_id, name from suppliers where tenant_id=? order by supplier_id", (tenant,))],
            "production_orders": [f"{r['order_id']} = {r['sku']} starting {r['start_date']}" for r in
                                  q("select order_id, sku, start_date from production_orders where tenant_id=? order by order_id", (tenant,))],
        }

    def suppliers(self, p: Principal) -> dict:
        snap = self.snapshot(p.tenant_id)
        sups = self.db.query("select * from suppliers where tenant_id=? order by supplier_id", (p.tenant_id,))
        items = self.db.query("select * from supplier_items where tenant_id=?", (p.tenant_id,))
        for s in sups:
            s["items"] = [i for i in items if i["supplier_id"] == s["supplier_id"]]
        return {"snapshot": snap["id"], "items": sups}

    # ------------------------------------------------------------------ material readiness (factory)
    def _supplier_options(self, tenant: str, material: str, qty: float, need: date, as_of: date) -> list[dict]:
        options = []
        for si in self.db.query("select si.*, s.name, s.approved from supplier_items si join suppliers s on s.tenant_id=si.tenant_id and s.supplier_id=si.supplier_id "
                                "where si.tenant_id=? and si.material_id=?", (tenant, material)):
            receipts = self.db.query("select * from purchase_orders where tenant_id=? and supplier_id=? and received_date is not null", (tenant, si["supplier_id"]))
            est = bz.estimate_supplier_lead_time(receipts, si["contract_lead_time_days"])
            lead = est["estimate_days"] if est["receipts"] >= 3 else si["contract_lead_time_days"]
            order_qty = max(qty, float(si["moq"]))
            arrival = as_of + timedelta(days=int(round(lead)))
            options.append({"option": f"order from {si['name']}", "supplier_id": si["supplier_id"], "approved": bool(si["approved"]),
                            "quantity": order_qty, "lead_days": round(lead, 1), "lead_time_basis": "demonstrated (goods receipts)" if est["receipts"] >= 3 else "contract",
                            "contract_lead_days": si["contract_lead_time_days"], "arrival_date": arrival.isoformat(), "in_time": arrival <= need,
                            "cost_eur": round(order_qty * float(si["unit_price_eur"]), 2), "unit_price_eur": float(si["unit_price_eur"]),
                            "covers_need": True, "feasible": bool(si["approved"]),
                            "reasons": ([] if si["approved"] else ["supplier is not approved (procurement policy POL-PROC-001)"])
                            + ([] if arrival <= need else [f"arrives {arrival.isoformat()}, after the need date {need.isoformat()}"])})
        return options

    def material_readiness(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of = snap["as_of"]
        if req.get("production_order_id"):
            po = self.db.one("select * from production_orders where tenant_id=? and order_id=?", (p.tenant_id, req["production_order_id"]))
            if po is None:
                raise HTTPException(status_code=404, detail=f"production order {req['production_order_id']} not found")
            sku, qty, plant, need = po["sku"], float(po["quantity"]), po["plant"], date.fromisoformat(po["start_date"])
        else:
            if not (req.get("sku") and req.get("quantity") and req.get("need_date")):
                raise HTTPException(status_code=422, detail="give production_order_id, or sku + quantity + need_date")
            sku, qty, plant, need = req["sku"], float(req["quantity"]), req.get("plant") or "FAC-1", date.fromisoformat(str(req["need_date"]))
            po = None
        bom_rows = self.db.query("select * from bom_components where tenant_id=? and sku=?", (p.tenant_id, sku))
        uoms = {m["material_id"]: m["uom"] for m in self.db.query("select material_id, uom from materials where tenant_id=?", (p.tenant_id,))}
        try:
            req_lines = bz.calculate_bom_requirements(bom_rows, qty, need, uoms)
        except bz.BusinessRuleError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        lines, short = [], []
        for line in req_lines["lines"]:
            m = line["material_id"]
            stock = bz.calculate_usable_stock(self._batches(p.tenant_id, m, plant), as_of)
            pos = self.db.query("select * from purchase_orders where tenant_id=? and material_id=? and plant=? and status in ('open','confirmed')", (p.tenant_id, m, plant))
            shortage = bz.calculate_material_shortage(line["required_quantity"], stock["usable"], pos, need, line["uom"])
            entry = {**line, "usable": stock["usable"], "excluded_stock": stock["excluded"], **{k: shortage[k] for k in
                     ("confirmed_timely_inbound", "missing", "status", "timely_purchase_orders", "late_purchase_orders", "unconfirmed_purchase_orders")},
                     "required_date": need.isoformat(), "source_records": {"batches": [b["batch_id"] for b in stock["used_batches"]],
                                                                          "purchase_orders": [x["po_id"] for x in pos]}}
            if shortage["missing"] > 0:
                options = self._supplier_options(p.tenant_id, m, shortage["missing"], need, as_of)
                for late in shortage["late_purchase_orders"]:
                    options.append({"option": f"expedite {late['po_id']}", "supplier_id": late["supplier_id"], "quantity": late["quantity"],
                                    "arrival_date": late["promised_date"], "in_time": False, "covers_need": late["quantity"] >= shortage["missing"],
                                    "cost_eur": None, "feasible": False, "lead_days": None,
                                    "reasons": [f"currently promised {late['promised_date']}; a new date needs written supplier confirmation (no date is assumed)"]})
                entry["supply_options"] = bz.compare_supply_options(options)
                short.append(entry)
            lines.append(entry)
        producible = qty
        for e in lines:
            if e["missing"] > 0:
                per_unit = e["qty_per_unit"] * (1 + e["scrap_pct"] / 100)
                producible = min(producible, float((e["usable"] + e["confirmed_timely_inbound"]) // per_unit) if per_unit else producible)
        actions, alternatives = [], []
        for e in short:
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
            late_all = all(not a.get("arrives_in_time") for a in actions)
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
    def _sites(self, tenant: str, sku: str, as_of: date) -> dict:
        sites = {}
        for wh in self.db.query("select * from warehouses where tenant_id=? and kind='warehouse'", (tenant,)):
            batches = self._batches(tenant, sku, wh["code"])
            local = bz.calculate_usable_stock(batches, as_of)
            sites[wh["code"]] = {"warehouse": wh, "batches": batches, "local": local, "demand": self._demand(tenant, sku, wh["code"], as_of)}
        return sites

    def warehouse_balancing(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of, sku = snap["as_of"], req["sku"]
        kind, uom = self._require_item(p.tenant_id, sku)
        if kind != "product":
            raise HTTPException(status_code=422, detail="warehouse balancing is for finished products")
        sites = self._sites(p.tenant_id, sku, as_of)
        lanes = {(lane["origin"], lane["destination"]): lane for lane in self.db.query("select * from transport_lanes where tenant_id=?", (p.tenant_id,))}
        positions = []
        for code, s in sites.items():
            cover = bz.calculate_days_of_cover(s["local"]["usable"], s["demand"])
            stockout = as_of + timedelta(days=int(cover)) if cover is not None else None
            positions.append({"warehouse": code, "name": s["warehouse"]["name"], "usable": s["local"]["usable"], "daily_demand": s["demand"],
                              "days_of_cover": cover, "projected_stockout": stockout.isoformat() if stockout else None,
                              "target_cover_days": s["warehouse"]["target_cover_days"], "excluded_stock": s["local"]["excluded"], "near_expiry": s["local"]["near_expiry"]})
        target = req.get("target_warehouse") or min((x for x in positions if x["days_of_cover"] is not None), key=lambda x: x["days_of_cover"])["warehouse"]
        if target not in sites:
            raise HTTPException(status_code=404, detail=f"warehouse {target} not found")
        tpos = next(x for x in positions if x["warehouse"] == target)
        options = []
        for donor_code, s in sites.items():
            if donor_code == target:
                continue
            lane = lanes.get((donor_code, target))
            arrival = as_of + timedelta(days=int(lane["lead_days"])) if lane else None
            movable = bz.calculate_usable_stock(s["batches"], as_of, transfer_arrival=arrival) if arrival else {"usable": 0.0, "excluded": []}
            site = bz.Site(donor_code, movable["usable"], s["local"]["usable"], s["demand"], s["warehouse"]["target_cover_days"])
            lead = int(lane["lead_days"]) if lane else 0
            need = bz.calculate_replenishment_quantity(tpos["daily_demand"], tpos["usable"], sites[target]["warehouse"]["target_cover_days"], lead, uom)
            cands = bz.generate_transfer_candidates(target, {donor_code: site, target: bz.Site(target, 0, 0, 0, 0)})
            cand = cands[0] if cands else {"donor": donor_code, "surplus": 0.0, "donor_keeps_days": site.target_cover_days}
            ev = bz.evaluate_transfer_feasibility(cand, need, lane, as_of, date.fromisoformat(tpos["projected_stockout"]) if tpos["projected_stockout"] else None)
            ev.update({"option": f"transfer from {donor_code}", "need": need, "not_transferable": movable["excluded"]})
            options.append(ev)
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
        best = ranked[0] if ranked and ranked[0].get("feasible") else None
        result = {"sku": sku, "target_warehouse": target, "positions": positions, "options": ranked,
                  "status": "transfer_recommended" if best and best.get("donor") else "no_feasible_transfer" if not best else "other_option",
                  "proposed_actions": ([{"action": "stock_transfer", "sku": sku, "from": best["donor"], "to": target, "quantity": best["quantity"], "uom": uom,
                                         "lane_id": best["lane_id"], "arrival_date": best["arrival_date"], "cost_eur": best["cost_eur"]}] if best and best.get("donor") else [])}
        return self._save_run(p, "warehouse_balancing", req, result, snap)

    def replenishment(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        kind, uom = self._require_item(p.tenant_id, req["item_id"])
        if kind == "product":
            res = self.warehouse_balancing(p, {"sku": req["item_id"], "target_warehouse": req.get("location")})
            return res
        as_of = snap["as_of"]
        location = req.get("location") or "FAC-1"
        need_date = date.fromisoformat(str(req["need_date"])) if req.get("need_date") else as_of + timedelta(days=14)
        usable = bz.calculate_usable_stock(self._batches(p.tenant_id, req["item_id"], location), as_of)["usable"]
        qty = float(req.get("quantity") or 0)
        if qty <= 0:
            raise HTTPException(status_code=422, detail="quantity must be positive for material replenishment")
        options = bz.compare_supply_options(self._supplier_options(p.tenant_id, req["item_id"], qty, need_date, as_of))
        result = {"item_id": req["item_id"], "location": location, "usable": usable, "quantity": qty, "need_date": need_date.isoformat(), "options": options,
                  "proposed_actions": [{"action": "purchase_request", "material_id": req["item_id"], "quantity": options[0]["quantity"], "uom": uom,
                                        "supplier_id": options[0]["supplier_id"], "arrival_date": options[0]["arrival_date"], "cost_eur": options[0]["cost_eur"],
                                        "lead_days": options[0]["lead_days"], "lead_time_basis": options[0].get("lead_time_basis")}]
                  if options and options[0].get("feasible") else []}
        return self._save_run(p, "replenishment", req, result, snap)

    def quality_check(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
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
    def forecast_demand(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        as_of, sku, wh, horizon = snap["as_of"], req["sku"], req["warehouse"], int(req.get("horizon_days") or 14)
        rows = {date.fromisoformat(r["day"]): float(r["quantity"]) for r in self.db.query("select day, quantity from sales_history where tenant_id=? and sku=? and warehouse=?", (p.tenant_id, sku, wh))}
        if not rows:
            raise HTTPException(status_code=404, detail=f"no sales history for {sku} at {wh}")

        def predict(day: date, cutoff: date) -> float:  # baseline: 28-day mean x weekday index (from the 56 days before cutoff)
            window = [rows.get(cutoff - timedelta(days=i), 0.0) for i in range(1, 29)]
            mean = sum(window) / 28 or 0.0
            same = [rows.get(cutoff - timedelta(days=i), 0.0) for i in range(1, 57) if (cutoff - timedelta(days=i)).weekday() == day.weekday()]
            idx = (sum(same) / len(same)) / mean if mean and same else 1.0
            return round(mean * idx, 1)
        holdout = [as_of - timedelta(days=i) for i in range(14, 0, -1)]
        cutoff = as_of - timedelta(days=14)
        actual = [rows.get(d, 0.0) for d in holdout]
        pred = [predict(d, cutoff) for d in holdout]
        naive = [rows.get(d - timedelta(days=7), 0.0) for d in holdout]
        wape = lambda f: round(100 * sum(abs(a - b) for a, b in zip(actual, f, strict=True)) / (sum(actual) or 1), 2)  # noqa: E731
        forecast = [{"date": (as_of + timedelta(days=i)).isoformat(), "units": predict(as_of + timedelta(days=i), as_of)} for i in range(horizon)]
        result = {"sku": sku, "warehouse": wh, "method": "baseline: 28-day mean x weekday index", "model_version": "demand-baseline-v1",
                  "forecast": forecast, "total": round(sum(f["units"] for f in forecast), 1),
                  "backtest": {"holdout_days": 14, "wape_pct": wape(pred), "naive_same_weekday_wape_pct": wape(naive)}, "proposed_actions": []}
        return self._save_run(p, "demand_forecast", req, result, snap)

    def lead_time(self, p: Principal, req: dict) -> dict:
        snap = self.snapshot(p.tenant_id)
        sup = self.db.one("select * from suppliers where tenant_id=? and supplier_id=?", (p.tenant_id, req["supplier_id"]))
        if sup is None:
            raise HTTPException(status_code=404, detail=f"supplier {req['supplier_id']} not found")
        material = req.get("material_id")
        item = self.db.one("select * from supplier_items where tenant_id=? and supplier_id=?" + (" and material_id=?" if material else ""),
                           (p.tenant_id, req["supplier_id"], material) if material else (p.tenant_id, req["supplier_id"]))
        receipts = self.db.query("select * from purchase_orders where tenant_id=? and supplier_id=? and received_date is not null" + (" and material_id=?" if material else ""),
                                 (p.tenant_id, req["supplier_id"], material) if material else (p.tenant_id, req["supplier_id"]))
        est = bz.estimate_supplier_lead_time(receipts, item["contract_lead_time_days"] if item else None)
        promoted = self.db.one("select * from model_versions where tenant_id=? and model_name='supplier_lead_time' and status='promoted' order by promoted_at desc limit 1", (p.tenant_id,))
        model_pred = None
        if promoted and req.get("quantity"):
            from backend.scinsight.learning import predict_lead_time
            model_pred = predict_lead_time(self.db, p.tenant_id, promoted, req["supplier_id"], float(req["quantity"]), snap["as_of"])
        predicted = model_pred if model_pred is not None else est["estimate_days"]
        result = {"supplier_id": req["supplier_id"], "supplier": sup["name"], "material_id": material, "estimate": est,
                  "predicted_lead_time_days": predicted, "model_version": promoted["version"] if (promoted and model_pred is not None) else "lead-time-empirical-v1",
                  "basis": "promoted ML model" if model_pred is not None else est["basis"], "proposed_actions": []}
        return self._save_run(p, "lead_time_estimate", req, result, snap)

    # ------------------------------------------------------------------ decisions + human review
    def create_decision(self, p: Principal, req: dict) -> dict:
        calc = self.calculation(p, req["calculation_id"])
        actions = calc.get("proposed_actions") or []
        if not actions and not req.get("allow_no_action"):
            raise HTTPException(status_code=422, detail="the calculation proposes no action; nothing to review")
        key = req.get("idempotency_key") or calc["calculation_id"]
        existing = self.db.one("select * from recommendations where tenant_id=? and idempotency_key=?", (p.tenant_id, key))
        if existing:
            return self._rec(existing) | {"idempotent_replay": True}
        rec_id = f"REC-{uuid.uuid4().hex[:10].upper()}"
        prediction = None
        purchase = next((a for a in actions if a.get("action") == "purchase_request" and a.get("lead_days") is not None), None)
        if purchase:  # the lead time behind the purchase request is a prediction that the goods receipt later verifies
            prediction = {"metric": "lead_time_days", "predicted": purchase["lead_days"], "supplier_id": purchase["supplier_id"],
                          "material_id": purchase["material_id"], "basis": purchase.get("lead_time_basis"), "po_id": req.get("po_id")}
        domain = "procurement" if calc["kind"] == "replenishment" and purchase else DOMAIN_OF.get(calc["kind"], "inventory")
        title = req.get("title") or f"{calc['kind'].replace('_', ' ')} — {len(actions)} proposed action(s)"
        risk = "high" if calc.get("status") in ("short",) or any(o.get("in_time") is False for o in calc.get("options", [])[:1]) else "medium"
        self.db.execute("insert into recommendations(id,tenant_id,calculation_id,domain,title,proposed_actions,evidence,prediction,risk_level,status,idempotency_key,"
                        "model_version,created_by,created_at,updated_at) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (rec_id, p.tenant_id, calc["calculation_id"], domain, title[:300], json.dumps(actions, default=str),
                         json.dumps({"calculation_id": calc["calculation_id"], "provenance": calc["provenance"]}), json.dumps(prediction) if prediction else None,
                         risk, "pending_review", key, calc.get("model_version"), p.user_id, now_iso(), now_iso()))
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.created", {"recommendation_id": rec_id, "calculation_id": calc["calculation_id"]})
        return self.get_decision(p, rec_id)

    @staticmethod
    def _rec(row: dict) -> dict:
        return {**row, "proposed_actions": json.loads(row["proposed_actions"]), "evidence": json.loads(row["evidence"]),
                "prediction": json.loads(row["prediction"]) if row.get("prediction") else None,
                "review_authority": sorted(REVIEW_AUTHORITY.get(row["domain"], set()))}

    def get_decision(self, p: Principal, rec_id: str) -> dict:
        row = self.db.one("select * from recommendations where id=? and tenant_id=?", (rec_id, p.tenant_id))
        if row is None:
            raise HTTPException(status_code=404, detail=f"recommendation {rec_id} not found for this tenant")
        out = self._rec(row)
        out["reviews"] = [{**r, "reviewer_roles": json.loads(r["reviewer_roles"]), "modifications": json.loads(r["modifications"]) if r["modifications"] else None}
                          for r in self.db.query("select * from human_decisions where recommendation_id=? and tenant_id=? order by created_at", (rec_id, p.tenant_id))]
        out["sap_execution"] = self.db.query("select * from sap_execution_refs where recommendation_id=? and tenant_id=?", (rec_id, p.tenant_id))
        out["outcomes"] = self.db.query("select * from observed_outcomes where recommendation_id=? and tenant_id=?", (rec_id, p.tenant_id))
        out["verified_review"] = out["status"] in ("approved", "rejected", "modified", "deferred", "executed") and bool(out["reviews"])
        return out

    def list_decisions(self, p: Principal, status: str | None) -> list[dict]:
        rows = self.db.query("select * from recommendations where tenant_id=?" + (" and status=?" if status else "") + " order by created_at desc",
                             (p.tenant_id, status) if status else (p.tenant_id,))
        return [self._rec(r) for r in rows]

    def review(self, p: Principal, rec_id: str, req: dict) -> dict:
        rec = self.get_decision(p, rec_id)
        self.security.require_reviewer(p, rec["domain"])
        if req["decision"] == "modify" and not req.get("modifications"):
            raise HTTPException(status_code=422, detail="a 'modify' decision must state the modifications")
        new_status = REVIEW_DECISIONS[req["decision"]]

        def apply(q):
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

    def withdraw(self, p: Principal, rec_id: str) -> dict:
        rec = self.get_decision(p, rec_id)
        if rec["created_by"] != p.user_id and "supply_chain_director" not in p.roles:
            raise HTTPException(status_code=403, detail="only the creator or the director can withdraw a recommendation")
        if not self.db.execute("update recommendations set status='withdrawn', updated_at=? where id=? and tenant_id=? and status='pending_review'", (now_iso(), rec_id, p.tenant_id)):
            raise HTTPException(status_code=409, detail="only a pending recommendation can be withdrawn")
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.withdrawn", {"recommendation_id": rec_id})
        return self.get_decision(p, rec_id)

    def record_sap_execution(self, p: Principal, rec_id: str, req: dict) -> dict:
        self.security.require(p, {"sap_executor", "supply_chain_director"}, "Recording an SAP execution")
        rec = self.get_decision(p, rec_id)
        if rec["status"] not in ("approved", "modified"):
            raise HTTPException(status_code=409, detail="only an approved (or approved-with-changes) recommendation can be marked as executed in SAP")
        linked = self.db.one("select recommendation_id from sap_execution_refs where tenant_id=? and sap_document=?", (p.tenant_id, req["sap_document"]))
        if linked:
            raise HTTPException(status_code=409, detail=f"SAP document {req['sap_document']} is already linked to {linked['recommendation_id']}")
        self.db.transaction([
            ("insert into sap_execution_refs(id,tenant_id,recommendation_id,sap_document,doc_type,executed_at,recorded_by,source) values(?,?,?,?,?,?,?,?)",
             (f"SX-{uuid.uuid4().hex[:10].upper()}", p.tenant_id, rec_id, req["sap_document"], req["doc_type"], str(req["executed_at"]), p.user_id, "manual_sap_execution_record")),
            ("update recommendations set status='executed', updated_at=? where id=? and tenant_id=?", (now_iso(), rec_id, p.tenant_id))])
        self.security.audit(p.tenant_id, p.user_id, sorted(p.roles), "decision.sap_execution_recorded", {"recommendation_id": rec_id, "sap_document": req["sap_document"]})
        return self.get_decision(p, rec_id)

    # ------------------------------------------------------------------ outcome reconciliation + learning
    def reconcile(self, p: Principal, rec_id: str) -> dict:
        self.security.require(p, {"agent_service", "planner", "supply_chain_director", "mlops_engineer"}, "Outcome reconciliation")
        rec = self.get_decision(p, rec_id)
        if rec["status"] != "executed":
            raise HTTPException(status_code=409, detail="only an executed recommendation (with a recorded SAP execution) can be reconciled")
        pred = rec["prediction"]
        if not pred or pred.get("metric") != "lead_time_days":
            return {"recommendation_id": rec_id, "status": "unsupported_metric",
                    "reason": "Phase 1 reconciles supplier lead-time predictions; other outcome types need their SAP result feed."}
        po_id = pred.get("po_id") or next((x["sap_document"] for x in rec["sap_execution"] if x["doc_type"] == "purchase_order"), None)
        po = self.db.one("select * from purchase_orders where tenant_id=? and po_id=?", (p.tenant_id, po_id)) if po_id else None
        outcome = bz.reconcile_actual_outcome(pred, po)
        if outcome["status"] in ("missing", "pending"):
            return {"recommendation_id": rec_id, **outcome}
        human = rec["reviews"][-1]["decision"] if rec["reviews"] else "none"
        out_id, lr_id = f"OUT-{uuid.uuid4().hex[:10].upper()}", f"LR-{uuid.uuid4().hex[:10].upper()}"
        verified = outcome["status"] == "verified"
        label = {"metric": "lead_time_days", "actual": outcome["actual"]}
        features = {"supplier_id": po["supplier_id"], "material_id": po["material_id"], "quantity": po["quantity"], "order_date": po["order_date"]}

        def write(q):
            if q("select id from learning_records where tenant_id=? and recommendation_id=? and label_version='v1'", (p.tenant_id, rec_id)):
                return False
            q("insert into observed_outcomes(id,tenant_id,recommendation_id,source_document,metric,predicted,actual,unit,observed_at,complete,quality_flags) values(?,?,?,?,?,?,?,?,?,?,?)",
              (out_id, p.tenant_id, rec_id, outcome["source_document"], "lead_time_days", outcome["error"]["predicted"], outcome["actual"], "days",
               outcome["received_date"], int(verified), json.dumps(outcome["quality_flags"])))
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

    def learning_metrics(self, p: Principal) -> dict:
        t = p.tenant_id
        executed = self.db.query("select id from recommendations where tenant_id=? and status='executed'", (t,))
        lr = self.db.query("select * from learning_records where tenant_id=?", (t,))
        verified = [r for r in lr if r["outcome_status"] == "verified"]
        decisions = self.db.query("select decision from human_decisions where tenant_id=?", (t,))
        approved = self.db.query("select id from recommendations where tenant_id=? and status in ('approved','modified','executed')", (t,))
        forecasts = [json.loads(r["result"]) for r in self.db.query("select result from agent_runs where tenant_id=? and kind='demand_forecast'", (t,))]
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
