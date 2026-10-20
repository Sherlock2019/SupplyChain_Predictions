"""Automatic insights in plain English and personalised watches (subscriptions).

Deterministic by construction: every insight is computed from the SAP snapshot by the engine, carries its evidence,
and the same snapshot always yields the same insights. No LLM is involved, so nothing here can hallucinate.
"""
from __future__ import annotations

import hashlib

from backend.app.engine import SupplyChainEngine

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "good": 3}


def _id(*parts) -> str:
    return "IN-" + hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:10]


class InsightEngine:
    def __init__(self, engine: SupplyChainEngine):
        self.engine = engine
        self.sap = engine.sap

    def _plant(self, code: str) -> str:
        return next((p["name"] for p in self.sap.section("plants") if p["code"] == code), code)

    def _mat(self, code: str) -> str:
        return next((m["description"] for m in self.sap.section("materials") if m["code"] == code), code)

    def insights(self) -> list[dict]:
        out: list[dict] = []
        add = out.append

        # Stock-out and overstock risk by warehouse position
        for p in self.engine.inventory_overview()["positions"]:
            cover, wh, mat = p["days_of_cover"], p["warehouse"], p["material"]
            evidence = [{"label": "On hand", "value": p["on_hand"]}, {"label": "Daily demand", "value": p["daily_demand"]},
                        {"label": "Open sales orders", "value": p["open_sales_orders"]}, {"label": "In transit (14 d)", "value": p["in_transit_14d"]},
                        {"label": "Source", "value": f"SAP snapshot {self.sap.snapshot['id']} · A_MaterialStock, A_SalesOrderItem, A_Shipment"}]
            if cover < 7:
                add({"id": _id("stockout", wh, mat), "severity": "critical" if cover < 4 else "warning", "category": "Inventory",
                     "title": f"{self._plant(wh)} has about {cover:g} days of {self._mat(mat)} left",
                     "detail": f"{p['on_hand']:,.0f} units on hand against {p['daily_demand']:,.0f}/day demand and {p['open_sales_orders']:,.0f} units "
                               f"on open sales orders; {p['in_transit_14d']:,.0f} units are in transit.",
                     "metric": {"label": "days of cover", "value": cover}, "evidence": evidence,
                     "action": {"label": "Rebalance stock", "kind": "stock_balance", "params": {"material": mat, "warehouse": wh}},
                     "ask": f"How should we rebalance {mat} to protect {wh}?"})
            elif cover > 30:
                add({"id": _id("overstock", wh, mat), "severity": "info", "category": "Inventory",
                     "title": f"{self._plant(wh)} holds {cover:g} days of {self._mat(mat)} — a likely transfer donor",
                     "detail": f"{p['on_hand']:,.0f} units on hand for {p['daily_demand']:,.0f}/day demand.",
                     "metric": {"label": "days of cover", "value": cover}, "evidence": evidence,
                     "action": {"label": "Rebalance stock", "kind": "stock_balance", "params": {"material": mat, "warehouse": wh}},
                     "ask": f"Can {wh} supply other DCs with {mat}?"})

        # Sales orders
        for o in self.engine.sales_order_fulfilment()["orders"]:
            if o["status"] == "on_track":
                continue
            fix = o["resolution"] or {}
            fix_text = (f" Fix: transfer {fix['quantity']:,.0f} from {fix['from']} (arrives {fix['arrives']}, €{fix['estimated_cost']:,.0f})."
                        if fix.get("action") == "stock_transfer" else " No DC can cover it in time — propose a partial delivery." if fix else "")
            add({"id": _id("so", o["order"]), "severity": "critical" if o["status"] == "at_risk" else "warning", "category": "Sales orders",
                 "title": (f"Order {o['order']} for {o['customer']} is short by {o['shortfall']:,.0f} units" if o["status"] == "at_risk"
                           else f"Order {o['order']} for {o['customer']} depends on stock still in transit"),
                 "detail": f"{o['quantity']:,.0f} × {self._mat(o['material'])} from {o['warehouse']} due {o['requested_date']} ({o['priority']} priority); "
                           f"{o['available_by_due_date']:,.0f} available by then.{fix_text}",
                 "metric": {"label": "shortfall", "value": o["shortfall"]},
                 "evidence": [{"label": "Sales order", "value": o["order"]}, {"label": "Requested", "value": o["requested_date"]},
                              {"label": "Confirmed", "value": o["confirmed"]}, {"label": "Source", "value": "A_SalesOrderItem, A_MaterialStock, A_Shipment, A_TransportLane"}],
                 "action": {"label": "Plan fulfilment", "kind": "sales_orders", "params": {}},
                 "ask": f"How do we fulfil sales order {o['order']} on time?"})

        # Production readiness
        for o in self.engine.production_overview()["orders"]:
            if o["readiness"] == "ready":
                continue
            add({"id": _id("prod", o["order"]), "severity": "critical" if o["readiness"] == "not_ready" else "warning", "category": "Production",
                 "title": f"Production order {o['order']} ({self._mat(o['material'])}, {self._plant(o['plant'])}) is {o['readiness'].replace('_', ' ')}",
                 "detail": f"{o['quantity']:,.0f} units due {o['finish_date']}; short: {', '.join(o['short_components'])}. "
                           f"{o['component_readiness_pct']}% of components are covered.",
                 "metric": {"label": "components covered", "value": f"{o['component_readiness_pct']}%"},
                 "evidence": [{"label": "Order", "value": o["order"]}, {"label": "Short components", "value": ", ".join(o["short_components"])},
                              {"label": "Rule", "value": "SOP SC-104: unrestricted stock + confirmed POs by need date"}],
                 "action": {"label": "Check readiness", "kind": "factory_readiness",
                            "params": {"plant": o["plant"], "material": o["material"], "quantity": o["quantity"], "need_by": o["finish_date"]}},
                 "ask": f"Can {o['plant']} produce {o['quantity']:g} {o['material']} by {o['finish_date']}?"})

        # Suppliers
        for s in self.engine.supplier_scorecard()["suppliers"]:
            if s["risk_rating"] != "high":
                continue
            add({"id": _id("supplier", s["supplier"]), "severity": "warning", "category": "Suppliers",
                 "title": f"{s['supplier']} is a high continuity risk",
                 "detail": f"OTIF {s['otif_pct']}%, average delay {s['average_delay_days']} days, rejects {s['quality_reject_pct']}%"
                           f"{', single source' if s['single_source'] else ''}; €{s['open_po_exposure_eur']:,.0f} open PO exposure.",
                 "metric": {"label": "risk score", "value": s["risk_score"]},
                 "evidence": [{"label": "OTIF", "value": f"{s['otif_pct']}%"}, {"label": "Reject rate", "value": f"{s['quality_reject_pct']}%"},
                              {"label": "Source", "value": "A_PurchaseOrderHistory, A_InspectionLot, supplier contracts"}],
                 "action": {"label": "Research supplier", "kind": "supplier", "params": {"supplier": s["supplier"]}},
                 "ask": f"Is {s['supplier']} a continuity risk? Cite the contract."})

        # Logistics
        for s in self.engine.logistics_status()["shipments"]:
            if s.get("escalate"):
                add({"id": _id("ship", s["shipment"]), "severity": "warning", "category": "Logistics",
                     "title": f"Shipment {s['shipment']} to {s['to']} is {s['delay_days']} days late",
                     "detail": f"{s['quantity']:,.0f} × {self._mat(s['material'])} via {s['carrier']} ({s['mode']}); revised ETA {s['revised_eta']}. "
                               f"Reason: {s['delay_reason']}.",
                     "metric": {"label": "days late", "value": s["delay_days"]},
                     "evidence": [{"label": "Carrier SLA policy", "value": "LP-05: delays above SLA trigger a claim review"}],
                     "action": {"label": "View shipments", "kind": "suppliers", "params": {}},
                     "ask": f"What is the impact of the delay on shipment {s['shipment']}?"})

        # Stocktake
        for c in self.engine.stocktake_reconciliation()["counts"]:
            if c["status"] in ("matched",):
                continue
            sev = "warning" if c["status"] == "investigate" else "info"
            why = "; ".join(f"{e['type'].replace('_', ' ')} {e['document']} ({e['quantity']:+g})" for e in c["evidence"]) or "no movement explains it"
            add({"id": _id("count", c["count_id"]), "severity": sev, "category": "Stocktake",
                 "title": f"Count difference of {c['difference']:+g} for {c['material']} at {c['plant']} — {c['status'].replace('_', ' ')}",
                 "detail": f"Book {c['book_quantity']:,.0f}, counted {c['counted_quantity']:,.0f} (€{c['difference_value_eur']:,.0f}). Explanation: {why}.",
                 "metric": {"label": "unexplained", "value": c["unexplained"]},
                 "evidence": [{"label": "Count", "value": c["count_id"]}] + [{"label": e["type"], "value": f"{e['document']} {e['quantity']:+g}"} for e in c["evidence"]],
                 "action": {"label": "Reconcile", "kind": "stocktake", "params": {}},
                 "ask": f"Why is there a stock count difference for {c['material']} at {c['plant']}?"})

        out.sort(key=lambda i: (SEVERITY_ORDER[i["severity"]], i["category"]))
        return out

    # ------------------------------------------------------------------ watches
    def evaluate(self, kind: str, params: dict, threshold: float) -> dict:
        if kind == "days_of_cover":
            pos = next(p for p in self.engine.inventory_overview(params["material"])["positions"] if p["warehouse"] == params["warehouse"])
            value = pos["days_of_cover"]
            return {"value": value, "triggered": value < threshold, "text": f"{params['warehouse']} {params['material']}: {value:g} days of cover (alert below {threshold:g})"}
        if kind == "supplier_risk":
            risk = self.engine.supplier_risk(params["supplier"])
            value = risk["risk_score"]
            return {"value": value, "triggered": value >= threshold, "text": f"{risk['supplier']['name']}: risk score {value:g} (alert at {threshold:g})"}
        if kind == "sales_orders_at_risk":
            value = self.engine.sales_order_fulfilment(params.get("warehouse") or None)["at_risk"]
            return {"value": value, "triggered": value >= threshold, "text": f"{value} sales order(s) at risk (alert at {threshold:g})"}
        if kind == "stocktake_unexplained":
            value = self.engine.stocktake_reconciliation()["to_investigate"]
            return {"value": value, "triggered": value >= threshold, "text": f"{value} count difference(s) need investigation"}
        if kind == "shipment_delay":
            ships = [s for s in self.engine.logistics_status(params.get("warehouse") or None)["shipments"]]
            value = max((int(s.get("delay_days") or 0) for s in ships), default=0)
            return {"value": value, "triggered": value > threshold, "text": f"longest delay {value} days (alert above {threshold:g})"}
        if kind == "question":
            return {"value": None, "triggered": False, "text": "Saved question — run it with the copilot"}
        raise ValueError(f"Unknown watch kind {kind}")


WATCH_KINDS = {
    "days_of_cover": {"label": "Days of cover below", "params": ["material", "warehouse"], "default": 5},
    "supplier_risk": {"label": "Supplier risk score at least", "params": ["supplier"], "default": 50},
    "sales_orders_at_risk": {"label": "Sales orders at risk at least", "params": [], "default": 1},
    "stocktake_unexplained": {"label": "Unexplained count differences at least", "params": [], "default": 1},
    "shipment_delay": {"label": "Shipment delay above (days)", "params": [], "default": 3},
    "question": {"label": "Saved copilot question", "params": ["question"], "default": 0},
}
