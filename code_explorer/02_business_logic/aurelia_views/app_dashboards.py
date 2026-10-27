# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/dashboards.py
# What this module is: the persona dashboards of the SPARC gateway (GET /api/v1/dashboards/{persona}). Each persona gets KPI tiles,
# charts and tables computed deterministically from the engine, optionally focused on one finished good and its BOM components.
# The front end renders the generic spec: kpis[], charts[{type: bar | diverging | line | stacked}], tables[].
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Role / task dashboards. Each persona gets KPI tiles, charts and tables computed deterministically from the snapshot.

Optional product focus: `build(persona, material)` restricts every persona to one finished good and its BOM components
(and therefore the suppliers, orders, counts and shipments that touch them).

The UI renders the generic spec: kpis[{label,value,unit,status,hint}], charts[{type: bar|diverging|line|stacked, ...}],
tables[{title, columns, rows}]. Charts carry their own unit and a status per bar where it means something.
"""
from __future__ import annotations

import json
# Counter: counts occurrences, e.g. insights per (category, severity).
from collections import Counter

from backend.app.engine import SupplyChainEngine
from backend.app.insights import InsightEngine
from backend.app.store import Store

# Persona catalogue (GET /api/v1/dashboards returns it as is).
PERSONAS = {
    "executive": {"title": "Supply-chain manager", "task": "Service, risk and decisions across the network"},
    "inventory": {"title": "Inventory planner", "task": "Inventory management: avoid stock-outs, minimise overstock"},
    "sales": {"title": "Sales order desk", "task": "Sales order management: fulfil every order on time"},
    "stocktake": {"title": "Warehouse & stocktake control", "task": "Stocktake management: explain every count difference"},
    "procurement": {"title": "Procurement / supplier manager", "task": "Supplier reliability, lead time and quality"},
    "production": {"title": "Production planner", "task": "Material readiness for production orders"},
    "logistics": {"title": "Logistics control tower", "task": "Shipments, delays, lanes and carbon"},
}

# ===== FUNCTION: _status_cover() =====
# ID: F0227 · function · used (framework)
# ORIGINAL FILE: backend/app/dashboards.py:28-31
# ROLE: Colour of a coverage percentage: < 60% critical, < 100% warning, else good.
# INPUTS:
#   pct: float | None.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0233 Dashboards._understock_chart() (calls)
# CALLS:
#   (none found)
def _status_cover(pct: float | None) -> str:
    if pct is None:
        return "info"
    return "critical" if pct < 60 else "warning" if pct < 100 else "good"


# ===== FUNCTION: _in() =====
# ID: F0228 · function · used (framework)
# ORIGINAL FILE: backend/app/dashboards.py:34-35
# ROLE: Is a material code inside the product scope? (scope None = whole network = always True).
# INPUTS:
#   scope: set | None, code: str | None.
# OUTPUT:
#   bool.
# CALLED BY:
#   <- F0236 Dashboards._executive() (calls)
#   <- F0237 Dashboards._inventory() (calls)
#   <- F0238 Dashboards._sales() (calls)
#   <- F0239 Dashboards._stocktake() (calls)
#   <- F0240 Dashboards._procurement() (calls)
#   <- F0241 Dashboards._production() (calls)
#   <- F0242 Dashboards._logistics() (calls)
# CALLS:
#   (none found)
def _in(scope, code: str | None) -> bool:
    return scope is None or code in scope


# ===== CLASS: Dashboards =====
# ID: F0229 · class · used
# ORIGINAL FILE: backend/app/dashboards.py:38-305
# ROLE: Builds persona dashboards for one tenant.
# FIELDS:
#   engine, insights, store.
# CALLED BY:
#   <- F0260 RoleCenter.__init__() (references)
#   <- F2039 TenantRegistry._build() (calls)
# CALLS:
#   (none found)
class Dashboards:
    # ===== FUNCTION: Dashboards.__init__() =====
    # ID: F0230 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:39-40
    # ROLE: Keep the collaborators.
    # INPUTS:
    #   engine: SupplyChainEngine, insights: InsightEngine, store: Store.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0192 SupplyChainEngine (references)
    #   -> F0244 InsightEngine (references)
    #   -> F0354 Store (references)
    def __init__(self, engine: SupplyChainEngine, insights: InsightEngine, store: Store):
        self.engine, self.insights, self.store = engine, insights, store

    # ===== FUNCTION: Dashboards.product_scope() =====
    # ID: F0231 · method · used
    # ORIGINAL FILE: backend/app/dashboards.py:42-49
    # ROLE: The product scope: a finished good plus its BOM components (None = the whole network).
    # INPUTS:
    #   material: str | None.
    # OUTPUT:
    #   set[str] | None (ValueError when the material is not a finished good).
    # CALLED BY:
    #   <- F0232 Dashboards.build() (calls)
    #   <- F0261 RoleCenter._facts() (calls)
    # CALLS:
    #   -> F0410 SapRepository.material() (calls)
    #   -> F0407 SapRepository.section() (calls)
    def product_scope(self, material: str | None) -> set[str] | None:
        """A finished good plus its BOM components; None means the whole network."""
        if not material:
            return None
        master = self.engine.sap.material(material)
        if master["type"] != "FG":
            raise ValueError(f"{material} is not a finished good")
        # Set union of {material} and the set comprehension of its components.
        return {material} | {b["component"] for b in self.engine.sap.section("bom") if b["parent"] == material}

    # ===== FUNCTION: Dashboards.build() =====
    # ID: F0232 · method · used
    # ORIGINAL FILE: backend/app/dashboards.py:51-59
    # ROLE: Build one persona dashboard by dispatching to _<persona>(scope, material).
    # INPUTS:
    #   persona: str (key of PERSONAS), material: str | None.
    # OUTPUT:
    #   dict -> persona, title, task, as_of, product focus, kpis, charts, tables (+ forecast / analysis).
    # CALLED BY:
    #   <- F0065 create_app.dashboard() (calls)
    #   <- F0280 RoleCenter._charts() (calls)
    # CALLS:
    #   -> F0231 Dashboards.product_scope() (calls)
    #   -> F0410 SapRepository.material() (calls)
    def build(self, persona: str, material: str | None = None) -> dict:
        if persona not in PERSONAS:
            raise ValueError(f"Unknown dashboard {persona}. Options: {', '.join(PERSONAS)}")
        scope = self.product_scope(material)
        body = getattr(self, f"_{persona}")(scope, material)
        focus = None
        if material:
            focus = {"material": material, "description": self.engine.sap.material(material)["description"], "scope": sorted(scope)}
        return {"persona": persona, **PERSONAS[persona], "as_of": self.engine.sap.as_of.isoformat(), "product": focus, **body}

    # ----------------------------------------------------------------- shared
    # ===== FUNCTION: Dashboards._understock_chart() =====
    # ID: F0233 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:62-68
    # ROLE: Chart of the 10 most understocked positions (lowest coverage %, then largest shortfall value).
    # INPUTS:
    #   rows: list[dict] (position_health rows), title: str.
    # OUTPUT:
    #   dict -> bar chart spec.
    # CALLED BY:
    #   <- F0236 Dashboards._executive() (calls)
    #   <- F0237 Dashboards._inventory() (calls)
    #   <- F0241 Dashboards._production() (calls)
    # CALLS:
    #   -> F0227 _status_cover() (calls)
    def _understock_chart(self, rows: list[dict], title: str) -> dict:
        top = sorted((r for r in rows if r["shortfall"] > 0), key=lambda r: (r["coverage_pct"] or 0, -r["shortfall_value_eur"]))[:10]
        return {"id": "understock", "type": "bar", "title": title, "subtitle": "available (stock + confirmed inbound, 14 days) as % of target; target = need + safety stock",
                "unit": "%", "reference": 100, "reference_label": "target",
                "rows": [{"label": f"{r['material']} @ {r['location']}", "value": r["coverage_pct"], "status": _status_cover(r["coverage_pct"]),
                          "hint": f"{r['description']}: {r['on_hand']:,.0f} on hand + {r['inbound']:,.0f} inbound vs target {r['target']:,.0f} {r['uom']} · short {r['shortfall']:,.0f} (€{r['shortfall_value_eur']:,.0f})"}
                         for r in top]}

    # ===== FUNCTION: Dashboards._supplier_rows() =====
    # ID: F0234 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:70-79
    # ROLE: Supplier scorecard rows (within scope) enriched with contract / effective lead time, OTIF target and materials.
    # INPUTS:
    #   scope.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0240 Dashboards._procurement() (calls)
    # CALLS:
    #   -> F0202 SupplyChainEngine.supplier_scorecard() (calls)
    #   -> F0411 SapRepository.supplier() (calls)
    def _supplier_rows(self, scope) -> list[dict]:
        rows = []
        for s in self.engine.supplier_scorecard()["suppliers"]:
            master = self.engine.sap.supplier(s["supplier"])
            if scope is not None and not scope & set(master["materials"]):
                continue
            rows.append({**s, "contract_lead_time_days": master["contract_lead_time_days"],
                         "effective_lead_time_days": round(master["contract_lead_time_days"] + (s["average_delay_days"] or 0), 1),
                         "otif_target_pct": master["otif_target_pct"], "materials": ", ".join(master["materials"])})
        return rows

    # ===== FUNCTION: Dashboards._mentions() =====
    # ID: F0235 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:81-86
    # ROLE: Does an insight mention a material of the scope (code or description) anywhere in its text, evidence or action?
    # INPUTS:
    #   insight: dict, scope.
    # OUTPUT:
    #   bool.
    # CALLED BY:
    #   <- F0236 Dashboards._executive() (calls)
    # CALLS:
    #   -> F0410 SapRepository.material() (calls)
    def _mentions(self, insight: dict, scope) -> bool:
        if scope is None:
            return True
        text = insight["title"] + insight["detail"] + json.dumps(insight["evidence"]) + json.dumps(insight["action"])
        names = {self.engine.sap.material(code)["description"] for code in scope}
        return any(token in text for token in scope | names)

    # ------------------------------------------------------------ personas
    # ===== FUNCTION: Dashboards._executive() =====
    # ID: F0236 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:89-120
    # ROLE: Executive dashboard: critical insights, fill rate, value short, expiring stock, decisions waiting / executed; insights by
    #       area, recommendation pipeline, understocked positions; top priorities table.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0248 InsightEngine.insights() (calls)
    #   -> F0235 Dashboards._mentions() (calls)
    #   -> F0210 SupplyChainEngine.position_health() (calls)
    #   -> F0228 _in() (calls)
    #   -> F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   -> F0389 Store.counts() (calls)
    #   -> F0225 SupplyChainEngine.expiry_risk() (calls)
    #   -> F0233 Dashboards._understock_chart() (calls)
    def _executive(self, scope, material) -> dict:
        insights = [i for i in self.insights.insights() if self._mentions(i, scope)]
        positions = [r for r in self.engine.position_health() if _in(scope, r["material"])]
        orders = [o for o in self.engine.sales_order_fulfilment()["orders"] if _in(scope, o["material"])]
        counts = self.store.counts(self.engine.sap.snapshot["id"])["recommendations"]  # this customer only
        qty = sum(float(o["quantity"]) for o in orders)
        fill = 100 * sum(float(o["confirmed"]) for o in orders) / qty if qty else 100
        value_at_risk = sum(r["shortfall_value_eur"] for r in positions)
        expiring = sum(r["value_eur"] for r in self.engine.expiry_risk(90) if _in(scope, r["material"]))
        cats = Counter((i["category"], i["severity"]) for i in insights)
        categories = sorted({c for c, _ in cats})
        return {
            "kpis": [
                {"label": "Critical insights", "value": sum(i["severity"] == "critical" for i in insights), "status": "critical", "hint": "needs action today"},
                {"label": "Order fill rate", "value": round(fill, 1), "unit": "%", "status": "good" if fill >= 98 else "warning", "hint": "confirmed / ordered, open orders"},
                {"label": "Value short vs target", "value": round(value_at_risk), "unit": "€", "status": "warning", "hint": "positions in scope, at cost"},
                {"label": "Stock expiring ≤ 90 days", "value": round(expiring), "unit": "€", "status": "warning" if expiring else "good"},
                {"label": "Awaiting your decision", "value": counts.get("pending_review", 0), "status": "info", "hint": "this customer"},
                {"label": "Executed in SAP sandbox", "value": counts.get("executed", 0), "status": "good", "hint": "this customer"},
            ],
            "charts": [
                {"id": "insights", "type": "stacked", "title": "Open insights by area", "subtitle": "deterministic, from the SAP snapshot",
                 "series": ["critical", "warning", "info"], "status_series": True,
                 "rows": [{"label": c, "segments": [{"name": s, "value": cats.get((c, s), 0)} for s in ("critical", "warning", "info")]} for c in categories]},
                {"id": "decisions", "type": "bar", "title": "Recommendation pipeline", "subtitle": "agent / planner proposals → manager decision → SAP sandbox",
                 "unit": "", "rows": [{"label": s.replace("_", " "), "value": counts.get(s, 0), "status": {"rejected": "critical", "executed": "good"}.get(s, "info")}
                                      for s in ("pending_review", "accepted", "executed", "rejected")]},
                self._understock_chart(positions, "Top 10 understocked positions"),
            ],
            "tables": [{"title": "Top priorities", "columns": ["Severity", "Area", "Insight"],
                        "rows": [[i["severity"], i["category"], i["title"]] for i in insights[:8]]}],
        }

    # ===== FUNCTION: Dashboards._inventory() =====
    # ID: F0237 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:122-155
    # ROLE: Inventory dashboard: positions below target, stock-out risk, inventory / excess / expiring value; understock, days of cover,
    #       surplus-gap (stock balance of the focus product) and shelf-life charts; forecast chart reference.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0210 SupplyChainEngine.position_health() (calls)
    #   -> F0228 _in() (calls)
    #   -> F0225 SupplyChainEngine.expiry_risk() (calls)
    #   -> F0198 SupplyChainEngine.stock_balance() (calls)
    #   -> F0407 SapRepository.section() (calls)
    #   -> F0233 Dashboards._understock_chart() (calls)
    #   -> F0410 SapRepository.material() (calls)
    def _inventory(self, scope, material) -> dict:
        positions = [r for r in self.engine.position_health() if _in(scope, r["material"])]
        fg = [r for r in positions if r["material_type"] == "FG"]
        expiry = [r for r in self.engine.expiry_risk(180) if _in(scope, r["material"])]
        # Default focus: the finished good with the lowest days of cover anywhere (works for every customer's catalogue)
        focus = material or min(fg, key=lambda r: r["days_of_cover"] if r["days_of_cover"] is not None else 1e9)["material"]
        balance = self.engine.stock_balance(focus)
        demand = self.engine.sap.section("warehouse_demand_daily")[focus]
        return {
            "kpis": [
                {"label": "Positions below target", "value": sum(r["shortfall"] > 0 for r in positions), "status": "warning", "hint": f"of {len(positions)} material × location"},
                {"label": "Stock-out risk (< 7 days)", "value": sum((r["days_of_cover"] or 99) < 7 for r in fg), "status": "critical"},
                {"label": "Inventory value", "value": round(sum(r["stock_value_eur"] for r in positions)), "unit": "€", "status": "info"},
                {"label": "Excess stock (> 2× target)", "value": round(sum(r["excess_value_eur"] for r in positions)), "unit": "€", "status": "warning", "hint": "cash tied up"},
                {"label": "Expiring ≤ 180 days", "value": round(sum(r["value_eur"] for r in expiry)), "unit": "€", "status": "warning"},
            ],
            "charts": [
                self._understock_chart(positions, "Top 10 understocked products" if scope is None else "Understocked positions (product + components)"),
                {"id": "cover", "type": "bar", "title": "Days of cover — finished goods by DC", "subtitle": "on hand ÷ daily demand; alert below 7 days",
                 "unit": " d", "reference": 7, "reference_label": "7-day alert",
                 "rows": [{"label": f"{r['material']} @ {r['location']}", "value": r["days_of_cover"],
                           "status": "critical" if r["days_of_cover"] < 4 else "warning" if r["days_of_cover"] < 7 else "good",
                           "hint": f"{r['on_hand']:,.0f} units, {r['requirement'] / 14:,.0f}/day"} for r in sorted(fg, key=lambda r: r["days_of_cover"])]},
                {"id": "gap", "type": "diverging", "title": f"{self.engine.sap.material(focus)['description']}: surplus (+) / gap (−) vs target by DC",
                 "subtitle": "XGBoost 14-day forecast + safety stock; OR-Tools moves surplus to gaps",
                 "unit": " units", "rows": [{"label": p["warehouse"], "value": p["surplus_or_gap"]} for p in balance["positions"]]},
                {"id": "expiry", "type": "bar", "title": "Shelf-life risk: batches expiring within 180 days", "subtitle": "days left; value at cost in the hint",
                 "unit": " d", "rows": [{"label": f"{r['batch']} · {r['material']} @ {r['plant']}", "value": r["days_left"],
                                         "status": "critical" if r["state"] != "warning" else "warning",
                                         "hint": f"{r['quantity']:,.0f} units, €{r['value_eur']:,.0f}, expires {r['expiry']}"} for r in expiry]},
            ],
            # The UI loads the forecast-vs-actuals chart of the focus product at its highest-demand DC.
            "forecast": {"material": focus, "warehouse": max(demand, key=lambda wh: float(demand[wh]))},
            "tables": [],
        }

    # ===== FUNCTION: Dashboards._sales() =====
    # ID: F0238 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:157-191
    # ROLE: Sales-order desk: open / at-risk / inbound-dependent orders, fill rate, value at risk, fixable by transfer; quantity by
    #       status and fill-rate charts; orders and resolutions table.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   -> F0228 _in() (calls)
    #   -> F0407 SapRepository.section() (calls)
    def _sales(self, scope, material) -> dict:
        result = self.engine.sales_order_fulfilment()
        orders = [o for o in result["orders"] if _in(scope, o["material"])]
        actions = [a for a in result["proposed_actions"] if _in(scope, a.get("material"))]
        qty = sum(float(o["quantity"]) for o in orders)
        fill = 100 * sum(float(o["confirmed"]) for o in orders) / qty if qty else 100
        cost = {m["code"]: float(m["unit_cost"]) for m in self.engine.sap.section("materials")}
        by_status = Counter(o["status"] for o in orders)
        return {
            "kpis": [
                {"label": "Open sales orders", "value": len(orders), "status": "info"},
                {"label": "At risk", "value": by_status.get("at_risk", 0), "status": "critical"},
                {"label": "Depends on inbound", "value": by_status.get("depends_on_inbound", 0), "status": "warning"},
                {"label": "Fill rate", "value": round(fill, 1), "unit": "%", "status": "good" if fill >= 98 else "warning"},
                {"label": "Value at risk", "value": round(sum(o["shortfall"] * cost[o["material"]] for o in orders)), "unit": "€", "status": "warning"},
                {"label": "Fixable by transfer", "value": sum(1 for a in actions if a["action"] == "stock_transfer"), "status": "good"},
            ],
            "charts": [
                {"id": "orders", "type": "stacked", "title": "Order quantity by status and warehouse", "subtitle": "confirmed vs shortfall, units",
                 "series": ["confirmed", "shortfall"],
                 "rows": [{"label": wh, "segments": [{"name": "confirmed", "value": sum(o["confirmed"] for o in orders if o["warehouse"] == wh)},
                                                      {"name": "shortfall", "value": sum(o["shortfall"] for o in orders if o["warehouse"] == wh)}]}
                          for wh in sorted({o["warehouse"] for o in orders})]},
                {"id": "fill", "type": "bar", "title": "Fill rate by order", "subtitle": "confirmed ÷ ordered by requested date", "unit": "%", "reference": 100,
                 "rows": [{"label": f"{o['order']} · {o['customer']}", "value": round(100 * o["confirmed"] / o["quantity"], 1),
                           "status": {"at_risk": "critical", "depends_on_inbound": "warning"}.get(o["status"], "good"),
                           "hint": f"due {o['requested_date']} · {o['priority']} priority · {o['quantity']:,.0f} {o['material']} from {o['warehouse']}"} for o in orders]},
            ],
            "tables": [{"title": "Orders and resolutions", "columns": ["Order", "Customer", "Due", "Qty", "Confirmed", "Status", "Resolution"],
                        "rows": [[o["order"], o["customer"], o["requested_date"], o["quantity"], o["confirmed"], o["status"],
                                  (f"transfer {o['resolution']['quantity']:g} from {o['resolution']['from']} (arrives {o['resolution']['arrives']})"
                                   if (o["resolution"] or {}).get("action") == "stock_transfer" else
                                   "partial delivery" if o["resolution"] else "—")] for o in orders]}],
            "analysis": "sales",
        }

    # ===== FUNCTION: Dashboards._stocktake() =====
    # ID: F0239 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:193-221
    # ROLE: Stocktake control: counts, record accuracy, explained / to investigate, difference value; explained-vs-unexplained and
    #       difference-value charts; reconciliation table with evidence.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0207 SupplyChainEngine.stocktake_reconciliation() (calls)
    #   -> F0228 _in() (calls)
    def _stocktake(self, scope, material) -> dict:
        result = self.engine.stocktake_reconciliation()
        counts = [c for c in result["counts"] if _in(scope, c["material"])]
        accurate = sum(c["status"] in ("matched", "within_tolerance") for c in counts)
        investigate = sum(c["status"] == "investigate" for c in counts)
        return {
            "kpis": [
                {"label": "Counts", "value": len(counts), "status": "info"},
                {"label": "Inventory record accuracy", "value": round(100 * accurate / len(counts), 1) if counts else 100, "unit": "%",
                 "status": "warning", "hint": "matched or within tolerance before posting"},
                {"label": "Explained automatically", "value": sum(c["status"] == "explained" for c in counts), "status": "good"},
                {"label": "To investigate", "value": investigate, "status": "critical" if investigate else "good"},
                {"label": "Absolute difference value", "value": round(sum(c["difference_value_eur"] for c in counts)), "unit": "€", "status": "warning"},
            ],
            "charts": [
                {"id": "explained", "type": "stacked", "title": "Count differences: explained vs unexplained", "subtitle": "absolute units by count",
                 "series": ["explained", "unexplained"],
                 "rows": [{"label": f"{c['material']} @ {c['plant']}", "segments": [{"name": "explained", "value": abs(c["explained"])},
                                                                                    {"name": "unexplained", "value": abs(c["unexplained"])}]}
                          for c in counts if c["difference"]]},
                {"id": "diffvalue", "type": "diverging", "title": "Difference value by count (€)", "subtitle": "counted − book, at cost", "unit": " €",
                 "rows": [{"label": f"{c['material']} @ {c['plant']}", "value": c["difference_value_eur"] if c["difference"] >= 0 else -c["difference_value_eur"]} for c in counts]},
            ],
            "tables": [{"title": "Reconciliation with evidence", "columns": ["Count", "Location", "Material", "Book", "Counted", "Diff", "Status", "Evidence", "Recommendation"],
                        "rows": [[c["count_id"], c["plant"], c["material"], c["book_quantity"], c["counted_quantity"], c["difference"], c["status"],
                                  "; ".join(f"{e['document']} {e['quantity']:+g} ({e['type'].replace('_', ' ')})" for e in c["evidence"]) or "—",
                                  (c["recommendation"] or {}).get("action", "—").replace("_", " ")] for c in counts]}],
            "analysis": "stocktake",
        }

    # ===== FUNCTION: Dashboards._procurement() =====
    # ID: F0240 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:223-255
    # ROLE: Procurement dashboard: supplier counts, high-risk, average OTIF, single sourcing, open PO value, unconfirmed POs; OTIF,
    #       time-to-deliver, reject-rate and exposure charts; supplier scorecard table.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0234 Dashboards._supplier_rows() (calls)
    #   -> F0407 SapRepository.section() (calls)
    #   -> F0228 _in() (calls)
    def _procurement(self, scope, material) -> dict:
        rows = self._supplier_rows(scope)
        open_pos = [po for po in self.engine.sap.section("purchase_orders") if _in(scope, po["material"])]
        return {
            "kpis": [
                {"label": "Suppliers", "value": len(rows), "status": "info"},
                {"label": "High-risk suppliers", "value": sum(r["risk_rating"] == "high" for r in rows), "status": "critical"},
                {"label": "Average OTIF", "value": round(sum(r["otif_pct"] or 0 for r in rows) / len(rows), 1) if rows else None, "unit": "%", "status": "warning"},
                {"label": "Single-source materials", "value": sum(r["single_source"] for r in rows), "status": "warning"},
                {"label": "Open PO value", "value": round(sum(r["open_po_exposure_eur"] for r in rows)), "unit": "€", "status": "info"},
                {"label": "Unconfirmed POs", "value": sum(po.get("status") != "confirmed" for po in open_pos), "status": "warning"},
            ],
            "charts": [
                {"id": "otif", "type": "bar", "title": "Top suppliers by reliability (OTIF %)", "subtitle": "on time and in full, last 6 months of receipts",
                 "unit": "%", "reference": 95, "reference_label": "95% target",
                 "rows": [{"label": r["supplier"], "value": r["otif_pct"], "status": "good" if (r["otif_pct"] or 0) >= r["otif_target_pct"] else "warning" if (r["otif_pct"] or 0) >= 50 else "critical",
                           "hint": f"target {r['otif_target_pct']}% · {r['materials']}"} for r in sorted(rows, key=lambda r: -(r["otif_pct"] or 0))[:10]]},
                {"id": "leadtime", "type": "stacked", "title": "Time to deliver (days)", "subtitle": "contract lead time + average actual delay",
                 "series": ["contract lead time", "average delay"],
                 "rows": [{"label": r["supplier"], "segments": [{"name": "contract lead time", "value": r["contract_lead_time_days"]},
                                                                {"name": "average delay", "value": r["average_delay_days"] or 0}]}
                          for r in sorted(rows, key=lambda r: r["effective_lead_time_days"])[:10]]},
                {"id": "rejects", "type": "bar", "title": "Quality reject rate by supplier", "subtitle": "rejected ÷ ordered quantity", "unit": "%",
                 "rows": [{"label": r["supplier"], "value": r["quality_reject_pct"], "status": "critical" if (r["quality_reject_pct"] or 0) > 5 else "warning" if (r["quality_reject_pct"] or 0) > 1 else "good"}
                          for r in sorted(rows, key=lambda r: -(r["quality_reject_pct"] or 0))]},
                {"id": "exposure", "type": "bar", "title": "Open PO exposure by supplier (€)", "subtitle": "open quantity × unit cost", "unit": " €",
                 "rows": [{"label": r["supplier"], "value": r["open_po_exposure_eur"], "status": "warning" if r["risk_rating"] == "high" else "info"}
                          for r in sorted(rows, key=lambda r: -r["open_po_exposure_eur"])]},
            ],
            "tables": [{"title": "Supplier scorecard", "columns": ["Supplier", "Supplies", "Risk", "Score", "OTIF %", "Lead time", "Avg delay", "Rejects %", "Single source"],
                        "rows": [[r["supplier"], r["materials"], r["risk_rating"], r["risk_score"], r["otif_pct"], r["contract_lead_time_days"], r["average_delay_days"],
                                  r["quality_reject_pct"], "yes" if r["single_source"] else "no"] for r in rows]}],
        }

    # ===== FUNCTION: Dashboards._production() =====
    # ID: F0241 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:257-281
    # ROLE: Production dashboard: orders ready / at risk, stock held in QM; component-readiness and component-shortage (21-day) charts;
    #       quality lots affecting production.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0208 SupplyChainEngine.production_overview() (calls)
    #   -> F0228 _in() (calls)
    #   -> F0210 SupplyChainEngine.position_health() (calls)
    #   -> F0203 SupplyChainEngine.quality_status() (calls)
    #   -> F0233 Dashboards._understock_chart() (calls)
    def _production(self, scope, material) -> dict:
        orders = [o for o in self.engine.production_overview()["orders"] if _in(scope, o["material"])]
        positions = [r for r in self.engine.position_health(21) if r["location_type"] != "warehouse" and _in(scope, r["material"])]
        quality = self.engine.quality_status()
        lots = {lot["lot"]: lot for lot in quality["lots"]}
        impacts = [i for i in quality["production_impacts"] if _in(scope, i["finished_good"])]
        held = sum(float(lot["quantity"]) for lot in quality["lots"] if lot["status"] in ("inspection", "blocked") and _in(scope, lot["material"]))
        return {
            "kpis": [
                {"label": "Production orders", "value": len(orders), "status": "info"},
                {"label": "Ready", "value": sum(o["readiness"] == "ready" for o in orders), "status": "good"},
                {"label": "At risk / not ready", "value": sum(o["readiness"] != "ready" for o in orders), "status": "critical"},
                {"label": "Stock held in QM", "value": round(held), "status": "warning", "hint": "inspection + blocked"},
            ],
            "charts": [
                {"id": "orders", "type": "bar", "title": "Component readiness by production order", "subtitle": "% of BOM components covered by the finish date",
                 "unit": "%", "reference": 100,
                 "rows": [{"label": f"{o['order']} · {o['material']} @ {o['plant']}", "value": o["component_readiness_pct"],
                           "status": {"ready": "good", "at_risk": "warning"}.get(o["readiness"], "critical"),
                           "hint": f"{o['quantity']:,.0f} units due {o['finish_date']}; short: {', '.join(o['short_components']) or 'none'}"} for o in orders]},
                self._understock_chart(positions, "Top 10 component shortages (21-day horizon)"),
            ],
            "tables": [{"title": "Quality lots affecting production", "columns": ["Lot", "Material", "Plant", "Status", "Production order"],
                        "rows": [[i["lot"], lots[i["lot"]]["material"], lots[i["lot"]]["plant"], lots[i["lot"]]["status"], i["production_order"]] for i in impacts]}],
        }

    # ===== FUNCTION: Dashboards._logistics() =====
    # ID: F0242 · method · used (framework)
    # ORIGINAL FILE: backend/app/dashboards.py:283-305
    # ROLE: Logistics control tower: shipments in flight, delayed, escalations, units delayed; delay-by-shipment and lane-cost charts.
    # INPUTS:
    #   scope, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0204 SupplyChainEngine.logistics_status() (calls)
    #   -> F0228 _in() (calls)
    def _logistics(self, scope, material) -> dict:
        status = self.engine.logistics_status()
        ships = [s for s in status["shipments"] if _in(scope, s["material"])]
        delayed = [s for s in ships if s.get("delay_days")]
        lanes = status["lanes"]
        return {
            "kpis": [
                {"label": "Shipments in flight", "value": sum(s["status"] in ("in_transit", "planned") for s in ships), "status": "info"},
                {"label": "Delayed", "value": len(delayed), "status": "warning"},
                {"label": "Escalations (> 3 days)", "value": sum(s["escalate"] for s in ships), "status": "critical"},
                {"label": "Units delayed", "value": round(sum(float(s["quantity"]) for s in delayed)), "status": "warning"},
            ],
            "charts": [
                {"id": "delays", "type": "bar", "title": "Delay by shipment (days)", "subtitle": "revised ETA − planned ETA; escalate above 3 days", "unit": " d", "reference": 3,
                 "rows": [{"label": f"{s['shipment']} {s['from']}→{s['to']}", "value": s.get("delay_days") or 0,
                           "status": "critical" if s["escalate"] else "warning" if s.get("delay_days") else "good",
                           "hint": f"{s['carrier']} ({s['mode']}) · {s['quantity']:,.0f} {s['material']} · ETA {s['revised_eta']}"} for s in sorted(ships, key=lambda s: -(s.get("delay_days") or 0))]},
                {"id": "lanes", "type": "bar", "title": "Transfer lanes: cost per unit (€)", "subtitle": "lead time and CO₂ in the hint", "unit": " €",
                 "rows": [{"label": f"{lane['from']}→{lane['to']}", "value": lane["cost_per_unit"], "status": "info",
                           "hint": f"{lane['lead_days']} days · {lane['carbon_kg_per_unit']} kg CO₂/unit"} for lane in sorted(lanes, key=lambda x: x["cost_per_unit"])]},
            ],
            "tables": [],
        }
