"""Deterministic business calculations. LLMs may explain these outputs but never create quantities."""
from __future__ import annotations

import math
from datetime import date, timedelta

from backend.app.forecasting import forecast
from backend.app.optimizer import optimize_transfers
from backend.app.sap import SapRepository

DECISION_CONTROL = "Advisory only. An authorized manager must approve; a planner executes any accepted action manually in SAP."


class SupplyChainEngine:
    def __init__(self, sap: SapRepository):
        self.sap = sap

    # ------------------------------------------------------------------ helpers
    def _confirmed_pos(self, plant: str, material: str) -> list[dict]:
        return [
            po
            for po in self.sap.section("purchase_orders")
            if po["plant"] == plant and po["material"] == material and po.get("status", "confirmed") == "confirmed"
        ]

    def _warehouses(self) -> list[str]:
        return [row["code"] for row in self.sap.section("plants") if row["type"] == "warehouse"]

    def _in_transit_to(self, warehouse: str, material: str, horizon_end: date) -> float:
        total = 0.0
        for shipment in self.sap.section("shipments") if self.sap.has("shipments") else []:
            if shipment["to"] != warehouse or shipment["material"] != material or shipment["status"] not in ("in_transit", "planned"):
                continue
            eta = date.fromisoformat(shipment["eta"]) + timedelta(days=int(shipment.get("delay_days") or 0))
            if eta <= horizon_end:
                total += float(shipment["quantity"])
        return round(total, 3)

    # ------------------------------------------------------- 1. factory readiness
    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: date) -> dict:
        self.sap.validate_codes(plant=plant, material=material)
        bom = [row for row in self.sap.section("bom") if row["plant"] == plant and row["parent"] == material]
        if not bom:
            raise ValueError(f"No approved BOM for {material} at {plant}")
        components, proposed_actions = [], []
        for item in bom:
            component = item["component"]
            uom = self.sap.material(component)["uom"]
            raw_required = quantity * float(item["quantity"]) * (1 + float(item["scrap_pct"]) / 100)
            required = math.ceil(raw_required) if uom == "EA" else round(raw_required, 3)
            on_hand = self.sap.on_hand(plant, component)
            excluded = [
                {"batch": row["batch"], "status": row["status"] if row["status"] != "unrestricted" else "expired", "quantity": row["quantity"]}
                for row in self.sap.stock_rows(plant, component)
                if row["status"] != "unrestricted" or (row.get("expiry") and date.fromisoformat(row["expiry"]) < self.sap.as_of)
            ]
            confirmed = self._confirmed_pos(plant, component)
            relevant_pos = [po for po in confirmed if date.fromisoformat(po["delivery_date"]) <= need_by]
            inbound = round(sum(float(po["quantity"]) for po in relevant_pos), 3)
            available = round(on_hand + inbound, 3)
            shortage = round(max(0.0, required - available), 3)
            components.append(
                {
                    "component": component,
                    "uom": uom,
                    "required": required,
                    "unrestricted_on_hand": on_hand,
                    "confirmed_inbound_by_need_date": inbound,
                    "available": available,
                    "shortage": shortage,
                    "status": "ready" if shortage == 0 else "short",
                    "source_documents": [po["po"] for po in relevant_pos],
                    "excluded_stock": excluded,
                }
            )
            if shortage:
                later = sorted(
                    (po for po in confirmed if date.fromisoformat(po["delivery_date"]) > need_by),
                    key=lambda po: po["delivery_date"],
                )
                if later:
                    proposed_actions.append(
                        {
                            "action": "expedite_purchase_order",
                            "purchase_order": later[0]["po"],
                            "supplier": later[0]["supplier"],
                            "plant": plant,
                            "material": component,
                            "quantity": min(shortage, float(later[0]["quantity"])),
                            "current_delivery_date": later[0]["delivery_date"],
                            "required_by": need_by.isoformat(),
                        }
                    )
                else:
                    suppliers = self.sap.section("suppliers") if self.sap.has("suppliers") else []
                    supplier = next((s for s in suppliers if component in s["materials"]), None)
                    proposed_actions.append(
                        {
                            "action": "source_material",
                            "plant": plant,
                            "material": component,
                            "quantity": shortage,
                            "required_by": need_by.isoformat(),
                            "primary_supplier": supplier["name"] if supplier else None,
                            "approved_secondary_source": supplier.get("secondary_source") if supplier else None,
                        }
                    )
        readiness_pct = round(100 * sum(1 for row in components if row["status"] == "ready") / len(components), 1)
        overall = "ready" if readiness_pct == 100 else "at_risk" if readiness_pct >= 75 else "not_ready"
        return {
            "use_case": "factory_material_readiness",
            "plant": plant,
            "material": material,
            "planned_quantity": quantity,
            "need_by": need_by.isoformat(),
            "as_of": self.sap.as_of.isoformat(),
            "status": overall,
            "component_readiness_pct": readiness_pct,
            "components": components,
            "proposed_actions": proposed_actions,
            "decision_control": DECISION_CONTROL,
        }

    # -------------------------------------------------------- 2. stock balancing
    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict:
        self.sap.validate_codes(material=material)
        warehouses = self._warehouses()
        daily_demand = self.sap.section("warehouse_demand_daily").get(material)
        if not daily_demand:
            raise ValueError(f"No warehouse demand history for {material}")
        horizon_end = self.sap.as_of + timedelta(days=horizon_days)
        on_hand = {warehouse: self.sap.on_hand(warehouse, material) for warehouse in warehouses}
        in_transit = {warehouse: self._in_transit_to(warehouse, material, horizon_end) for warehouse in warehouses}
        stock = {warehouse: round(on_hand[warehouse] + in_transit[warehouse], 3) for warehouse in warehouses}
        safety_stock = float(self.sap.material(material).get("safety_stock", 0))
        forecast_by_warehouse = {warehouse: forecast(float(daily_demand[warehouse]), horizon_days) for warehouse in warehouses}
        service_factor = max(0.75, min(1.25, service_level / 0.95))
        targets = {
            warehouse: round(forecast_by_warehouse[warehouse]["total_forecast"] * service_factor + safety_stock, 3)
            for warehouse in warehouses
        }
        optimization = optimize_transfers(stock, targets, self.sap.section("lanes"))
        positions = [
            {
                "warehouse": warehouse,
                "on_hand": on_hand[warehouse],
                "in_transit_within_horizon": in_transit[warehouse],
                "forecast_demand": forecast_by_warehouse[warehouse]["total_forecast"],
                "target_stock": targets[warehouse],
                "surplus_or_gap": round(stock[warehouse] - targets[warehouse], 3),
                "days_of_cover": round(on_hand[warehouse] / max(float(daily_demand[warehouse]), 0.001), 1),
            }
            for warehouse in warehouses
        ]
        return {
            "use_case": "three_warehouse_stock_balancing",
            "material": material,
            "horizon_days": horizon_days,
            "service_level": service_level,
            "as_of": self.sap.as_of.isoformat(),
            "positions": positions,
            "forecast_engine": sorted({item["engine"] for item in forecast_by_warehouse.values()}),
            "forecast_training_mae": {w: f["training_mae"] for w, f in forecast_by_warehouse.items()},
            "optimization": optimization,
            "proposed_actions": optimization["transfers"],
            "decision_control": "Transfers are proposals only; no SAP stock-transport order is created.",
        }

    def demand_forecast(self, material: str, warehouse: str | None, horizon_days: int) -> dict:
        self.sap.validate_codes(material=material, plant=warehouse)
        demands = self.sap.section("warehouse_demand_daily").get(material)
        if not demands:
            raise ValueError(f"No demand history for {material}")
        selected = {warehouse: demands[warehouse]} if warehouse else demands
        return {
            "material": material,
            "forecasts": {code: forecast(float(base), horizon_days) for code, base in selected.items()},
        }

    def what_if(self, material: str, demand_change_pct: float, supplier_delay_days: int, horizon_days: int) -> dict:
        baseline = self.stock_balance(material, horizon_days)
        factor = 1 + demand_change_pct / 100
        scenario_positions = []
        for position in baseline["positions"]:
            demand = round(position["forecast_demand"] * factor, 3)
            target = round(position["target_stock"] + demand - position["forecast_demand"], 3)
            stock = position["on_hand"] + position["in_transit_within_horizon"]
            scenario_positions.append({**position, "forecast_demand": demand, "target_stock": target, "surplus_or_gap": round(stock - target, 3)})
        stock = {row["warehouse"]: row["on_hand"] + row["in_transit_within_horizon"] for row in scenario_positions}
        targets = {row["warehouse"]: row["target_stock"] for row in scenario_positions}
        optimization = optimize_transfers(stock, targets, self.sap.section("lanes"))
        if supplier_delay_days:
            for action in optimization["transfers"]:
                action["scenario_warning"] = f"Supplier receipts assumed {supplier_delay_days} days late"
        return {
            "scenario": {"demand_change_pct": demand_change_pct, "supplier_delay_days": supplier_delay_days},
            "material": material,
            "baseline_positions": baseline["positions"],
            "scenario_positions": scenario_positions,
            "optimization": optimization,
            "proposed_actions": optimization["transfers"],
            "hypothetical": True,
        }

    # -------------------------------------------------------- 3. supplier risk
    def supplier_risk(self, supplier: str) -> dict:
        master = self.sap.supplier(supplier)
        history = [row for row in self.sap.section("po_history") if row["supplier"] == master["name"]]
        receipts = []
        for row in history:
            delay = (date.fromisoformat(row["received_date"]) - date.fromisoformat(row["promised_date"])).days
            accepted = float(row["quantity_received"]) - float(row["quality_rejected"])
            in_full = accepted >= 0.98 * float(row["quantity_ordered"])
            receipts.append({**row, "delay_days": delay, "on_time": delay <= 0, "in_full": in_full, "otif": delay <= 0 and in_full})
        count = len(receipts) or 1
        otif_pct = round(100 * sum(r["otif"] for r in receipts) / count, 1) if receipts else None
        avg_delay = round(sum(max(r["delay_days"], 0) for r in receipts) / count, 1) if receipts else None
        ordered = sum(float(r["quantity_ordered"]) for r in receipts) or 1
        reject_pct = round(100 * sum(float(r["quality_rejected"]) for r in receipts) / ordered, 2) if receipts else None
        open_pos = [po for po in self.sap.section("purchase_orders") if po["supplier"] == master["name"]]
        exposure = round(sum(float(po["quantity"]) * float(self.sap.material(po["material"])["unit_cost"]) for po in open_pos), 2)
        open_quality = [lot for lot in self.sap.section("quality_lots") if lot.get("supplier") == master["name"] and lot["status"] in ("inspection", "blocked")]
        single_source = not master.get("secondary_source")

        score = 0.0
        if otif_pct is not None:
            score += max(0.0, master["otif_target_pct"] - otif_pct) * 0.8
        score += min(25.0, (avg_delay or 0) * 2.5)
        score += min(25.0, (reject_pct or 0) * 2.5)
        score += 15.0 if single_source else 0.0
        score += 10.0 * len(open_quality)
        score = round(min(100.0, score), 1)
        rating = "high" if score >= 50 else "medium" if score >= 25 else "low"

        actions = []
        if rating != "low" and master.get("secondary_source"):
            actions.append({"action": "evaluate_secondary_source", "supplier": master["name"], "secondary_source": master["secondary_source"], "materials": master["materials"]})
        if any(lot["status"] == "blocked" for lot in open_quality):
            actions.append({"action": "issue_supplier_corrective_action_request", "supplier": master["name"], "lots": [lot["lot"] for lot in open_quality if lot["status"] == "blocked"]})
        if rating == "high" and single_source:
            actions.append({"action": "accelerate_secondary_source_qualification", "supplier": master["name"], "materials": master["materials"]})
        return {
            "use_case": "supplier_risk",
            "supplier": master,
            "as_of": self.sap.as_of.isoformat(),
            "receipts_analysed": len(receipts),
            "otif_pct": otif_pct,
            "otif_target_pct": master["otif_target_pct"],
            "average_delay_days": avg_delay,
            "quality_reject_pct": reject_pct,
            "single_source": single_source,
            "open_purchase_orders": open_pos,
            "open_po_exposure_eur": exposure,
            "open_quality_issues": open_quality,
            "risk_score": score,
            "risk_rating": rating,
            "receipts": receipts,
            "proposed_actions": actions,
            "decision_control": DECISION_CONTROL,
        }

    def supplier_scorecard(self) -> dict:
        rows = []
        for supplier in self.sap.section("suppliers"):
            risk = self.supplier_risk(supplier["name"])
            rows.append({k: risk[k] for k in ("otif_pct", "average_delay_days", "quality_reject_pct", "single_source", "open_po_exposure_eur", "risk_score", "risk_rating")} | {"supplier": supplier["name"], "code": supplier["code"]})
        return {"use_case": "supplier_scorecard", "as_of": self.sap.as_of.isoformat(), "suppliers": sorted(rows, key=lambda r: -r["risk_score"])}

    # ----------------------------------------------------------- 4. quality
    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict:
        self.sap.validate_codes(plant=plant, material=material)
        lots = [
            lot
            for lot in self.sap.section("quality_lots")
            if (not plant or lot["plant"] == plant) and (not material or lot["material"] == material)
        ]
        open_lots = [lot for lot in lots if lot["status"] not in ("released",)]
        bom = self.sap.section("bom")
        impacts = []
        for lot in open_lots:
            for order in self.sap.section("production_orders"):
                components = {row["component"] for row in bom if row["plant"] == order["plant"] and row["parent"] == order["material"]}
                if order["plant"] == lot["plant"] and lot["material"] in components:
                    impacts.append({"lot": lot["lot"], "production_order": order["order"], "finished_good": order["material"], "finish_date": order["finish_date"]})
        actions = [
            {"action": "expedite_quality_release", "lot": lot["lot"], "plant": lot["plant"], "material": lot["material"], "expected_release": lot["expected_release"]}
            for lot in open_lots
            if lot["status"] == "inspection" and any(i["lot"] == lot["lot"] for i in impacts)
        ] + [
            {"action": "replace_rejected_material", "lot": lot["lot"], "plant": lot["plant"], "material": lot["material"], "quantity": lot["quantity"], "supplier": lot.get("supplier")}
            for lot in open_lots
            if lot["status"] == "blocked"
        ]
        return {
            "use_case": "quality_status",
            "as_of": self.sap.as_of.isoformat(),
            "filters": {"plant": plant, "material": material},
            "lots": lots,
            "unavailable_quantity_by_material": {
                m: sum(float(lot["quantity"]) for lot in open_lots if lot["material"] == m) for m in sorted({lot["material"] for lot in open_lots})
            },
            "production_impacts": impacts,
            "proposed_actions": actions,
            "decision_control": DECISION_CONTROL,
        }

    # ---------------------------------------------------------- 5. logistics
    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict:
        self.sap.validate_codes(plant=warehouse, material=material)
        shipments = [
            s
            for s in self.sap.section("shipments")
            if (not warehouse or warehouse in (s["from"], s["to"])) and (not material or s["material"] == material)
        ]
        for s in shipments:
            s["revised_eta"] = (date.fromisoformat(s["eta"]) + timedelta(days=int(s.get("delay_days") or 0))).isoformat()
            s["escalate"] = int(s.get("delay_days") or 0) > 3
        delayed = [s for s in shipments if s.get("delay_days")]
        actions = [
            {"action": "escalate_shipment_delay", "shipment": s["shipment"], "carrier": s["carrier"], "delay_days": s["delay_days"], "reason": s["delay_reason"]}
            for s in shipments
            if s["escalate"]
        ]
        return {
            "use_case": "logistics_status",
            "as_of": self.sap.as_of.isoformat(),
            "filters": {"warehouse": warehouse, "material": material},
            "shipments": shipments,
            "delayed_count": len(delayed),
            "units_delayed": sum(float(s["quantity"]) for s in delayed),
            "lanes": self.sap.section("lanes"),
            "proposed_actions": actions,
            "decision_control": DECISION_CONTROL,
        }

    # ---------------------------------------------------------- 6. inventory
    def inventory_overview(self, material: str | None = None) -> dict:
        self.sap.validate_codes(material=material)
        warehouses = self._warehouses()
        goods = [m for m in self.sap.section("materials") if m["type"] == "FG" and (not material or m["code"] == material)]
        demand = self.sap.section("warehouse_demand_daily")
        rows = []
        for good in goods:
            for warehouse in warehouses:
                qty = self.sap.on_hand(warehouse, good["code"])
                daily = float(demand[good["code"]][warehouse])
                open_orders = sum(float(o["quantity"]) for o in self.sap.section("sales_orders") if o["warehouse"] == warehouse and o["material"] == good["code"])
                rows.append(
                    {
                        "material": good["code"],
                        "warehouse": warehouse,
                        "on_hand": qty,
                        "daily_demand": daily,
                        "days_of_cover": round(qty / daily, 1),
                        "open_sales_orders": open_orders,
                        "in_transit_14d": self._in_transit_to(warehouse, good["code"], self.sap.as_of + timedelta(days=14)),
                        "below_safety_stock": qty < float(good["safety_stock"]),
                    }
                )
        return {"use_case": "inventory_overview", "as_of": self.sap.as_of.isoformat(), "positions": rows, "proposed_actions": []}

    # --------------------------------------------------- 7. sales order fulfilment
    def sales_order_fulfilment(self, warehouse: str | None = None) -> dict:
        """Allocate warehouse stock (+ inbound arriving before each requested date) to open orders by date and priority;
        for shortfalls, propose the cheapest transfer from another DC whose lead time still meets the requested date."""
        self.sap.validate_codes(plant=warehouse)
        orders = sorted(self.sap.section("sales_orders"), key=lambda o: (o["requested_date"], o["priority"] != "high"))
        lanes = {(lane["from"], lane["to"]): lane for lane in self.sap.section("lanes")}
        allocated: dict[tuple[str, str], float] = {}
        rows, actions = [], []
        for order in orders:
            wh, mat, due = order["warehouse"], order["material"], date.fromisoformat(order["requested_date"])
            key = (wh, mat)
            on_hand = self.sap.on_hand(wh, mat)
            supply = on_hand + self._in_transit_to(wh, mat, due)
            prior = allocated.get(key, 0.0)
            confirmed = min(float(order["quantity"]), max(0.0, supply - prior))
            allocated[key] = prior + confirmed
            shortfall = round(float(order["quantity"]) - confirmed, 3)
            inbound_needed = confirmed > max(0.0, on_hand - prior)  # cannot ship from stock alone
            status = "on_track" if not shortfall and not inbound_needed else "depends_on_inbound" if not shortfall else "at_risk"
            option = None
            if shortfall:
                safety = float(self.sap.material(mat).get("safety_stock", 0))
                donors = []
                for donor in self._warehouses():
                    lane = lanes.get((donor, wh))
                    if donor == wh or not lane:
                        continue
                    committed = sum(float(o["quantity"]) for o in orders if o["warehouse"] == donor and o["material"] == mat)
                    spare = self.sap.on_hand(donor, mat) - committed - safety - allocated.get((donor, f"transfer:{mat}"), 0.0)
                    arrives = self.sap.as_of + timedelta(days=int(lane["lead_days"]))
                    if spare >= shortfall and arrives <= due:
                        donors.append((float(lane["cost_per_unit"]), donor, lane, arrives))
                if donors:
                    _, donor, lane, arrives = min(donors)
                    allocated[(donor, f"transfer:{mat}")] = allocated.get((donor, f"transfer:{mat}"), 0.0) + shortfall
                    option = {
                        "action": "stock_transfer", "from": donor, "to": wh, "material": mat, "quantity": shortfall,
                        "lead_days": lane["lead_days"], "arrives": arrives.isoformat(), "estimated_cost": round(shortfall * float(lane["cost_per_unit"]), 2),
                        "carbon_kg": round(shortfall * float(lane["carbon_kg_per_unit"]), 2), "for_sales_order": order["order"],
                    }
                else:
                    option = {"action": "propose_partial_delivery", "sales_order": order["order"], "warehouse": wh, "material": mat,
                              "deliverable_now": confirmed, "shortfall": shortfall, "customer": order["customer"]}
                actions.append(option)
            rows.append({**order, "available_by_due_date": round(supply, 3), "confirmed": round(confirmed, 3), "shortfall": shortfall,
                         "status": status, "resolution": option})
        if warehouse:
            rows = [r for r in rows if r["warehouse"] == warehouse]
            actions = [a for a in actions if a.get("to", a.get("warehouse")) == warehouse]
        return {
            "use_case": "sales_order_fulfilment",
            "as_of": self.sap.as_of.isoformat(),
            "orders": rows,
            "at_risk": sum(r["status"] == "at_risk" for r in rows),
            "depends_on_inbound": sum(r["status"] == "depends_on_inbound" for r in rows),
            "proposed_actions": actions,
            "decision_control": DECISION_CONTROL,
        }

    # --------------------------------------------------- 8. stocktake reconciliation
    def stocktake_reconciliation(self, tolerance_pct: float = 1.0) -> dict:
        """Explain each count difference from unposted goods movements, quality decisions and expiry; recommend posting or recount."""
        movements = self.sap.section("goods_movements")
        lots = self.sap.section("quality_lots")
        rows, actions = [], []
        for count in self.sap.section("stocktake_counts"):
            diff = round(float(count["counted_quantity"]) - float(count["book_quantity"]), 3)
            explained, evidence = 0.0, []
            for mv in movements:
                if not mv["posted"] and mv["plant"] == count["plant"] and mv["material"] == count["material"] and mv.get("batch") in (None, count["batch"]):
                    explained += float(mv["quantity"])
                    evidence.append({"type": "unposted_" + mv["type"], "document": mv["document"], "quantity": mv["quantity"], "date": mv["date"], "note": mv["reference"]})
            for lot in lots:
                if lot["plant"] == count["plant"] and lot["batch"] == count["batch"] and lot.get("usage_decision") == "scrap_pending":
                    explained -= float(lot["quantity"])
                    evidence.append({"type": "scrap_not_posted", "document": lot["lot"], "quantity": -float(lot["quantity"]), "note": lot.get("defect")})
            residual = round(diff - explained, 3)
            pct = round(100 * abs(residual) / max(float(count["book_quantity"]), 1), 2)
            if diff == 0:
                status, action = "matched", None
            elif residual == 0:
                status = "explained"
                action = {"action": "post_pending_movements", "plant": count["plant"], "material": count["material"], "batch": count["batch"],
                          "documents": [e["document"] for e in evidence], "quantity": diff, "count_id": count["count_id"]}
            elif pct <= tolerance_pct:
                status = "within_tolerance"
                action = {"action": "post_inventory_adjustment", "plant": count["plant"], "material": count["material"], "batch": count["batch"],
                          "quantity": residual, "count_id": count["count_id"], "reason": f"{pct}% <= {tolerance_pct}% tolerance"}
            else:
                status = "investigate"
                action = {"action": "recount", "plant": count["plant"], "material": count["material"], "batch": count["batch"],
                          "unexplained_quantity": residual, "count_id": count["count_id"], "reason": f"{pct}% unexplained exceeds {tolerance_pct}% tolerance"}
            if action:
                actions.append(action)
            value = abs(diff) * float(self.sap.material(count["material"])["unit_cost"])
            rows.append({**count, "difference": diff, "explained": round(explained, 3), "unexplained": residual, "unexplained_pct": pct,
                         "difference_value_eur": round(value, 2), "status": status, "evidence": evidence, "recommendation": action})
        return {
            "use_case": "stocktake_reconciliation",
            "as_of": self.sap.as_of.isoformat(),
            "tolerance_pct": tolerance_pct,
            "counts": rows,
            "to_investigate": sum(r["status"] == "investigate" for r in rows),
            "proposed_actions": actions,
            "decision_control": DECISION_CONTROL,
        }

    # --------------------------------------------------- 9. production order sweep
    def production_overview(self) -> dict:
        rows = []
        for order in self.sap.section("production_orders"):
            result = self.factory_readiness(order["plant"], order["material"], float(order["quantity"]), date.fromisoformat(order["finish_date"]))
            rows.append({**order, "readiness": result["status"], "component_readiness_pct": result["component_readiness_pct"],
                         "short_components": [c["component"] for c in result["components"] if c["status"] == "short"],
                         "proposed_actions": len(result["proposed_actions"])})
        return {"use_case": "production_overview", "as_of": self.sap.as_of.isoformat(), "orders": rows, "proposed_actions": []}

    def forecast_vs_actuals(self, material: str, warehouse: str) -> dict:
        from backend.app.forecasting import backtest

        self.sap.validate_codes(material=material, plant=warehouse)
        demand = self.sap.section("warehouse_demand_daily").get(material, {})
        if warehouse not in demand:
            raise ValueError(f"No demand history for {material} at {warehouse}")
        result = backtest(float(demand[warehouse]))
        to_date = lambda offset: (self.sap.as_of + timedelta(days=offset)).isoformat()  # noqa: E731
        return {
            "material": material, "warehouse": warehouse, "engine": result["engine"], "holdout_mape_pct": result["holdout_mape_pct"],
            "actual": [{"date": to_date(o), "value": v} for o, v in zip(result["offsets_actual"], result["actual"], strict=True)],
            "backtest": [{"date": to_date(o), "value": v} for o, v in zip(result["offsets_backtest"], result["backtest"], strict=True)],
            "forecast": [{"date": to_date(o), "value": v} for o, v in zip(result["offsets_forecast"], result["forecast"], strict=True)],
            "model_scope": "synthetic POC history; replace with approved SAP billing history before production",
        }

    # --------------------------------------------------- 10. position health (all material x location)
    def position_health(self, horizon_days: int = 14) -> list[dict]:
        """Coverage of every stocked position against its target: finished goods at DCs (demand x horizon + safety stock)
        and components at plants (requirements of production orders due within the horizon + safety stock)."""
        end = self.sap.as_of + timedelta(days=horizon_days)
        demand = self.sap.section("warehouse_demand_daily")
        bom = self.sap.section("bom")
        rows = []
        for material in self.sap.section("materials"):
            code, safety, cost = material["code"], float(material.get("safety_stock", 0)), float(material["unit_cost"])
            for plant in self.sap.section("plants"):
                loc = plant["code"]
                on_hand = self.sap.on_hand(loc, code)
                if plant["type"] == "warehouse":
                    if material["type"] != "FG":
                        continue
                    daily = float(demand.get(code, {}).get(loc, 0))
                    requirement = daily * horizon_days
                    inbound = self._in_transit_to(loc, code, end)
                else:
                    if material["type"] == "FG":
                        continue
                    requirement = 0.0
                    for order in self.sap.section("production_orders"):
                        if order["plant"] == loc and date.fromisoformat(order["finish_date"]) <= end:
                            for item in bom:
                                if item["plant"] == loc and item["parent"] == order["material"] and item["component"] == code:
                                    requirement += float(order["quantity"]) * float(item["quantity"]) * (1 + float(item["scrap_pct"]) / 100)
                    if not requirement and not on_hand:
                        continue
                    daily = requirement / horizon_days
                    inbound = sum(float(po["quantity"]) for po in self._confirmed_pos(loc, code) if date.fromisoformat(po["delivery_date"]) <= end)
                target = requirement + safety
                available = on_hand + inbound
                shortfall = max(0.0, target - available)
                rows.append({
                    "location": loc, "location_name": plant["name"], "location_type": plant["type"], "material": code,
                    "description": material["description"], "material_type": material["type"], "uom": material["uom"],
                    "on_hand": round(on_hand, 3), "inbound": round(inbound, 3), "requirement": round(requirement, 3), "target": round(target, 3),
                    "coverage_pct": round(100 * available / target, 1) if target else None,
                    "days_of_cover": round(on_hand / daily, 1) if daily else None,
                    "shortfall": round(shortfall, 3), "shortfall_value_eur": round(shortfall * cost, 2),
                    "excess": round(max(0.0, available - 2 * target), 3), "excess_value_eur": round(max(0.0, available - 2 * target) * cost, 2),
                    "stock_value_eur": round(on_hand * cost, 2),
                })
        return rows

    # --------------------------------------------------- 11. product 360
    PRODUCTION_LEAD_DAYS = 5  # POC assumption: release-to-finish time of a production order

    def products(self) -> list[dict]:
        out = []
        for m in self.sap.section("materials"):
            if m["type"] != "FG":
                continue
            p = self.product_360(m["code"], brief=True)
            out.append({k: p[k] for k in ("material", "description", "network_on_hand", "daily_demand", "network_days_of_cover", "first_stockout", "health", "producing_plant")})
        return out

    def product_360(self, material: str, horizon_days: int = 60, brief: bool = False) -> dict:
        """Everything about one finished good: stock by DC, sales, projected end of stock, component resupply needs with
        order-by dates, best suppliers per component and the best donor warehouse for each at-risk DC."""
        from backend.app.forecasting import forecast

        self.sap.validate_codes(material=material)
        master = self.sap.material(material)
        if master["type"] != "FG":
            raise ValueError(f"{material} is not a finished good")
        demand = self.sap.section("warehouse_demand_daily").get(material, {})
        safety = float(master.get("safety_stock", 0))
        as_of = self.sap.as_of
        orders = [o for o in self.sap.section("sales_orders") if o["material"] == material]
        shipments = [s for s in self.sap.section("shipments") if s["material"] == material and s["status"] in ("in_transit", "planned")]

        # Planned production output reaches the DCs 3 days after the finish date, split by each DC's share of demand
        # (POC assumption until SAP deployment plans are extracted).
        total_demand = sum(float(v) for v in demand.values()) or 1.0
        production_arrivals: dict[str, dict[int, float]] = {}
        for order in self.sap.section("production_orders"):
            if order["material"] != material:
                continue
            day = (date.fromisoformat(order["finish_date"]) + timedelta(days=3) - as_of).days
            for wh, daily in demand.items():
                share = float(order["quantity"]) * float(daily) / total_demand
                production_arrivals.setdefault(wh, {})[max(day, 0)] = production_arrivals.get(wh, {}).get(max(day, 0), 0) + share

        # Projection per DC: on hand + inbound shipments (revised ETA) + planned production share - XGBoost daily forecast
        dcs = []
        for wh in self._warehouses():
            daily_fc = forecast(float(demand.get(wh, 0)), horizon_days)["daily_forecast"]
            on_hand = self.sap.on_hand(wh, material)
            arrivals = {}
            for s in shipments:
                if s["to"] == wh:
                    eta = (date.fromisoformat(s["eta"]) + timedelta(days=int(s.get("delay_days") or 0)) - as_of).days
                    arrivals[max(eta, 0)] = arrivals.get(max(eta, 0), 0) + float(s["quantity"])
            from_production = production_arrivals.get(wh, {})
            level, projection, stockout, below_safety = on_hand, [], None, None
            for day in range(horizon_days):
                level += arrivals.get(day, 0) + from_production.get(day, 0) - daily_fc[day]
                projection.append({"date": (as_of + timedelta(days=day + 1)).isoformat(), "value": round(level, 1)})
                if below_safety is None and level < safety:
                    below_safety = (as_of + timedelta(days=day + 1)).isoformat()
                if stockout is None and level < 0:
                    stockout = (as_of + timedelta(days=day + 1)).isoformat()
            inbound = sum(arrivals.values())
            dcs.append({
                "warehouse": wh, "name": next(p["name"] for p in self.sap.section("plants") if p["code"] == wh),
                "on_hand": on_hand, "in_transit": inbound, "from_planned_production": round(sum(from_production.values()), 1),
                "daily_demand": float(demand.get(wh, 0)),
                "forecast_14d": round(sum(daily_fc[:14]), 1), "forecast_30d": round(sum(daily_fc[:30]), 1),
                "open_sales_orders": sum(float(o["quantity"]) for o in orders if o["warehouse"] == wh),
                "days_of_cover": round(on_hand / float(demand[wh]), 1) if demand.get(wh) else None,
                "below_safety_date": below_safety, "stockout_date": stockout,
                # Same 14-day target the OR-Tools balancer uses: forecast + safety stock.
                "surplus_14d": round(on_hand + inbound - sum(daily_fc[:14]) - safety, 1),
                "surplus_30d": round(on_hand + inbound - sum(daily_fc[:30]) - safety, 1), "projection": projection,
            })

        # Best donor warehouse for each DC that drops below safety stock within the horizon (14-day surplus, like the balancer)
        lanes = {(lane["from"], lane["to"]): lane for lane in self.sap.section("lanes")}
        for dc in dcs:
            dc["best_donor"], dc["donor_options"] = None, []
            if dc["stockout_date"] or dc["below_safety_date"]:
                deadline = date.fromisoformat(dc["stockout_date"] or dc["below_safety_date"])  # "in time" = before the stock-out
                need = round(max(0.0, -dc["surplus_14d"]), 1)
                options = []
                for donor in dcs:
                    lane = lanes.get((donor["warehouse"], dc["warehouse"]))
                    if donor is dc or not lane or donor["surplus_14d"] <= 0 or not need:
                        continue
                    arrives = as_of + timedelta(days=int(lane["lead_days"]))
                    qty = round(min(need, donor["surplus_14d"]), 1)
                    options.append({"from": donor["warehouse"], "quantity": qty, "lead_days": lane["lead_days"], "arrives": arrives.isoformat(),
                                    "in_time": arrives <= deadline, "cost_per_unit": lane["cost_per_unit"], "estimated_cost": round(qty * float(lane["cost_per_unit"]), 2),
                                    "carbon_kg": round(qty * float(lane["carbon_kg_per_unit"]), 1), "donor_surplus_14d": donor["surplus_14d"]})
                options.sort(key=lambda o: (not o["in_time"], -o["quantity"], o["cost_per_unit"]))
                dc["donor_options"] = options
                dc["best_donor"] = options[0] if options else None
                dc["gap_14d"] = need

        network_on_hand = sum(d["on_hand"] for d in dcs)
        network_daily = sum(d["daily_demand"] for d in dcs)
        first_stockout = min((d["stockout_date"] for d in dcs if d["stockout_date"]), default=None)
        first_below = min((d["below_safety_date"] for d in dcs if d["below_safety_date"]), default=None)
        health = "critical" if first_stockout and (date.fromisoformat(first_stockout) - as_of).days <= 14 else "warning" if first_below else "good"
        plant = next((b["plant"] for b in self.sap.section("bom") if b["parent"] == material), None)
        summary = {"material": material, "description": master["description"], "producing_plant": plant, "network_on_hand": network_on_hand,
                   "daily_demand": network_daily, "network_days_of_cover": round(network_on_hand / network_daily, 1) if network_daily else None,
                   "first_stockout": first_stockout, "first_below_safety": first_below, "health": health}
        if brief:
            return summary

        # Network resupply: 30-day demand + safety stock at every DC, net of stock, inbound and planned production orders.
        planned = sorted((o for o in self.sap.section("production_orders") if o["material"] == material), key=lambda o: o["finish_date"])
        planned_qty = sum(float(o["quantity"]) for o in planned)
        network_need = sum(max(0.0, d["forecast_30d"] + safety - d["on_hand"] - d["in_transit"]) for d in dcs)
        production_needed = round(max(0.0, network_need - planned_qty), 0)
        need_date = date.fromisoformat(first_below or first_stockout or (as_of + timedelta(days=30)).isoformat())
        finish_by = max(need_date - timedelta(days=3), as_of + timedelta(days=self.PRODUCTION_LEAD_DAYS))  # 3-day transfer window
        builds = [{"order": o["order"], "quantity": float(o["quantity"]), "finish_date": o["finish_date"], "status": o["status"]} for o in planned]
        if production_needed:
            builds.append({"order": "proposed", "quantity": production_needed, "finish_date": finish_by.isoformat(), "status": "proposed"})
        for build in builds:  # components must be at the plant when the order is released
            build["components_needed_by"] = max(as_of, date.fromisoformat(build["finish_date"]) - timedelta(days=self.PRODUCTION_LEAD_DAYS)).isoformat()

        suppliers = {s["name"]: s for s in self.sap.section("suppliers")}
        scorecard = {s["supplier"]: s for s in self.supplier_scorecard()["suppliers"]}
        components = []
        for item in (b for b in self.sap.section("bom") if b["parent"] == material and b["plant"] == plant):
            comp = item["component"]
            cmaster = self.sap.material(comp)
            per_unit = float(item["quantity"]) * (1 + float(item["scrap_pct"]) / 100)
            on_hand = self.sap.on_hand(plant, comp)
            confirmed = self._confirmed_pos(plant, comp)
            cumulative, first_short, schedule = 0.0, None, []
            for build in builds:  # MRP-style netting: cumulative requirement vs supply available by each need date
                need = per_unit * build["quantity"]
                need = math.ceil(need) if cmaster["uom"] == "EA" else round(need, 3)
                cumulative += need
                by = date.fromisoformat(build["components_needed_by"])
                supply = on_hand + sum(float(po["quantity"]) for po in confirmed if date.fromisoformat(po["delivery_date"]) <= by)
                gap = round(max(0.0, cumulative - supply), 3)
                schedule.append({"build": build["order"], "needed_by": build["components_needed_by"], "requirement": need, "cumulative": round(cumulative, 3),
                                 "supply_by_then": round(supply, 3), "gap": gap})
                if gap and first_short is None:
                    first_short = by
            total_supply = on_hand + sum(float(po["quantity"]) for po in confirmed)
            shortfall = round(max(0.0, cumulative + float(cmaster.get("safety_stock", 0)) - total_supply), 3)
            ranked = []
            for name, sup in suppliers.items():
                if comp in sup["materials"]:
                    sc = scorecard[name]
                    ranked.append({"supplier": name, "code": sup["code"], "risk_rating": sc["risk_rating"], "risk_score": sc["risk_score"], "otif_pct": sc["otif_pct"],
                                   "contract_lead_time_days": sup["contract_lead_time_days"],
                                   "effective_lead_time_days": round(sup["contract_lead_time_days"] + (sc["average_delay_days"] or 0), 1),
                                   "secondary_source": sup.get("secondary_source")})
            ranked.sort(key=lambda s: (s["risk_score"], s["effective_lead_time_days"]))
            best = ranked[0] if ranked else None
            target = first_short or (date.fromisoformat(builds[-1]["components_needed_by"]) if builds and shortfall else None)
            order_by = target - timedelta(days=math.ceil(best["effective_lead_time_days"])) if best and target else None
            if not shortfall and not first_short:
                status = "covered"
            elif not shortfall:
                status = "timing_gap"  # enough supply overall, but a confirmed PO lands after the need date: expedite it
            elif not first_short:
                status = "replenish_safety_stock"  # production is covered; only the safety stock is not
            elif order_by and order_by < as_of:
                status = "late"  # real shortage the normal lead time cannot meet: expedite or use a secondary source
            elif order_by and (order_by - as_of).days <= 7:
                status = "order_this_week"
            else:
                status = "plan"
            open_later = [po for po in confirmed if not first_short or date.fromisoformat(po["delivery_date"]) > first_short]
            components.append({
                "component": comp, "description": cmaster["description"], "uom": cmaster["uom"], "requirement_total": round(cumulative, 3),
                "on_hand": on_hand, "confirmed_inbound": round(total_supply - on_hand, 3), "purchase_orders": [po["po"] for po in confirmed],
                "first_shortage_date": first_short.isoformat() if first_short else None, "shortfall": shortfall,
                "order_by": order_by.isoformat() if order_by else None, "status": status, "schedule": schedule,
                "expedite_candidates": [po["po"] for po in open_later], "best_suppliers": ranked,
                "alternative_sources": [s["secondary_source"] for s in ranked if s.get("secondary_source")],
            })

        sales_history = self.forecast_vs_actuals(material, max(dcs, key=lambda d: d["daily_demand"])["warehouse"])

        # Inventory vs time to out-of-stock, based on forecast sales; warehouses ranked best -> worst
        for d in dcs:
            daily_sales = d["forecast_14d"] / 14 if d["forecast_14d"] else 0
            d["sales_days_of_cover"] = round(d["on_hand"] / daily_sales, 1) if daily_sales else None
            d["days_to_stockout"] = (date.fromisoformat(d["stockout_date"]) - as_of).days if d["stockout_date"] else None
            soon_below = d["below_safety_date"] and (date.fromisoformat(d["below_safety_date"]) - as_of).days <= 14
            d["health"] = "critical" if d["days_to_stockout"] is not None and d["days_to_stockout"] <= 7 else "warning" if soon_below or d["days_to_stockout"] else "good"
        ranked = sorted(dcs, key=lambda d: (d["days_to_stockout"] if d["days_to_stockout"] is not None else horizon_days + 1, d["sales_days_of_cover"] or 0), reverse=True)
        warehouse_ranking = [{"rank": i + 1, **{k: d[k] for k in ("warehouse", "name", "on_hand", "in_transit", "sales_days_of_cover", "days_to_stockout",
                                                               "stockout_date", "below_safety_date", "surplus_14d", "health")}} for i, d in enumerate(ranked[:5])]

        # Supply options per component: primary suppliers (actual performance) + qualified alternatives (quotes)
        quotes = self.sap.section("supplier_quotes") if self.sap.has("supplier_quotes") else []
        options = []
        for item in (b for b in self.sap.section("bom") if b["parent"] == material and b["plant"] == plant):
            comp, per_fg = item["component"], float(item["quantity"]) * (1 + float(item["scrap_pct"]) / 100)
            for name, sup in suppliers.items():
                if comp in sup["materials"] and sup.get("unit_price_eur") is not None:
                    sc = scorecard[name]
                    unit = sup["unit_price_eur"] + sup["freight_eur_per_order"] / sup["typical_order_qty"]
                    options.append({"supplier": name, "material": comp, "type": "primary", "qualified": True,
                                    "time_to_deliver_days": round(sup["contract_lead_time_days"] + (sc["average_delay_days"] or 0), 1),
                                    "time_basis": "contract lead time + actual average delay", "otif_pct": sc["otif_pct"], "risk_rating": sc["risk_rating"],
                                    "landed_cost_per_unit_eur": round(unit, 4), "cost_per_1000_finished_eur": round(unit * per_fg * 1000, 2)})
            for q in (q for q in quotes if q["material"] == comp):
                unit = q["unit_price_eur"] + q["freight_eur_per_order"] / q["typical_order_qty"]
                options.append({"supplier": q["supplier"], "material": comp, "type": "alternative", "qualified": q["qualified"],
                                "time_to_deliver_days": float(q["quoted_lead_time_days"]), "time_basis": "quoted lead time (no delivery history)",
                                "otif_pct": None, "risk_rating": None, "landed_cost_per_unit_eur": round(unit, 4),
                                "cost_per_1000_finished_eur": round(unit * per_fg * 1000, 2), "reference": q.get("reference")})
        for comp in {o["material"] for o in options}:
            same = [o for o in options if o["material"] == comp]
            cheapest, fastest = min(o["landed_cost_per_unit_eur"] for o in same), min(o["time_to_deliver_days"] for o in same)
            for o in same:
                o["cost_premium_pct"] = round(100 * (o["landed_cost_per_unit_eur"] / cheapest - 1), 1)
                o["days_slower_than_best"] = round(o["time_to_deliver_days"] - fastest, 1)
            # Recommended source per component: fastest qualified option within 10% of the cheapest landed cost
            eligible = [o for o in same if o["qualified"] and o["cost_premium_pct"] <= 10] or [o for o in same if o["qualified"]]
            best = min(eligible, key=lambda o: (o["time_to_deliver_days"], o["landed_cost_per_unit_eur"]))
            for o in same:
                o["recommended"] = o is best
        qualified = [o for o in options if o["qualified"]]
        supplier_ranking = {
            "fastest": sorted(qualified, key=lambda o: (o["time_to_deliver_days"], o["landed_cost_per_unit_eur"]))[:5],
            "lowest_cost": sorted(qualified, key=lambda o: (o["cost_premium_pct"], o["cost_per_1000_finished_eur"]))[:5],
        }

        # Easy-to-read key metrics for this product
        product_orders = [o for o in self.sales_order_fulfilment()["orders"] if o["material"] == material]
        ordered = sum(float(o["quantity"]) for o in product_orders)
        fill = round(100 * sum(float(o["confirmed"]) for o in product_orders) / ordered, 1) if ordered else 100.0
        sales_daily = sum(d["forecast_14d"] for d in dcs) / 14 or 1
        cover = round(network_on_hand / sales_daily, 1)
        primary = [o for o in options if o["type"] == "primary"]
        days_out = (date.fromisoformat(first_stockout) - as_of).days if first_stockout else None
        stock_value = round(network_on_hand * float(master["unit_cost"]), 2)
        scorecard_kpis = [
            {"label": "Stock on hand", "value": network_on_hand, "status": "info", "hint": f"{len(dcs)} DCs · €{stock_value:,.0f} at cost"},
            {"label": "Days of cover (sales)", "value": cover, "unit": " d", "status": "critical" if cover < 7 else "warning" if cover < 21 else "good", "hint": f"{sales_daily:,.0f} units/day forecast"},
            {"label": "First out-of-stock in", "value": days_out, "unit": " d", "status": "critical" if days_out is not None and days_out <= 7 else "warning" if days_out else "good",
             "hint": first_stockout and f"{first_stockout} at {next(d['warehouse'] for d in dcs if d['stockout_date'] == first_stockout)}" or "none within 60 days"},
            {"label": "Order fill rate", "value": fill, "unit": "%", "status": "good" if fill >= 98 else "warning", "hint": f"{len(product_orders)} open orders"},
            {"label": "Forecast accuracy", "value": round(100 - sales_history["holdout_mape_pct"], 1), "unit": "%", "status": "good", "hint": "100 − back-test MAPE"},
            {"label": "Inventory turns", "value": round(365 / cover, 1) if cover else None, "unit": "×", "status": "info", "hint": "annualised, sales ÷ stock"},
            {"label": "Supplier OTIF", "value": round(sum(o["otif_pct"] or 0 for o in primary) / len(primary), 1) if primary else None, "unit": "%",
             "status": "warning", "hint": "average of component suppliers"},
            {"label": "Slowest component", "value": max((o["time_to_deliver_days"] for o in primary), default=None), "unit": " d", "status": "warning",
             "hint": max(primary, key=lambda o: o["time_to_deliver_days"])["material"] if primary else ""},
            {"label": "Components late", "value": sum(c["status"] == "late" for c in components), "status": "critical" if any(c["status"] == "late" for c in components) else "good",
             "hint": f"of {len(components)} BOM components"},
            {"label": "Production coverage", "value": round(min(999, 100 * planned_qty / network_need), 1) if network_need else 100.0, "unit": "%",
             "status": "good" if planned_qty >= network_need else "warning", "hint": "planned ÷ 30-day need"},
        ]

        return {
            **summary,
            "scorecard": scorecard_kpis, "warehouse_ranking": warehouse_ranking,
            "supply_options": sorted(options, key=lambda o: (o["material"], not o["recommended"], o["time_to_deliver_days"])),
            "supplier_ranking": supplier_ranking,
            "unit_cost": master["unit_cost"], "safety_stock": safety, "horizon_days": horizon_days,
            "warehouses": dcs,
            "sales": {"open_orders": orders, "open_order_quantity": sum(float(o["quantity"]) for o in orders),
                      "forecast_vs_actuals": sales_history},
            "resupply": {"network_need_30d": round(network_need, 0), "builds": builds, "planned_quantity": planned_qty,
                         "additional_production_needed": production_needed, "need_at_dc_by": need_date.isoformat(),
                         "assumptions": f"production lead time {self.PRODUCTION_LEAD_DAYS} days (components due at release); 3-day transfer window to DCs; "
                                        "30-day XGBoost demand + safety stock target; supplier time to deliver = contract lead time + average delay",
                         "components": components},
        }

    def product_brief(self, material: str) -> dict:
        """One-screen product brief: supply status, reserve above safety stock, time to out-of-stock per DC,
        every open supply issue paired with its proposed fix, and the best suppliers and warehouses.
        Deterministic: built from product_360 and the sales-order allocation, no language model."""
        p = self.product_360(material)
        as_of = self.sap.as_of
        dcs, comps, resupply = p["warehouses"], p["resupply"]["components"], p["resupply"]
        safety = p["safety_stock"]
        sales_daily = sum(d["forecast_14d"] for d in dcs) / 14 or 1.0
        in_transit = sum(d["in_transit"] for d in dcs)
        planned = sum(d["from_planned_production"] for d in dcs)
        reserve = sum(max(0.0, d["on_hand"] - safety) for d in dcs)
        open_orders = p["sales"]["open_order_quantity"]
        rank = {"critical": 0, "warning": 1, "info": 2}
        issues: list[dict] = []

        unit_cost = float(p["unit_cost"])
        exposure = {s["supplier"]: s["open_po_exposure_eur"] for s in self.supplier_scorecard()["suppliers"]}

        def add(severity, area, issue, impact, fix, kind, label, at_risk=None, fix_cost=None, **params):
            # at_risk_eur: value (at standard cost) of demand or supply that is not covered; fix_cost_eur: direct cost of the proposed fix
            issues.append({"severity": severity, "area": area, "issue": issue, "impact": impact, "fix": fix,
                           "at_risk_eur": round(at_risk, 0) if at_risk is not None else None, "fix_cost_eur": round(fix_cost, 0) if fix_cost is not None else None,
                           "action": {"kind": kind, "label": label, "params": {"material": material, **params}}})

        # 1. Warehouses running out or dropping below safety stock
        for d in dcs:
            if not (d["stockout_date"] or d["below_safety_date"]):
                continue
            days = d["days_to_stockout"]
            below_in = (date.fromisoformat(d["below_safety_date"]) - as_of).days if d["below_safety_date"] else None
            severity = "critical" if days is not None and days <= 14 else "warning" if (days is not None and days <= 30) or (below_in is not None and below_in <= 14) else "info"
            what = (f"{d['name']} runs out on {d['stockout_date']} (in {days} days)" if days is not None
                    else f"{d['name']} drops below safety stock on {d['below_safety_date']}")
            donor = d.get("best_donor")
            if donor:
                fix = (f"Transfer {donor['quantity']:,.0f} units from {donor['from']} — arrives {donor['arrives']}"
                       f"{' before the stock-out' if donor['in_time'] else ' (after the stock-out: also pull production forward)'} · €{donor['estimated_cost']:,.0f}")
            else:
                fix = "No warehouse has spare stock within 14 days — pull planned production forward for this DC"
            add(severity, "Stock", what, f"{d['on_hand']:,.0f} on hand · {d['daily_demand']:,.0f}/day demand · {d['open_sales_orders']:,.0f} on open orders",
                fix, "stock_balance", "Plan transfer" if donor else "Rebalance stock", at_risk=max(0.0, -d["surplus_14d"]) * unit_cost,
                fix_cost=donor["estimated_cost"] if donor else None, warehouse=d["warehouse"])

        # 2. Customer orders that cannot be served in full
        for o in self.sales_order_fulfilment()["orders"]:
            if o["material"] != material or o["status"] == "on_track":
                continue
            res = o.get("resolution") or {}
            if o["status"] == "at_risk":
                fix = (f"Transfer {res['quantity']:,.0f} from {res['from']} (arrives {res['arrives']}, €{res['estimated_cost']:,.0f})" if res.get("action") == "stock_transfer"
                       else f"Agree a partial delivery of {res.get('deliverable_now', 0):,.0f} now with {o['customer']}; the rest from the next production")
                add("critical" if o["priority"] == "high" else "warning", "Sales orders", f"Order {o['order']} for {o['customer']} is short by {o['shortfall']:,.0f} units",
                    f"{float(o['quantity']):,.0f} ordered at {o['warehouse']} · due {o['requested_date']}", fix, "sales_orders", "Open order",
                    at_risk=float(o["shortfall"]) * unit_cost, fix_cost=res.get("estimated_cost"))
            else:
                add("info", "Sales orders", f"Order {o['order']} for {o['customer']} depends on stock in transit",
                    f"{float(o['quantity']):,.0f} at {o['warehouse']} · due {o['requested_date']}", "Track the inbound shipment; no action unless it slips", "sales_orders", "Open order")

        # 3. Components (MRP netting against planned production)
        builds = resupply["builds"]
        first_build = builds[0] if builds else None
        def qty(value, uom):
            return f"{math.ceil(value):,} {uom}" if uom == "EA" else f"{value:,.1f} {uom}"

        def when(day):
            return "now" if not day or date.fromisoformat(day) <= as_of else day

        def by(day):
            return "now" if when(day) == "now" else f"by {day}"

        for c in comps:
            if c["status"] in ("covered", "plan"):
                continue
            best = c["best_suppliers"][0]["supplier"] if c["best_suppliers"] else "the approved supplier"
            alt = f"; or use secondary source {c['alternative_sources'][0]}" if c["alternative_sources"] else ""
            pos = ", ".join(c["expedite_candidates"] or c["purchase_orders"]) or "a new purchase order"
            if c["status"] == "late":
                severity, what = "critical", f"{c['description']} short by {qty(c['shortfall'], c['uom'])}, needed {when(c['first_shortage_date'])}"
                fix = (f"Expedite {pos} with {best}" if c["expedite_candidates"] or c["purchase_orders"] else f"Place an urgent order for {qty(c['shortfall'], c['uom'])} with {best}") + alt
            elif c["status"] == "timing_gap":
                severity, what = "warning", f"{c['description']}: confirmed supply arrives after the need date ({'needed now' if when(c['first_shortage_date']) == 'now' else c['first_shortage_date']})"
                fix = f"Expedite {pos} with {best}" + (" for immediate delivery" if when(c["first_shortage_date"]) == "now" else f" to arrive before {c['first_shortage_date']}")
            elif c["status"] == "order_this_week":
                severity, what = "warning", f"{c['description']} short by {qty(c['shortfall'], c['uom'])}"
                fix = f"Order {qty(c['shortfall'], c['uom'])} from {best} {by(c['order_by'])}{alt}"
            else:  # replenish_safety_stock
                severity, what = "info", f"{c['description']} below its safety stock after planned production"
                fix = f"Reorder {qty(c['shortfall'], c['uom'])} from {best}" + (f" {by(c['order_by'])}" if c["order_by"] else "")
            impact = f"{c['component']} · need {qty(c['requirement_total'], c['uom'])} · on hand {qty(c['on_hand'], c['uom'])} · confirmed inbound {qty(c['confirmed_inbound'], c['uom'])}"
            if first_build:
                add(severity, "Components", what, impact, fix, "factory_readiness", "Check readiness", at_risk=c["shortfall"] * float(self.sap.material(c["component"])["unit_cost"]),
                    plant=p["producing_plant"],
                    quantity=int(first_build["quantity"]), need_by=first_build["finish_date"])
            else:
                add(severity, "Components", what, impact, fix, "supplier", "Review supplier", at_risk=c["shortfall"] * float(self.sap.material(c["component"])["unit_cost"]),
                    supplier=best)

        # 4. Production capacity vs the 30-day network need
        if resupply["additional_production_needed"]:
            proposed = next(b for b in builds if b["order"] == "proposed")
            add("warning", "Production", f"Planned production covers {resupply['planned_quantity']:,.0f} of the {resupply['network_need_30d']:,.0f}-unit 30-day need",
                f"gap {resupply['additional_production_needed']:,.0f} units across the network",
                f"Add a production order of {proposed['quantity']:,.0f} at {p['producing_plant']}, finishing by {proposed['finish_date']}",
                "factory_readiness", "Check readiness", at_risk=resupply["additional_production_needed"] * unit_cost,
                plant=p["producing_plant"], quantity=int(proposed["quantity"]), need_by=proposed["finish_date"])

        # 5. High-risk component suppliers, with the recommended source for the same component
        recommended = {o["material"]: o for o in p["supply_options"] if o["recommended"]}
        seen = set()
        for c in comps:
            for s in c["best_suppliers"]:
                if s["risk_rating"] != "high" or s["supplier"] in seen:
                    continue
                seen.add(s["supplier"])
                rec = recommended.get(c["component"])
                fix = (f"Shift volume to {rec['supplier']} ({rec['time_to_deliver_days']} d, {rec['cost_premium_pct']}% cost premium)"
                       if rec and rec["supplier"] != s["supplier"] else "Hold extra safety stock and qualify a second source")
                add("warning", "Suppliers", f"{s['supplier']} is a high continuity risk for {c['description']}",
                    f"OTIF {s['otif_pct']}% · effective lead time {s['effective_lead_time_days']} d vs {s['contract_lead_time_days']} d contract", fix,
                    "supplier", "Review supplier", at_risk=exposure.get(s["supplier"]), supplier=s["supplier"])

        issues.sort(key=lambda i: rank[i["severity"]])
        counts = {k: sum(i["severity"] == k for i in issues) for k in rank}
        first = p["first_stockout"]
        days_out = (date.fromisoformat(first) - as_of).days if first else None
        worst = min((d for d in dcs if d["days_to_stockout"] is not None), key=lambda d: d["days_to_stockout"], default=None)
        status = "critical" if counts["critical"] else "warning" if counts["warning"] else "good"

        def level(row):  # same thresholds as the stock issues above, so ranking, chart and issue list agree
            days, below = row["days_to_stockout"], row["below_safety_date"]
            below_in = (date.fromisoformat(below) - as_of).days if below else None
            return ("critical" if days is not None and days <= 14 else "warning" if (days is not None and days <= 30) or (below_in is not None and below_in <= 14)
                    else "info" if days is not None or below else "good")
        for row in p["warehouse_ranking"]:
            row["health"] = level(row)
        for d in dcs:
            d["health"] = level(d)
        headline = (issues[0]["issue"] + ". Fix: " + issues[0]["fix"]) if issues and status != "good" else "Supply is on track: no stock-out within 60 days and every component is covered."
        return {
            "material": material, "description": p["description"], "producing_plant": p["producing_plant"], "as_of": as_of.isoformat(),
            "status": status, "headline": headline, "issue_counts": counts,
            "supply": {"on_hand": p["network_on_hand"], "in_transit": in_transit, "from_planned_production": round(planned, 0),
                       "open_sales_orders": open_orders, "available_after_orders": round(p["network_on_hand"] - open_orders, 0),
                       "daily_sales_forecast": round(sales_daily, 1), "days_of_cover": round(p["network_on_hand"] / sales_daily, 1)},
            "reserve": {"safety_stock_per_dc": safety, "safety_stock_total": safety * len(dcs), "units_above_safety": round(reserve, 0),
                        "days": round(reserve / sales_daily, 1),
                        "status": "critical" if reserve / sales_daily < 7 else "warning" if reserve / sales_daily < 14 else "good"},
            "time_to_out_of_stock": {"days": days_out, "date": first, "warehouse": worst["warehouse"] if worst else None,
                                     "by_warehouse": [{k: d[k] for k in ("warehouse", "name", "on_hand", "days_to_stockout", "stockout_date", "below_safety_date", "sales_days_of_cover", "health")}
                                                      for d in sorted(dcs, key=lambda d: d["days_to_stockout"] if d["days_to_stockout"] is not None else 999)]},
            "issues": issues,
            "top_warehouses": p["warehouse_ranking"],
            "top_suppliers": [{k: o[k] for k in ("supplier", "material", "type", "time_to_deliver_days", "landed_cost_per_unit_eur", "cost_premium_pct", "otif_pct", "risk_rating", "qualified")}
                              for o in sorted(recommended.values(), key=lambda o: o["time_to_deliver_days"])],
        }

    def sales_outlook(self, material: str | None = None, horizon_days: int = 60) -> dict:
        """Current sales rates per product and DC (last 7 / 28 days vs the 14-day forecast) and a calendar of predicted
        stock-out and below-safety dates, with the resupply arrivals that should prevent them."""
        if material:
            self.sap.validate_codes(material=material)
        as_of = self.sap.as_of
        goods = [m for m in self.sap.section("materials") if m["type"] == "FG" and (not material or m["code"] == material)]
        dc_codes = set(self._warehouses())
        rates, events = [], []
        for good in goods:
            p = self.product_360(good["code"], horizon_days=horizon_days)
            for d in p["warehouses"]:
                if not d["daily_demand"]:
                    continue
                history = self.forecast_vs_actuals(good["code"], d["warehouse"])
                actual = [pt["value"] for pt in history["actual"]]
                last7 = sum(actual[-7:]) / len(actual[-7:])
                last28 = sum(actual[-28:]) / len(actual[-28:])
                next14 = d["forecast_14d"] / 14
                trend = round(100 * (last7 / last28 - 1), 1) if last28 else 0.0
                rates.append({"material": good["code"], "description": good["description"], "warehouse": d["warehouse"], "name": d["name"],
                              "last_7d_per_day": round(last7, 1), "last_28d_per_day": round(last28, 1), "forecast_14d_per_day": round(next14, 1),
                              "trend_pct": trend, "trend": "up" if trend > 5 else "down" if trend < -5 else "flat",
                              "sparkline": [round(v, 1) for v in actual[-28:]], "days_to_stockout": d["days_to_stockout"], "on_hand": d["on_hand"]})
                for kind, day in (("stockout", d["stockout_date"]), ("below_safety", d["below_safety_date"])):
                    if day and not (kind == "below_safety" and day == d["stockout_date"]):
                        donor = d.get("best_donor")
                        events.append({"date": day, "kind": kind, "material": good["code"], "description": good["description"], "warehouse": d["warehouse"],
                                       "days_from_today": (date.fromisoformat(day) - as_of).days,
                                       "fix": (f"transfer {donor['quantity']:,.0f} from {donor['from']} (arrives {donor['arrives']})" if donor else "pull production forward")})
            for s in self.sap.section("shipments"):
                if s["material"] == good["code"] and s["status"] in ("in_transit", "planned") and s["to"] in dc_codes:  # resupply only, not customer deliveries
                    eta = date.fromisoformat(s["eta"]) + timedelta(days=int(s.get("delay_days") or 0))
                    events.append({"date": max(eta, as_of).isoformat(), "kind": "arrival", "material": good["code"], "description": good["description"],
                                   "warehouse": s["to"], "days_from_today": max(0, (eta - as_of).days),
                                   "fix": f"shipment {s['shipment']}: {float(s['quantity']):,.0f} units{' (delayed ' + str(s['delay_days']) + ' d)' if s.get('delay_days') else ''}"})
            for o in self.sap.section("production_orders"):
                if o["material"] == good["code"]:
                    lands = date.fromisoformat(o["finish_date"]) + timedelta(days=3)
                    events.append({"date": max(lands, as_of).isoformat(), "kind": "production", "material": good["code"], "description": good["description"],
                                   "warehouse": "all DCs", "days_from_today": max(0, (lands - as_of).days),
                                   "fix": f"production order {o['order']}: {float(o['quantity']):,.0f} units from {o['plant']}"})
        events = [e for e in events if e["days_from_today"] <= horizon_days]
        order = {"stockout": 0, "below_safety": 1, "arrival": 2, "production": 3}
        events.sort(key=lambda e: (e["date"], order[e["kind"]], e["material"], e["warehouse"]))
        return {"as_of": as_of.isoformat(), "horizon_days": horizon_days,
                "end": (as_of + timedelta(days=horizon_days)).isoformat(),
                "sales_rates": sorted(rates, key=lambda r: (r["days_to_stockout"] if r["days_to_stockout"] is not None else 999, r["material"])),
                "calendar": events,
                "model_scope": "sales history is synthetic POC data; replace with approved SAP billing history before production"}

    # --------------------------------------------------- 12. warehouse / site 360
    def sites(self) -> list[dict]:
        out = []
        for plant in self.sap.section("plants"):
            positions = [r for r in self.position_health() if r["location"] == plant["code"]]
            primary = next((c for c in plant.get("contacts", []) if c.get("primary")), None)
            out.append({"code": plant["code"], "name": plant["name"], "type": plant["type"], "country": plant["country"],
                        "manager": primary, "stock_value_eur": round(sum(r["stock_value_eur"] for r in positions), 2),
                        "below_target": sum(r["shortfall"] > 0 for r in positions), "positions": len(positions)})
        return out

    def site_360(self, code: str) -> dict:
        self.sap.validate_codes(plant=code)
        plant = next(p for p in self.sap.section("plants") if p["code"] == code)
        is_dc = plant["type"] == "warehouse"
        positions = [r for r in self.position_health() if r["location"] == code]
        logistics = self.logistics_status()
        inbound = [s for s in logistics["shipments"] if s["to"] == code]
        outbound = [s for s in logistics["shipments"] if s["from"] == code]
        counts = [c for c in self.stocktake_reconciliation()["counts"] if c["plant"] == code]
        expiry = [r for r in self.expiry_risk(180) if r["plant"] == code]
        lanes = [lane for lane in self.sap.section("lanes") if code in (lane["from"], lane["to"])]
        accurate = sum(c["status"] in ("matched", "within_tolerance") for c in counts)
        site = {k: plant.get(k) for k in ("code", "name", "type", "country", "address", "timezone", "operating_hours", "contacts", "contacts_note")}
        base = {"site": site, "as_of": self.sap.as_of.isoformat(), "positions": positions, "inbound_shipments": inbound, "outbound_shipments": outbound,
                "stocktake": counts, "expiry": expiry, "lanes": lanes}
        if is_dc:
            products, transfers = [], []
            for good in (m for m in self.sap.section("materials") if m["type"] == "FG"):
                p = self.product_360(good["code"])
                d = next(w for w in p["warehouses"] if w["warehouse"] == code)
                rank = next(r["rank"] for r in p["warehouse_ranking"] if r["warehouse"] == code)
                products.append({"material": good["code"], "description": good["description"], "rank_in_network": rank, "network_dcs": len(p["warehouses"]),
                                 **{k: d[k] for k in ("on_hand", "in_transit", "from_planned_production", "daily_demand", "sales_days_of_cover", "days_to_stockout",
                                                      "stockout_date", "below_safety_date", "surplus_14d", "health", "best_donor")}})
                for t in self.stock_balance(good["code"])["proposed_actions"]:
                    if code in (t["from"], t["to"]):
                        transfers.append({**t, "material": good["code"], "direction": "in" if t["to"] == code else "out"})
            orders = [o for o in self.sales_order_fulfilment()["orders"] if o["warehouse"] == code]
            soonest = min((p for p in products if p["days_to_stockout"] is not None), key=lambda p: p["days_to_stockout"], default=None)
            ordered = sum(float(o["quantity"]) for o in orders)
            kpis = [
                {"label": "Stock on hand", "value": sum(p["on_hand"] for p in products), "status": "info", "hint": f"{len(products)} finished goods"},
                {"label": "Stock value", "value": round(sum(r["stock_value_eur"] for r in positions)), "unit": "€", "status": "info"},
                {"label": "Products at risk (≤ 14 d)", "value": sum(1 for p in products if p["days_to_stockout"] is not None and p["days_to_stockout"] <= 14),
                 "status": "critical" if soonest and soonest["days_to_stockout"] <= 14 else "good"},
                {"label": "First out-of-stock in", "value": soonest["days_to_stockout"] if soonest else None, "unit": " d",
                 "status": "critical" if soonest and soonest["days_to_stockout"] <= 7 else "warning" if soonest else "good",
                 "hint": f"{soonest['material']} on {soonest['stockout_date']}" if soonest else "none within 60 days"},
                {"label": "Open sales orders", "value": len(orders), "status": "info", "hint": f"{ordered:,.0f} units"},
                {"label": "Order fill rate", "value": round(100 * sum(float(o["confirmed"]) for o in orders) / ordered, 1) if ordered else 100.0, "unit": "%",
                 "status": "good" if all(o["status"] == "on_track" for o in orders) else "warning"},
                {"label": "Inbound shipments", "value": len(inbound), "status": "warning" if any(s.get("delay_days") for s in inbound) else "info",
                 "hint": f"{sum(1 for s in inbound if s.get('delay_days'))} delayed"},
                {"label": "Count accuracy", "value": round(100 * accurate / len(counts), 1) if counts else None, "unit": "%", "status": "warning" if counts and accurate < len(counts) else "good",
                 "hint": f"{len(counts)} counts"},
                {"label": "Expiring ≤ 180 days", "value": round(sum(r["value_eur"] for r in expiry)), "unit": "€", "status": "warning" if expiry else "good"},
            ]
            return {**base, "kind": "warehouse", "kpis": kpis, "products": products, "sales_orders": orders, "transfers": transfers}
        orders = [o for o in self.production_overview()["orders"] if o["plant"] == code]
        quality = [lot for lot in self.sap.section("quality_lots") if lot["plant"] == code]
        open_pos = [po for po in self.sap.section("purchase_orders") if po["plant"] == code]
        kpis = [
            {"label": "Components below target", "value": sum(r["shortfall"] > 0 for r in positions), "status": "warning", "hint": f"of {len(positions)} stocked components"},
            {"label": "Stock value", "value": round(sum(r["stock_value_eur"] for r in positions)), "unit": "€", "status": "info"},
            {"label": "Production orders", "value": len(orders), "status": "info", "hint": f"{sum(o['quantity'] for o in orders):,.0f} units"},
            {"label": "Not ready / at risk", "value": sum(o["readiness"] != "ready" for o in orders), "status": "critical" if any(o["readiness"] != "ready" for o in orders) else "good"},
            {"label": "Lots in QM / blocked", "value": sum(lot["status"] in ("inspection", "blocked") for lot in quality), "status": "warning"},
            {"label": "Open purchase orders", "value": len(open_pos), "status": "info", "hint": f"{sum(po.get('status') != 'confirmed' for po in open_pos)} unconfirmed"},
            {"label": "Count accuracy", "value": round(100 * accurate / len(counts), 1) if counts else None, "unit": "%", "status": "warning" if counts and accurate < len(counts) else "good"},
            {"label": "Expiring ≤ 180 days", "value": round(sum(r["value_eur"] for r in expiry)), "unit": "€", "status": "warning" if expiry else "good"},
        ]
        return {**base, "kind": "plant", "kpis": kpis, "production_orders": orders, "quality_lots": quality, "purchase_orders": open_pos}

    # --------------------------------------------------- 13. network map & supplier geography
    @staticmethod
    def supplier_tier(supplier_country: str, supplier_zone: str, plant: dict) -> str:
        """local = same country as the plant; regional = same geographic zone; international = otherwise."""
        if supplier_country == plant["country"]:
            return "local"
        return "regional" if supplier_zone == plant.get("zone") else "international"

    def network_map(self) -> dict:
        plants = {p["code"]: p for p in self.sap.section("plants")}
        bom = self.sap.section("bom")
        scorecard = {s["supplier"]: s for s in self.supplier_scorecard()["suppliers"]}
        site_rows = {s["code"]: s for s in self.sites()}
        sites = [{**{k: p.get(k) for k in ("code", "name", "type", "lat", "lon", "city", "country", "zone")},
                  "stock_value_eur": site_rows[p["code"]]["stock_value_eur"], "below_target": site_rows[p["code"]]["below_target"],
                  "manager": site_rows[p["code"]]["manager"]} for p in plants.values()]
        suppliers, flows = [], []
        price = {s["name"]: s.get("unit_price_eur") for s in self.sap.section("suppliers")}
        for s in self.sap.section("suppliers"):
            sc = scorecard[s["name"]]
            serves = sorted({b["plant"] for b in bom if b["component"] in s["materials"]})
            country, zone = s.get("manufacturing_country", s["country"]), s.get("zone")
            served = [{"plant": code, "tier": self.supplier_tier(country, zone, plants[code])} for code in serves]
            learned = round(s["contract_lead_time_days"] + (sc["average_delay_days"] or 0), 1)
            suppliers.append({"name": s["name"], "code": s["code"], "lat": s.get("lat"), "lon": s.get("lon"), "city": s.get("city"), "country": country,
                              "zone": zone, "manufacturing_site": s.get("manufacturing_site"), "materials": s["materials"], "risk_rating": sc["risk_rating"],
                              "risk_score": sc["risk_score"], "otif_pct": sc["otif_pct"], "sap_lead_time_days": s["contract_lead_time_days"],
                              "learned_time_to_deliver_days": learned, "learned_vs_sap_days": round(learned - s["contract_lead_time_days"], 1),
                              "single_source": sc["single_source"], "serves": served,
                              "worst_tier": max((x["tier"] for x in served), key=["local", "regional", "international"].index, default="regional")})
            for x in served:
                p = plants[x["plant"]]
                flows.append({"kind": "supply", "tier": x["tier"], "status": sc["risk_rating"], "from": [s.get("lat"), s.get("lon")], "to": [p.get("lat"), p.get("lon")],
                              "label": f"{s['name']} → {x['plant']} · {', '.join(m for m in s['materials'])} · {x['tier']} · actual {learned} d vs SAP {s['contract_lead_time_days']} d"})
        alternatives = [q for q in (self.sap.section("supplier_quotes") if self.sap.has("supplier_quotes") else []) if q.get("lat") is not None]
        origins = self.sap.section("ingredient_origins") if self.sap.has("ingredient_origins") else []
        by_name = {s["name"]: s for s in suppliers}
        for o in origins:
            target = by_name.get(o["feeds_supplier"])
            if target:
                flows.append({"kind": "tier2", "tier": "international", "status": o["criticality"], "from": [o["lat"], o["lon"]], "to": [target["lat"], target["lon"]],
                              "label": f"{o['ingredient']} ({o['origin']}) → {o['feeds_supplier']} · {o['transit_days']}±{o['transit_variability_days']} d"})
        for factory in (p for p in plants.values() if p["type"] != "warehouse"):
            for dc in (p for p in plants.values() if p["type"] == "warehouse"):
                flows.append({"kind": "distribution", "tier": None, "status": "info", "from": [factory.get("lat"), factory.get("lon")], "to": [dc.get("lat"), dc.get("lon")],
                              "label": f"{factory['code']} → {dc['code']} finished goods"})
        for lane in self.sap.section("lanes"):
            if lane["from"] < lane["to"]:
                a, b = plants[lane["from"]], plants[lane["to"]]
                flows.append({"kind": "lane", "tier": None, "status": "info", "from": [a.get("lat"), a.get("lon")], "to": [b.get("lat"), b.get("lon")],
                              "label": f"{lane['from']} ↔ {lane['to']} · {lane['lead_days']} d · €{lane['cost_per_unit']}/unit"})
        codes = {s["code"]: s for s in self.sap.section("suppliers")}
        for sh in self.logistics_status()["shipments"]:
            src = plants.get(sh["from"]) or codes.get(sh["from"])
            dst = plants.get(sh["to"])
            if src and dst and sh["status"] in ("in_transit", "planned"):
                late = f" · {sh['delay_days']} d late" if sh.get("delay_days") else ""
                flows.append({"kind": "shipment", "tier": None, "status": "critical" if sh["escalate"] else "warning" if sh.get("delay_days") else "good",
                              "from": [src.get("lat"), src.get("lon")], "to": [dst.get("lat"), dst.get("lon")],
                              "label": f"{sh['shipment']} {sh['quantity']:,.0f} {sh['material']} via {sh['carrier']} · ETA {sh['revised_eta']}{late}"})

        # L'Oréal-style sourcing KPI per factory: share of spend (open + last 6 months of POs) by supplier tier
        spend: dict[str, dict[str, float]] = {}
        po_rows = [(po["supplier"], po["plant"], float(po["quantity"])) for po in self.sap.section("purchase_orders")]
        for h in self.sap.section("po_history"):
            plants_using = sorted({b["plant"] for b in bom if b["component"] == h["material"]})
            for code in plants_using:
                po_rows.append((h["supplier"], code, float(h["quantity_ordered"]) / len(plants_using)))
        tier_of = {(s["name"], x["plant"]): x["tier"] for s in suppliers for x in s["serves"]}
        for supplier, plant_code, qty in po_rows:
            tier = tier_of.get((supplier, plant_code)) or self.supplier_tier(by_name[supplier]["country"], by_name[supplier]["zone"], plants[plant_code])
            spend.setdefault(plant_code, {}).setdefault(tier, 0.0)
            spend[plant_code][tier] += qty * float(price.get(supplier) or 0)
        factory_sourcing = []
        for code, tiers in sorted(spend.items()):
            total = sum(tiers.values()) or 1
            factory_sourcing.append({"plant": code, "name": plants[code]["name"], "zone": plants[code].get("zone"), "spend_eur": round(total, 2),
                                     **{f"{t}_pct": round(100 * tiers.get(t, 0) / total, 1) for t in ("local", "regional", "international")},
                                     "within_zone_pct": round(100 * (tiers.get("local", 0) + tiers.get("regional", 0)) / total, 1)})
        tier_summary = []
        for tier in ("local", "regional", "international"):
            group = [s for s in suppliers if s["worst_tier"] == tier]
            tier_summary.append({"tier": tier, "suppliers": len(group), "names": [s["name"] for s in group],
                                 "avg_learned_time_to_deliver_days": round(sum(s["learned_time_to_deliver_days"] for s in group) / len(group), 1) if group else None,
                                 "avg_otif_pct": round(sum(s["otif_pct"] or 0 for s in group) / len(group), 1) if group else None,
                                 "avg_delay_vs_sap_days": round(sum(s["learned_vs_sap_days"] for s in group) / len(group), 1) if group else None})
        return {"as_of": self.sap.as_of.isoformat(), "sites": sites, "suppliers": suppliers, "alternatives": alternatives, "origins": origins, "flows": flows,
                "factory_sourcing": factory_sourcing, "tier_summary": tier_summary,
                "reference": self.sap.section("sourcing_reference") if self.sap.has("sourcing_reference") else None}

    def expiry_risk(self, within_days: int = 180) -> list[dict]:
        rows = []
        for row in self.sap.section("stock"):
            if not row.get("expiry"):
                continue
            days_left = (date.fromisoformat(row["expiry"]) - self.sap.as_of).days
            if days_left <= within_days:
                cost = float(self.sap.material(row["material"])["unit_cost"])
                rows.append({**row, "days_left": days_left, "value_eur": round(float(row["quantity"]) * cost, 2),
                             "state": "expired" if days_left < 0 else "critical" if days_left <= 90 else "warning"})
        return sorted(rows, key=lambda r: r["days_left"])

    def kpis(self) -> dict:
        warehouses = self._warehouses()
        finished_goods = [row for row in self.sap.section("materials") if row["type"] == "FG"]
        inventory_value = 0.0
        risks = []
        for material in finished_goods:
            for warehouse in warehouses:
                qty = self.sap.on_hand(warehouse, material["code"])
                inventory_value += qty * float(material["unit_cost"])
                demand = self.sap.section("warehouse_demand_daily")[material["code"]][warehouse]
                cover = qty / demand
                if cover < 7:
                    risks.append({"severity": "high" if cover < 4 else "medium", "warehouse": warehouse, "material": material["code"], "days_of_cover": round(cover, 1)})
        lots = self.sap.section("quality_lots")
        return {
            "as_of": self.sap.as_of.isoformat(),
            "inventory_value": round(inventory_value, 2),
            "at_risk_positions": risks,
            "at_risk_count": len(risks),
            "open_purchase_orders": len(self.sap.section("purchase_orders")),
            "open_production_orders": len(self.sap.section("production_orders")),
            "quality_lots_open": sum(1 for lot in lots if lot["status"] in ("inspection", "blocked")),
            "shipments_delayed": sum(1 for s in self.sap.section("shipments") if s.get("delay_days")),
            "suppliers": len(self.sap.section("suppliers")),
            "currency": "EUR",
        }
