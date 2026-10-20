"""Role-centred decision views: the product is organised around the people who make supply-chain decisions.

Every role answers the same four questions on one screen:
  1. What matters        -> KPIs with an agreed definition, formula, target and SAP source
  2. What is likely to go wrong -> dated predictions with the basis of each prediction
  3. What it will cost   -> value at risk and the direct cost of the proposed fixes
  4. What to do next     -> recommended actions, each with a button and an owner agent
plus a specialised agent (mission, scoped tools, industry rules) the person can ask.

Everything is computed deterministically from the SAP snapshot. KPIs whose source data is not in the snapshot are
returned with available=False and the SAP source they need, never with an invented number. Targets are demo targets
until the customer agrees its own definitions, periods and targets.
"""
from __future__ import annotations

from datetime import date, timedelta

from backend.app.dashboards import Dashboards
from backend.app.engine import SupplyChainEngine
from backend.app.forecasting import evaluate_models
from backend.app.insights import InsightEngine
from backend.app.store import Store

CARRYING_COST_RATE = 0.25  # annual inventory carrying cost as a share of stock value (demo assumption)

NORTH_STAR = {
    "statement": "Maximise reliable customer fulfilment at the lowest sustainable supply-chain cost and inventory risk.",
    "learning": "Improve verified operational outcomes over time, comparing model-assisted decisions with the business baseline.",
}

# --------------------------------------------------------------------------------------------- role catalogue
ROLES: dict[str, dict] = {
    "director": {
        "priority": 1, "mvp": True, "title": "Supply Chain Director", "agent": "Supervisor Agent",
        "focus": "Overall operations and business value: service vs cost vs inventory risk",
        "recommends": "Identify the biggest risks, balance cost against service, prioritise decisions",
        "areas": None, "tools": None,
        "starters": ["What are the three biggest supply risks this week and what do they cost?",
                     "Which decisions are waiting for me and which matters most?",
                     "Where are we trading service for cost right now?"],
    },
    "demand": {
        "priority": 2, "mvp": True, "title": "Demand Planner", "agent": "Forecast Agent",
        "focus": "Future demand and stock-out prediction by SKU and warehouse",
        "recommends": "Predict demand by SKU, region and season; flag projected stock-outs early",
        "areas": {"Stock", "Sales orders"},
        "tools": ["sap_snapshot", "demand_forecast", "inventory_overview", "warehouse_stock_balance", "sales_order_fulfilment", "search_governed_knowledge"],
        "starters": ["Which products will stock out in the next 30 days and where?",
                     "How accurate is the forecast for Eau de Parfum in Dubai?",
                     "Which warehouse demand is the most variable?"],
    },
    "production": {
        "priority": 3, "mvp": True, "title": "Production Planner", "agent": "Factory Agent",
        "focus": "Factory material readiness and production schedule",
        "recommends": "Predict material shortages and production delays before release",
        "areas": {"Components", "Production"},
        "tools": ["sap_snapshot", "factory_material_readiness", "quality_status", "supplier_risk", "inventory_overview", "search_governed_knowledge"],
        "starters": ["Can FR20 produce 6000 FG-SERUM-50 by 2026-10-27?",
                     "Which production orders are at risk and which component blocks them?",
                     "Do we need extra production for any product this month?"],
    },
    "procurement": {
        "priority": 4, "mvp": True, "title": "Procurement Manager", "agent": "Procurement Agent",
        "focus": "Supplier reliability, lead times, prices and replenishment",
        "recommends": "Recommend suppliers, quantities and order dates",
        "areas": {"Components", "Suppliers"},
        "tools": ["sap_snapshot", "supplier_risk", "factory_material_readiness", "quality_status", "search_governed_knowledge"],
        "starters": ["Which suppliers deliver later than their contract and what does it cost us?",
                     "What should I order this week, from whom and by when?",
                     "Is PackGlass Europe a continuity risk? Cite the contract."],
    },
    "warehouse": {
        "priority": 5, "mvp": True, "title": "Warehouse Manager", "agent": "Inventory Agent",
        "focus": "Stock across the three warehouses: balance, accuracy and expiry (FEFO)",
        "recommends": "Optimise stock across the three warehouses and prioritise FEFO",
        "areas": {"Stock"},
        "tools": ["sap_snapshot", "inventory_overview", "warehouse_stock_balance", "stocktake_reconciliation", "logistics_status", "search_governed_knowledge"],
        "starters": ["Rebalance FG-PERFUME-100 across the three DCs",
                     "Explain the stock count differences",
                     "Which batches should ship first because they expire soonest?"],
    },
    "logistics": {
        "priority": 6, "mvp": False, "title": "Logistics Manager", "agent": "Logistics Agent",
        "focus": "Shipments, transfers, transit times and freight cost",
        "recommends": "Optimise shipments, routes and warehouse transfers",
        "areas": {"Stock", "Sales orders"},
        "tools": ["sap_snapshot", "logistics_status", "warehouse_stock_balance", "sales_order_fulfilment", "search_governed_knowledge"],
        "starters": ["Which delayed shipments put stock at risk?",
                     "What is the cheapest on-time transfer for Dubai?",
                     "Where are we paying for air freight?"],
    },
    "quality": {
        "priority": 7, "mvp": False, "title": "Quality Manager", "agent": "Quality Agent",
        "focus": "Batch release, blocked stock and expiry risk",
        "recommends": "Identify quality and expiry risks before materials or products are used",
        "areas": set(),
        "tools": ["sap_snapshot", "quality_status", "supplier_risk", "search_governed_knowledge"],
        "starters": ["Which inspection lots block production this week?",
                     "What is our blocked stock worth and why is it blocked?",
                     "What does the quality policy say about releasing RM-ACTIVE early?"],
    },
    "finance": {
        "priority": 8, "mvp": False, "title": "Finance / CFO", "agent": "Cost Intelligence Agent",
        "focus": "Working capital, carrying cost, expedite spend and verified savings",
        "recommends": "Quantify financial impact and compare alternatives",
        "areas": None,
        "tools": ["sap_snapshot", "inventory_overview", "warehouse_stock_balance", "supplier_risk", "sales_order_fulfilment", "search_governed_knowledge"],
        "starters": ["How much working capital is tied up in excess stock?",
                     "What will the proposed fixes cost versus the value they protect?",
                     "Which savings have been verified so far?"],
    },
    "mlops": {
        "priority": 9, "mvp": False, "title": "AI / MLOps Manager", "agent": "Learning Agent",
        "focus": "Prediction quality, drift and verified business outcomes",
        "recommends": "Detect errors, retrain models, evaluate and promote improvements",
        "areas": set(),
        "tools": ["sap_snapshot", "demand_forecast", "inventory_overview"],
        "starters": ["Is the demand model drifting anywhere?",
                     "How much better is the model than the simple baseline?",
                     "Which executed recommendations still need a verified outcome?"],
    },
}

# Industry-specific KPIs: the same framework, adapted to each industry's risks.
INDUSTRY_KPIS = {
    "cosmetics": ["Packaging readiness", "Promotion forecast accuracy", "Batch expiry loss", "Ingredient availability"],
    "pharmaceutical": ["Quality release lead time", "Lot traceability", "Qualified supplier reliability", "Controlled-temperature deviations"],
    "food": ["Spoilage rate", "Shelf-life remaining", "Cold-chain excursions", "Ingredient freshness"],
    "automotive": ["Line-stop risk", "Component shortages", "Supplier delivery reliability", "Production schedule adherence"],
    "ecommerce": ["SKU availability", "Fill rate", "Returns rate", "Promotion forecast accuracy"],
}

INDUSTRY_RULES = {
    "cosmetics": "Cosmetics rules: packaging (bottles, cartons) is a frequent bottleneck; batches have shelf lives, so ship FEFO; promotions drive demand spikes.",
    "pharmaceutical": "Pharma rules: only GMP-released lots may be used; keep lot traceability; only qualified suppliers; never shortcut quality release.",
    "food": "Food rules: shelf life and freshness drive allocation (FEFO); cold-chain excursions make stock unusable.",
    "automotive": "Automotive rules: a missing component stops the line; protect production schedule adherence; dual-source critical parts.",
    "ecommerce": "E-commerce rules: SKU availability and fulfilment lead time drive conversion; promotions and returns change demand quickly.",
}


def agent_system_prompt(role: str, industry: str = "cosmetics") -> str:
    """Role-specific instructions for the specialised agent (LangGraph chat graph)."""
    spec = ROLES[role]
    return (f"You are the {spec['agent']} working for the {spec['title']}. Mission: {spec['recommends']}. "
            f"Focus: {spec['focus']}. {INDUSTRY_RULES.get(industry, '')} "
            "Answer in this order: what matters, what is likely to go wrong (with dates), what it will cost, what to do next. "
            "Every number must come from a tool result.")


def _status(value, target, direction) -> str:
    if value is None or target is None:
        return "info"
    if direction == "up":
        return "good" if value >= target else "warning" if value >= target * 0.9 else "critical"
    return "good" if value <= target else "warning" if value <= target * 1.25 else "critical"


def kpi(label, value, unit, target, direction, definition, formula, source, hint=None, status=None, available=True) -> dict:
    """A KPI with its agreed definition. available=False means the SAP source is not in this snapshot yet."""
    if not available:
        value, status = None, "info"
    return {"label": label, "value": None if value is None else round(value, 1), "unit": unit, "target": target, "direction": direction,
            "status": status or _status(value, target, direction), "definition": definition, "formula": formula, "source": source,
            "hint": hint if available else f"needs SAP data: {source}", "available": available}


class RoleCenter:
    def __init__(self, engine: SupplyChainEngine, insights: InsightEngine, store: Store, dashboards: Dashboards, industry: str = "cosmetics"):
        self.engine, self.insights, self.store, self.dashboards, self.industry = engine, insights, store, dashboards, industry

    # ------------------------------------------------------------------ shared facts (computed once per request)
    def _facts(self, material: str | None) -> dict:
        e = self.engine
        sap = e.sap
        scope = self.dashboards.product_scope(material)
        fgs = [m["code"] for m in sap.section("materials") if m["type"] == "FG" and (not material or m["code"] == material)]
        briefs = [e.product_brief(code) for code in fgs]
        orders = [o for o in e.sales_order_fulfilment()["orders"] if not scope or o["material"] in scope]
        positions = [r for r in e.position_health() if not scope or r["material"] in scope]
        cost = {m["code"]: float(m["unit_cost"]) for m in sap.section("materials")}
        demand = sap.section("warehouse_demand_daily")
        models = []
        for code in fgs:
            for wh, daily in demand.get(code, {}).items():
                if float(daily):
                    models.append({"material": code, "warehouse": wh, "daily": float(daily), **evaluate_models(float(daily))})
        return {
            "scope": scope, "fgs": fgs, "briefs": briefs, "orders": orders, "positions": positions, "cost": cost, "models": models,
            "issues": [i | {"product": b["description"], "material": b["material"]} for b in briefs for i in b["issues"]],
            "suppliers": [s for s in e.supplier_scorecard()["suppliers"]
                          if not scope or scope & set(sap.supplier(s["supplier"])["materials"])],
            "production": [o for o in e.production_overview()["orders"] if not scope or o["material"] in scope],
            "quality": e.quality_status(), "expiry": [r for r in e.expiry_risk(180) if not scope or r["material"] in scope],
            "counts": [c for c in e.stocktake_reconciliation()["counts"] if not scope or c["material"] in scope],
            "logistics": e.logistics_status(), "calendar": e.sales_outlook(material)["calendar"],
            "outcomes": self.store.list_outcomes(sap.snapshot["id"]), "decisions": self.store.decision_stats(sap.snapshot["id"]),
            "executed": self.store.list_recommendations("executed", sap.snapshot["id"]),
        }

    # ------------------------------------------------------------------ platform KPIs + north star
    def _otif(self, f) -> float | None:
        orders = f["orders"]
        return 100 * sum(o["shortfall"] == 0 and o["status"] != "at_risk" for o in orders) / len(orders) if orders else None

    def _inventory_value(self, f) -> float:
        return sum(r["stock_value_eur"] for r in f["positions"])

    def _annual_cogs(self, f) -> float:
        demand = self.engine.sap.section("warehouse_demand_daily")
        return sum(float(v) * f["cost"][m] * 365 for m in f["fgs"] for v in demand.get(m, {}).values())

    def _wape(self, f) -> float | None:
        total = sum(m["daily"] for m in f["models"])
        return sum(m["model"]["wape_pct"] * m["daily"] for m in f["models"]) / total if total else None

    def _supply_chain_cost(self, f) -> dict:
        """30-day estimate: procurement (open POs) + transport (proposed transfers) + storage (carrying) + expiry + exceptions."""
        sap = self.engine.sap
        price = {(s["name"], m): s.get("unit_price_eur") for s in sap.section("suppliers") for m in s["materials"]}
        procurement = sum(float(po["quantity"]) * (price.get((po["supplier"], po["material"])) or f["cost"][po["material"]])
                          for po in sap.section("purchase_orders") if not f["scope"] or po["material"] in f["scope"])
        transport = sum(i["fix_cost_eur"] or 0 for i in f["issues"] if i["area"] in ("Stock", "Sales orders") and i["severity"] != "info")
        storage = self._inventory_value(f) * CARRYING_COST_RATE * 30 / 365
        expiry = sum(r["value_eur"] for r in f["expiry"] if r["days_left"] <= 30)
        lanes = {(lane["from"], lane["to"]): lane for lane in f["logistics"]["lanes"]}
        exceptions = sum(float(s["quantity"]) * lanes.get((s["from"], s["to"]), {}).get("cost_per_unit", 0)
                         for s in f["logistics"]["shipments"] if s["mode"] == "air" and s["status"] in ("in_transit", "planned"))
        parts = {"procurement": procurement, "transport": transport, "storage": storage, "expiry": expiry, "exceptions": exceptions}
        return {"total": round(sum(parts.values()), 0), "parts": {k: round(v, 0) for k, v in parts.items()}}

    def platform_kpis(self, f) -> list[dict]:
        orders = f["production"]
        ready = 100 * sum(o["readiness"] == "ready" for o in orders) / len(orders) if orders else None
        value = self._inventory_value(f)
        turns = self._annual_cogs(f) / value if value else None
        sc = self._supply_chain_cost(f)
        return [
            kpi("Customer OTIF (projected)", self._otif(f), "%", 95, "up", "Orders delivered on time and in full ÷ eligible orders",
                "open orders projected on time and in full ÷ open orders × 100", "SD sales orders + stock + inbound",
                hint=f"{len(f['orders'])} open orders; delivered-order history is needed for actual OTIF"),
            kpi("Material readiness", ready, "%", 95, "up", "Production orders with all usable materials ready ÷ scheduled orders",
                "ready production orders ÷ scheduled production orders × 100", "PP production orders + BOM + stock + POs", hint=f"{len(orders)} scheduled orders"),
            kpi("Inventory turnover", turns, "×", 8, "up", "Cost of goods sold ÷ average inventory value",
                "annualised forecast demand × standard cost ÷ stock value at cost", "MM stock + material standard cost + demand",
                hint=f"stock €{value:,.0f} at cost"),
            kpi("Forecast WAPE", self._wape(f), "%", 20, "down", "Sum of absolute forecast errors ÷ sum of actual demand",
                "Σ|forecast − actual| ÷ Σ actual × 100 on a 14-day holdout, demand-weighted", "SD billing history (synthetic in this POC)",
                hint="lower is better · synthetic history"),
            kpi("Supply-chain cost (30 d)", sc["total"], "€", None, "down", "Agreed procurement, transport, storage, expiry and exception costs",
                "open PO value + proposed transfer cost + carrying cost (25%/yr) + expiring stock ≤30 d + air freight in flight", "MM/PUR/LE + assumptions",
                hint=" · ".join(f"{k} €{v:,.0f}" for k, v in sc["parts"].items()), status="info"),
        ]

    def learning_summary(self, f) -> dict:
        outcomes = f["outcomes"]
        observed = [o for o in outcomes if o["status"] != "awaiting_observation"]
        executed = max(len(f["executed"]), len(outcomes))  # decisions executed before outcome tracking still count as awaiting
        verified = [o for o in observed if o["achieved"]]
        models = f["models"]
        weight = sum(m["daily"] for m in models) or 1
        reduction = sum((m["error_reduction_pct"] or 0) * m["daily"] for m in models) / weight if models else None
        drift = max((m["drift"]["change_pts"] for m in models), default=None)
        overdue = [o for o in outcomes if o["status"] == "awaiting_observation" and o["due_date"] and o["due_date"] < self.engine.sap.as_of.isoformat()]
        return {
            "error_reduction_pct": None if reduction is None else round(reduction, 1),
            "drift_max_pts": drift, "executed": executed, "observed": len(observed), "verified": len(verified),
            "verified_pct": round(100 * len(observed) / executed, 1) if executed else None,
            "achieved_pct": round(100 * len(verified) / len(observed), 1) if observed else None,
            "realized_impact_eur": round(sum(o["realized_impact_eur"] or 0 for o in verified), 0), "overdue": len(overdue),
            **{k: f["decisions"][k] for k in ("acceptance_pct", "override_pct", "decided", "override_reasons")},
        }

    def north_star(self, material: str | None = None) -> dict:
        f = self._facts(material)
        risk = (sum(r["shortfall_value_eur"] for r in f["positions"]) + sum(r["value_eur"] for r in f["expiry"] if r["days_left"] <= 90)
                + sum(r["excess_value_eur"] for r in f["positions"]))
        learning = self.learning_summary(f)
        return {
            **NORTH_STAR, "as_of": self.engine.sap.as_of.isoformat(),
            "components": [
                {"label": "Reliable fulfilment", "value": None if self._otif(f) is None else round(self._otif(f), 1), "unit": "%", "hint": "projected OTIF, open orders"},
                {"label": "Supply-chain cost (30 d)", "value": self._supply_chain_cost(f)["total"], "unit": "€", "hint": "estimate, see definition"},
                {"label": "Inventory risk", "value": round(risk, 0), "unit": "€", "hint": "short vs target + expiring ≤ 90 d + excess, at cost"},
            ],
            "learning_components": [
                {"label": "Forecast error vs baseline", "value": None if learning["error_reduction_pct"] is None else -learning["error_reduction_pct"], "unit": "%",
                 "hint": "WAPE change vs same-weekday-last-week baseline (negative = better)"},
                {"label": "Verified outcomes", "value": learning["verified_pct"], "unit": "%", "hint": f"{learning['observed']} of {learning['executed']} executed decisions observed in SAP"},
                {"label": "Realised impact (verified)", "value": learning["realized_impact_eur"], "unit": "€", "hint": "only outcomes confirmed against SAP documents"},
            ],
            "platform_kpis": self.platform_kpis(f),
            "industry": self.industry_kpis(f),
        }

    # ------------------------------------------------------------------ industry KPIs
    def industry_kpis(self, f) -> dict:
        sap = self.engine.sap
        materials = {m["code"]: m for m in sap.section("materials")}
        comp_pos = [r for r in f["positions"] if r["material_type"] != "FG"]
        pack = [r for r in comp_pos if r["material"].startswith("PK") or materials[r["material"]]["type"] in ("PACK", "PK", "packaging")]
        rm = [r for r in comp_pos if r not in pack]
        covered = lambda rows: 100 * sum((r["coverage_pct"] or 0) >= 100 for r in rows) / len(rows) if rows else None  # noqa: E731
        value = self._inventory_value(f) or 1
        expired = sum(r["value_eur"] for r in f["expiry"] if r["days_left"] < 0)
        stock = [s for s in sap.section("stock") if not f["scope"] or s["material"] in f["scope"]]
        lots = f["quality"]["lots"]
        waiting = [(date.fromisoformat(lot["expected_release"]) - sap.as_of).days for lot in lots if lot["status"] == "inspection" and lot.get("expected_release")]
        approved = [s for s in f["suppliers"] if sap.supplier(s["supplier"]).get("approved", True)]
        fg_expiry = [(date.fromisoformat(s["expiry"]) - sap.as_of).days for s in stock if s.get("expiry") and materials[s["material"]]["type"] == "FG"]
        rm_expiry = [(date.fromisoformat(s["expiry"]) - sap.as_of).days for s in stock if s.get("expiry") and materials[s["material"]]["type"] != "FG"]
        fg_pos = [r for r in f["positions"] if r["material_type"] == "FG"]
        qty = sum(float(o["quantity"]) for o in f["orders"])
        fill = 100 * sum(float(o["confirmed"]) for o in f["orders"]) / qty if qty else None
        not_ready = [o for o in f["production"] if o["readiness"] != "ready"]
        otd = [s["otif_pct"] for s in f["suppliers"] if s["otif_pct"] is not None]
        catalogue = {
            "Packaging readiness": kpi("Packaging readiness", covered(pack), "%", 95, "up", "Packaging positions covered for the next 14 days", "packaging positions at ≥100% of target ÷ packaging positions", "MM stock + POs", available=bool(pack)),
            "Promotion forecast accuracy": kpi("Promotion forecast accuracy", None, "%", None, "up", "Forecast accuracy during promotions", "1 − WAPE on promotion periods", "promotion calendar (SD/CRM)", available=False),
            "Batch expiry loss": kpi("Batch expiry loss", 100 * expired / value, "%", 0.5, "down", "Value of expired stock ÷ inventory value", "expired batch value ÷ stock value × 100", "MM batch expiry dates"),
            "Ingredient availability": kpi("Ingredient availability", covered(rm), "%", 95, "up", "Raw-material positions covered for the next 14 days", "RM positions at ≥100% of target ÷ RM positions", "MM stock + POs", available=bool(rm)),
            "Quality release lead time": kpi("Quality release lead time", sum(waiting) / len(waiting) if waiting else 0, " d", 3, "down", "Average days until lots in inspection are released", "Σ(expected release − today) ÷ lots in inspection", "QM inspection lots"),
            "Lot traceability": kpi("Lot traceability", 100 * sum(bool(s.get("batch")) for s in stock) / len(stock) if stock else None, "%", 100, "up", "Stock quantities carrying a batch number", "stock records with batch ÷ stock records", "MM batch management"),
            "Qualified supplier reliability": kpi("Qualified supplier reliability", sum(s["otif_pct"] or 0 for s in approved) / len(approved) if approved else None, "%", 95, "up", "OTIF of approved suppliers", "average OTIF of approved suppliers", "PUR receipts (po_history)"),
            "Controlled-temperature deviations": kpi("Controlled-temperature deviations", None, "", 0, "down", "Temperature excursions in storage or transport", "count of logged excursions", "temperature loggers / LE events", available=False),
            "Spoilage rate": kpi("Spoilage rate", 100 * expired / value, "%", 0.5, "down", "Value of expired (spoiled) stock ÷ inventory value", "expired value ÷ stock value × 100", "MM batch expiry dates"),
            "Shelf-life remaining": kpi("Shelf-life remaining", sum(fg_expiry) / len(fg_expiry) if fg_expiry else None, " d", 180, "up", "Average days left before finished-good batches expire", "Σ days to expiry ÷ FG batches", "MM batch expiry dates", available=bool(fg_expiry)),
            "Cold-chain excursions": kpi("Cold-chain excursions", None, "", 0, "down", "Shipments or storage outside the cold-chain range", "count of excursions", "temperature loggers / LE events", available=False),
            "Ingredient freshness": kpi("Ingredient freshness", sum(rm_expiry) / len(rm_expiry) if rm_expiry else None, " d", 90, "up", "Average days left before ingredient batches expire", "Σ days to expiry ÷ ingredient batches", "MM batch expiry dates", available=bool(rm_expiry)),
            "Line-stop risk": kpi("Line-stop risk", len(not_ready), "", 0, "down", "Production orders that would stop for a missing component", "production orders not ready", "PP orders + BOM + stock + POs", status="critical" if not_ready else "good"),
            "Component shortages": kpi("Component shortages", sum(r["shortfall"] > 0 for r in comp_pos), "", 0, "down", "Component positions short of their 14-day target", "component positions with shortfall > 0", "MM stock + POs + PP requirements"),
            "Supplier delivery reliability": kpi("Supplier delivery reliability", sum(otd) / len(otd) if otd else None, "%", 95, "up", "On time in full deliveries by suppliers", "OTIF receipts ÷ receipts", "PUR receipts (po_history)"),
            "Production schedule adherence": kpi("Production schedule adherence", None, "%", 95, "up", "Orders finished on the planned date", "on-time confirmations ÷ orders", "PP order confirmations", available=False),
            "SKU availability": kpi("SKU availability", 100 * sum((r["days_of_cover"] or 0) >= 7 for r in fg_pos) / len(fg_pos) if fg_pos else None, "%", 98, "up", "Product × warehouse positions with at least 7 days of stock", "positions with ≥ 7 days of cover ÷ positions", "MM stock + demand"),
            "Fill rate": kpi("Fill rate", fill, "%", 98, "up", "Ordered quantity that can be confirmed", "confirmed quantity ÷ ordered quantity", "SD sales orders + stock + inbound"),
            "Returns rate": kpi("Returns rate", None, "%", 5, "down", "Returned quantity ÷ delivered quantity", "returns ÷ deliveries", "SD returns orders", available=False),
        }
        return {"industry": self.industry, "rules": INDUSTRY_RULES.get(self.industry, ""),
                "kpis": [catalogue[name] for name in INDUSTRY_KPIS.get(self.industry, INDUSTRY_KPIS["cosmetics"])]}

    # ------------------------------------------------------------------ role views
    def catalogue(self) -> list[dict]:
        return [{"id": rid, **{k: v for k, v in spec.items() if k not in ("areas",)}} for rid, spec in sorted(ROLES.items(), key=lambda x: x[1]["priority"])]

    def build(self, role: str, material: str | None = None) -> dict:
        if role not in ROLES:
            raise ValueError(f"Unknown role {role}. Options: {', '.join(ROLES)}")
        spec = ROLES[role]
        f = self._facts(material)
        body = getattr(self, f"_{role}")(f, material)
        predictions = sorted(body["predictions"], key=lambda p: ({"critical": 0, "warning": 1, "info": 2}[p["severity"]], p.get("in_days") if p.get("in_days") is not None else 999))
        actions = sorted(body["actions"], key=lambda a: ({"critical": 0, "warning": 1, "info": 2}[a["severity"]], -(a.get("at_risk_eur") or 0)))
        at_risk = sum(p.get("at_risk_eur") or 0 for p in predictions if p["severity"] != "info")
        known = [a["fix_cost_eur"] for a in actions if a.get("fix_cost_eur") is not None]
        focus = None
        if material:
            focus = {"material": material, "description": self.engine.sap.material(material)["description"]}
        return {
            "role": role, "title": spec["title"], "focus": spec["focus"], "mvp": spec["mvp"], "priority": spec["priority"],
            "as_of": self.engine.sap.as_of.isoformat(), "product": focus,
            "agent": {"name": spec["agent"], "mission": spec["recommends"], "tools": spec["tools"] or "all read-only tools",
                      "starters": spec["starters"], "industry": self.industry},
            "kpis": body["kpis"], "predictions": predictions[:12],
            "cost": {"at_risk_eur": round(at_risk, 0), "fix_cost_eur": round(sum(known), 0), "fixes_with_cost": len(known), "fixes": len(actions),
                     "note": "Value at risk at standard cost; issues can overlap (for example a stock-out and the order it shorts)."},
            "actions": actions[:10], "charts": body.get("charts", []), "tables": body.get("tables", []),
            "forecast": body.get("forecast"),
        }

    # ----------------------------------------------------------- building blocks
    def _issue_actions(self, f, areas=None, limit=None) -> list[dict]:
        rows = [i for i in f["issues"] if areas is None or i["area"] in areas]
        out = [{"severity": i["severity"], "title": i["fix"], "why": f"{i['product']}: {i['issue']}", "area": i["area"],
                "at_risk_eur": i["at_risk_eur"], "fix_cost_eur": i["fix_cost_eur"], "action": i["action"]} for i in rows]
        return out[:limit] if limit else out

    def _stock_predictions(self, f) -> list[dict]:
        out = []
        for ev in f["calendar"]:
            if ev["kind"] not in ("stockout", "below_safety"):
                continue
            days = ev["days_from_today"]
            issue = next((i for i in f["issues"] if i["area"] == "Stock" and i["material"] == ev["material"] and i["action"]["params"].get("warehouse") == ev["warehouse"]), None)
            out.append({"severity": ("critical" if days <= 14 else "warning" if days <= 30 else "info") if ev["kind"] == "stockout" else ("warning" if days <= 14 else "info"),
                        "what": f"{ev['description']} {'runs out' if ev['kind'] == 'stockout' else 'drops below safety stock'} at {ev['warehouse']}",
                        "when": ev["date"], "in_days": days, "area": "Stock",
                        "basis": "stock + inbound shipments + planned production − XGBoost daily forecast",
                        "at_risk_eur": issue["at_risk_eur"] if issue and ev["kind"] == "stockout" else None})
        return out

    def _production_predictions(self, f) -> list[dict]:
        out = []
        for o in f["production"]:
            if o["readiness"] == "ready":
                continue
            days = (date.fromisoformat(o["finish_date"]) - self.engine.sap.as_of).days
            value = float(o["quantity"]) * f["cost"][o["material"]]
            out.append({"severity": "critical" if o["readiness"] == "not_ready" else "warning", "area": "Production",
                        "what": f"Production order {o['order']} ({o['material']} @ {o['plant']}) will miss its finish date unless {', '.join(o['short_components']) or 'components'} arrive",
                        "when": o["finish_date"], "in_days": days, "basis": f"BOM netting: {o['component_readiness_pct']}% of components covered by stock + confirmed POs",
                        "at_risk_eur": value})
        return out

    def _supplier_predictions(self, f) -> list[dict]:
        sap, out = self.engine.sap, []
        delay = {s["supplier"]: s["average_delay_days"] or 0 for s in f["suppliers"]}
        for po in sap.section("purchase_orders"):
            if f["scope"] and po["material"] not in f["scope"]:
                continue
            d = delay.get(po["supplier"], 0)
            if d >= 2:
                likely = date.fromisoformat(po["delivery_date"]) + timedelta(days=round(d))
                out.append({"severity": "warning" if d < 7 else "critical", "area": "Suppliers",
                            "what": f"PO {po['po']} ({po['material']}) from {po['supplier']} likely arrives {likely.isoformat()}, not {po['delivery_date']}",
                            "when": likely.isoformat(), "in_days": (likely - sap.as_of).days, "basis": f"supplier's average actual delay +{d:g} days on past receipts",
                            "at_risk_eur": float(po["quantity"]) * f["cost"][po["material"]]})
        return out

    def _shipment_predictions(self, f) -> list[dict]:
        out = []
        for s in f["logistics"]["shipments"]:
            if (f["scope"] and s["material"] not in f["scope"]) or not s.get("delay_days") or s["status"] not in ("in_transit", "planned"):
                continue
            out.append({"severity": "critical" if s["escalate"] else "warning", "area": "Logistics",
                        "what": f"Shipment {s['shipment']} {s['from']}→{s['to']} ({s['quantity']:,} {s['material']}) arrives {s['delay_days']} days late",
                        "when": s["revised_eta"], "in_days": (date.fromisoformat(s["revised_eta"]) - self.engine.sap.as_of).days,
                        "basis": f"carrier revised ETA: {s.get('delay_reason') or 'delay reported'}", "at_risk_eur": float(s["quantity"]) * f["cost"][s["material"]]})
        return out

    def _quality_predictions(self, f) -> list[dict]:
        as_of, out = self.engine.sap.as_of, []
        for imp in f["quality"]["production_impacts"]:
            lot = next(lot for lot in f["quality"]["lots"] if lot["lot"] == imp["lot"])
            if f["scope"] and lot["material"] not in f["scope"]:
                continue
            out.append({"severity": "critical" if lot["status"] == "blocked" else "warning", "area": "Quality",
                        "what": f"Lot {lot['lot']} ({lot['material']}, {lot['status']}) may hold production order {imp['production_order']} due {imp['finish_date']}",
                        "when": lot.get("expected_release") or imp["finish_date"], "in_days": (date.fromisoformat(lot.get("expected_release") or imp["finish_date"]) - as_of).days,
                        "basis": f"QM status {lot['status']}" + (f", expected release {lot['expected_release']}" if lot.get("expected_release") else ""),
                        "at_risk_eur": float(lot["quantity"]) * f["cost"][lot["material"]]})
        for r in f["expiry"]:
            if r["days_left"] <= 90:
                out.append({"severity": "critical" if r["days_left"] < 0 else "warning" if r["days_left"] <= 30 else "info", "area": "Expiry",
                            "what": f"Batch {r['batch']} ({r['material']} @ {r['plant']}) {'has expired' if r['days_left'] < 0 else 'expires'} {r['expiry']}",
                            "when": r["expiry"], "in_days": r["days_left"], "basis": "batch expiry date in SAP", "at_risk_eur": r["value_eur"]})
        return out

    @staticmethod
    def _go(severity, title, why, page, label, at_risk=None, fix_cost=None, **params) -> dict:
        return {"severity": severity, "title": title, "why": why, "at_risk_eur": at_risk, "fix_cost_eur": fix_cost,
                "action": {"kind": "go", "label": label, "params": {"page": page, **params}}}

    def _charts(self, persona: str, material: str | None, ids: set[str] | None = None) -> dict:
        d = self.dashboards.build(persona, material)
        return {"charts": [c for c in d["charts"] if ids is None or c["id"] in ids], "tables": d.get("tables", []), "forecast": d.get("forecast")}

    # -------------------------------------------------------------------- 1. director
    def _director(self, f, material) -> dict:
        learning = self.learning_summary(f)
        value = self._inventory_value(f)
        pending = len(self.store.list_recommendations("pending_review", self.engine.sap.snapshot["id"]))
        actions = self._issue_actions(f, limit=6)
        if pending:
            actions.insert(0, self._go("warning", f"Decide on {pending} recommendation{'s' if pending > 1 else ''} waiting for you", "Proposals from planners and agents need a manager decision",
                                       "approvals", "Review approvals"))
        predictions = (self._stock_predictions(f) + self._production_predictions(f) + self._supplier_predictions(f))
        kpis = self.platform_kpis(f)
        kpis.insert(2, kpi("Inventory value", value, "€", None, "down", "Stock value at standard cost across plants and warehouses", "Σ on hand × standard cost",
                           "MM stock + material master", status="info", hint=f"carrying cost ≈ €{value * CARRYING_COST_RATE:,.0f}/yr at 25%"))
        kpis.append(kpi("Verified outcomes", learning["verified_pct"], "%", 80, "up", "Executed decisions whose real result has been observed in SAP",
                        "observed outcomes ÷ executed recommendations × 100", "governance ledger + SAP documents",
                        hint=f"{learning['observed']} of {learning['executed']} executed"))
        return {"kpis": kpis, "predictions": predictions, "actions": actions, **self._charts("executive", material)}

    # -------------------------------------------------------------------- 2. demand planner
    def _demand(self, f, material) -> dict:
        models = f["models"]
        weight = sum(m["daily"] for m in models) or 1
        bias = sum(m["model"]["bias_pct"] * m["daily"] for m in models) / weight if models else None
        cv = sum(m["demand_cv_pct"] * m["daily"] for m in models) / weight if models else None
        fg = [r for r in f["positions"] if r["material_type"] == "FG"]
        cover = sum(r["on_hand"] for r in fg) / sum(r["requirement"] / 14 for r in fg) if fg and sum(r["requirement"] for r in fg) else None
        outs = [e for e in f["calendar"] if e["kind"] == "stockout"]
        kpis = [
            kpi("Forecast WAPE", self._wape(f), "%", 20, "down", "Sum of absolute forecast errors ÷ sum of actual demand", "Σ|forecast − actual| ÷ Σ actual × 100 (14-day holdout)", "SD billing history (synthetic)"),
            kpi("Forecast bias", bias, "%", 5, "down", "Systematic over- (+) or under-forecasting (−)", "Σ(forecast − actual) ÷ Σ actual × 100", "SD billing history (synthetic)",
                status=_status(abs(bias) if bias is not None else None, 5, "down"), hint="close to 0 is best"),
            kpi("Days of stock cover", cover, " d", 21, "up", "Finished-goods stock ÷ average daily demand", "Σ on hand ÷ Σ daily demand", "MM stock + demand"),
            kpi("Projected stock-outs (60 d)", len(outs), "", 0, "down", "Product × warehouse positions predicted to run out within 60 days",
                "count of projected stock-out dates", "stock + inbound + production − forecast", hint=f"first {outs[0]['date']} at {outs[0]['warehouse']}" if outs else "none predicted"),
            kpi("Demand variability", cv, "%", 15, "down", "Coefficient of variation of daily demand (last 28 days)", "std ÷ mean × 100", "SD billing history (synthetic)"),
        ]
        rows = sorted(models, key=lambda m: -m["model"]["wape_pct"])
        charts = [
            {"id": "wape", "type": "bar", "title": "Forecast error (WAPE) by product and warehouse", "subtitle": "14-day holdout; lower is better; 20% demo target",
             "unit": "%", "reference": 20, "reference_label": "target",
             "rows": [{"label": f"{m['material']} @ {m['warehouse']}", "value": m["model"]["wape_pct"], "status": _status(m["model"]["wape_pct"], 20, "down"),
                       "hint": f"bias {m['model']['bias_pct']:+}% · baseline WAPE {m['baseline']['wape_pct']}%"} for m in rows]},
            {"id": "bias", "type": "diverging", "title": "Forecast bias by product and warehouse", "subtitle": "+ over-forecast · − under-forecast (%)", "unit": "%",
             "rows": [{"label": f"{m['material']} @ {m['warehouse']}", "value": m["model"]["bias_pct"]} for m in rows]},
        ]
        extra = self._charts("inventory", material, {"cover"})
        return {"kpis": kpis, "predictions": self._stock_predictions(f), "actions": self._issue_actions(f, ROLES["demand"]["areas"]),
                "charts": charts + extra["charts"], "forecast": extra["forecast"]}

    # -------------------------------------------------------------------- 3. production planner
    def _production(self, f, material) -> dict:
        orders = f["production"]
        ready = 100 * sum(o["readiness"] == "ready" for o in orders) / len(orders) if orders else None
        shortages = [i for i in f["issues"] if i["area"] == "Components" and i["severity"] != "info"]
        kpis = [
            kpi("Material readiness", ready, "%", 95, "up", "Production orders with all required usable materials ready ÷ scheduled orders",
                "ready orders ÷ scheduled orders × 100", "PP orders + BOM + stock + POs"),
            kpi("BOM shortages", len(shortages), "", 0, "down", "Components short for planned production", "components with a shortfall or late supply", "BOM + MM stock + PUR POs"),
            kpi("Orders at risk", sum(o["readiness"] != "ready" for o in orders), "", 0, "down", "Production orders not fully covered by their finish date",
                "orders with readiness ≠ ready", "PP orders + BOM"),
            kpi("Production schedule adherence", None, "%", 95, "up", "Orders finished on the planned date", "on-time confirmations ÷ orders", "PP order confirmations (history)", available=False),
            kpi("Production downtime", None, " h", None, "down", "Unplanned line downtime", "Σ downtime hours", "PM/PP downtime events", available=False),
        ]
        return {"kpis": kpis, "predictions": self._production_predictions(f) + self._quality_predictions(f)[:3],
                "actions": self._issue_actions(f, ROLES["production"]["areas"]), **self._charts("production", material)}

    # -------------------------------------------------------------------- 4. procurement
    def _procurement(self, f, material) -> dict:
        sap = self.engine.sap
        hist = [h for h in sap.section("po_history") if not f["scope"] or h["material"] in f["scope"]]
        on_time = 100 * sum(h["received_date"] <= h["promised_date"] for h in hist) / len(hist) if hist else None
        defects = 100 * sum(h["quality_rejected"] for h in hist) / sum(h["quantity_received"] for h in hist) if hist and sum(h["quantity_received"] for h in hist) else None
        actual = [(date.fromisoformat(h["received_date"]) - date.fromisoformat(h["promised_date"])).days for h in hist]
        sup = {s["name"]: s for s in sap.section("suppliers")}
        ppv_num = ppv_den = 0.0
        for po in sap.section("purchase_orders"):
            s = sup.get(po["supplier"])
            if s and s.get("unit_price_eur") is not None and (not f["scope"] or po["material"] in f["scope"]):
                std = f["cost"][po["material"]]
                ppv_num += (s["unit_price_eur"] - std) * float(po["quantity"])
                ppv_den += std * float(po["quantity"])
        kpis = [
            kpi("Supplier on-time delivery", on_time, "%", 95, "up", "Receipts on or before the promised date ÷ receipts", "on-time receipts ÷ receipts × 100", "PUR receipts (po_history)"),
            kpi("Actual vs planned lead time", sum(actual) / len(actual) if actual else None, " d", 1, "down", "Average days received after the promised date",
                "Σ(received − promised) ÷ receipts", "PUR receipts (po_history)", hint="positive = late"),
            kpi("Purchase price variance", 100 * ppv_num / ppv_den if ppv_den else None, "%", 2, "down", "Purchase price vs standard cost, weighted by open PO quantity",
                "Σ(price − standard) × qty ÷ Σ standard × qty × 100", "PUR prices + material standard cost"),
            kpi("Supplier defect rate", defects, "%", 1, "down", "Quantity rejected by quality ÷ quantity received", "rejected ÷ received × 100", "PUR receipts + QM"),
            kpi("High-risk suppliers", sum(s["risk_rating"] == "high" for s in f["suppliers"]), "", 0, "down", "Suppliers rated high continuity risk", "risk score ≥ threshold", "supplier scorecard"),
        ]
        return {"kpis": kpis, "predictions": self._supplier_predictions(f) + [p for p in self._production_predictions(f)][:2],
                "actions": self._issue_actions(f, ROLES["procurement"]["areas"]), **self._charts("procurement", material)}

    # -------------------------------------------------------------------- 5. warehouse manager
    def _warehouse(self, f, material) -> dict:
        counts = f["counts"]
        accurate = 100 * sum(c["status"] in ("matched", "within_tolerance", "explained") for c in counts) / len(counts) if counts else None
        value = self._inventory_value(f)
        fg = [r for r in f["positions"] if r["material_type"] == "FG"]
        daily_value = sum(r["requirement"] / 14 * f["cost"][r["material"]] for r in fg)
        expiring = sum(r["value_eur"] for r in f["expiry"] if r["days_left"] <= 90)
        turns = self._annual_cogs(f) / value if value else None
        kpis = [
            kpi("Stock accuracy", accurate, "%", 98, "up", "Counts matching the book (or fully explained) ÷ counts", "accurate counts ÷ counts × 100", "WM/IM physical inventory"),
            kpi("Inventory turnover", turns, "×", 8, "up", "Cost of goods sold ÷ average inventory value", "annualised COGS ÷ stock value", "MM stock + standard cost + demand"),
            kpi("Days of inventory", sum(r["stock_value_eur"] for r in fg) / daily_value if daily_value else None, " d", 30, "down",
                "Finished-goods stock value ÷ daily cost of sales", "FG stock value ÷ (daily demand × standard cost)", "MM stock + demand"),
            kpi("Expiry-risk value (90 d)", expiring, "€", 0, "down", "Value of batches expired or expiring within 90 days", "Σ batch quantity × cost, expiry ≤ 90 days", "MM batch expiry dates"),
            kpi("Picking accuracy", None, "%", 99.5, "up", "Order lines picked without error", "correct lines ÷ picked lines", "WM/EWM picking confirmations", available=False),
        ]
        actions = self._issue_actions(f, ROLES["warehouse"]["areas"])
        for c in counts:
            if c["status"] in ("investigate", "explained"):
                rec = (c.get("recommendation") or {}).get("action", "review").replace("_", " ")
                actions.append({"severity": "warning" if c["status"] == "investigate" else "info", "title": f"{rec.capitalize()} for count {c['count_id']}",
                                "why": f"{c['material']} @ {c['plant']}: book {c['book_quantity']:,} vs counted {c['counted_quantity']:,} ({c['status']})",
                                "at_risk_eur": c["difference_value_eur"], "fix_cost_eur": None, "action": {"kind": "stocktake", "label": "Open stocktake", "params": {}}})
        for r in f["expiry"]:
            if 0 <= r["days_left"] <= 90:
                actions.append({"severity": "warning", "title": f"Ship batch {r['batch']} first (FEFO)", "why": f"{r['material']} @ {r['plant']} expires {r['expiry']}",
                                "at_risk_eur": r["value_eur"], "fix_cost_eur": None, "action": {"kind": "go", "label": "See stock", "params": {"page": "inventory"}}})
        inv = self._charts("inventory", material, {"understock", "gap", "expiry"})
        st = self._charts("stocktake", material, {"explained"})
        return {"kpis": kpis, "predictions": self._stock_predictions(f) + [p for p in self._quality_predictions(f) if p["area"] == "Expiry"],
                "actions": actions, "charts": inv["charts"] + st["charts"], "forecast": inv["forecast"]}

    # -------------------------------------------------------------------- 6. logistics manager
    def _logistics(self, f, material) -> dict:
        ships = [s for s in f["logistics"]["shipments"] if not f["scope"] or s["material"] in f["scope"]]
        done_or_moving = [s for s in ships if s["status"] in ("in_transit", "planned", "delivered")]
        on_time = 100 * sum(not s.get("delay_days") for s in done_or_moving) / len(done_or_moving) if done_or_moving else None
        lanes = {(lane["from"], lane["to"]): lane for lane in f["logistics"]["lanes"]}
        costed = [(float(s["quantity"]), lanes[(s["from"], s["to"])]) for s in ships if (s["from"], s["to"]) in lanes]
        transit = [(date.fromisoformat(s["revised_eta"]) - date.fromisoformat(s["departed"])).days for s in ships if s.get("departed") and s.get("revised_eta")]
        kpis = [
            kpi("Delivery OTIF", on_time, "%", 95, "up", "Shipments arriving on the planned ETA ÷ shipments", "shipments without delay ÷ shipments × 100", "LE shipments (revised ETA)"),
            kpi("Freight cost per unit", sum(q * lane["cost_per_unit"] for q, lane in costed) / sum(q for q, _ in costed) if costed else None, "€", 0.6, "down",
                "Transfer freight cost ÷ units moved", "Σ qty × lane cost ÷ Σ qty", "lane rates (LE)"),
            kpi("Average transit time", sum(transit) / len(transit) if transit else None, " d", 7, "down", "Days from departure to (revised) arrival", "Σ(ETA − departed) ÷ shipments", "LE shipments"),
            kpi("Emergency shipments", sum(s["mode"] == "air" for s in ships if s["status"] in ("in_transit", "planned")), "", 0, "down",
                "Shipments moved by air to recover service", "air shipments in flight", "LE shipments (mode)"),
            kpi("Transport utilisation", None, "%", 85, "up", "Used vs available truck / container capacity", "loaded ÷ capacity", "TM load plans", available=False),
        ]
        actions = [a for a in self._issue_actions(f, ROLES["logistics"]["areas"]) if "Transfer" in a["title"] or a["area"] == "Sales orders"]
        for a in f["logistics"]["proposed_actions"]:
            if a["action"] == "escalate_shipment_delay":
                actions.append({"severity": "warning", "title": f"Escalate {a['shipment']} with {a['carrier']}", "why": f"{a['delay_days']} days late: {a['reason']}",
                                "at_risk_eur": None, "fix_cost_eur": None, "action": {"kind": "go", "label": "Open shipments", "params": {"page": "suppliers"}}})
        return {"kpis": kpis, "predictions": self._shipment_predictions(f) + self._stock_predictions(f)[:4], "actions": actions, **self._charts("logistics", material)}

    # -------------------------------------------------------------------- 7. quality manager
    def _quality(self, f, material) -> dict:
        lots = [lot for lot in f["quality"]["lots"] if not f["scope"] or lot["material"] in f["scope"]]
        stock = [s for s in self.engine.sap.section("stock") if not f["scope"] or s["material"] in f["scope"]]
        blocked = sum(float(s["quantity"]) * f["cost"][s["material"]] for s in stock if s["status"] == "blocked")
        held = sum(float(s["quantity"]) * f["cost"][s["material"]] for s in stock if s["status"] == "quality_inspection")
        value = self._inventory_value(f) or 1
        expired = sum(r["value_eur"] for r in f["expiry"] if r["days_left"] < 0)
        waiting = [(date.fromisoformat(lot["expected_release"]) - self.engine.sap.as_of).days for lot in lots if lot["status"] == "inspection" and lot.get("expected_release")]
        kpis = [
            kpi("Batch rejection", 100 * sum(lot["status"] in ("blocked", "rejected") for lot in lots) / len(lots) if lots else None, "%", 2, "down",
                "Inspection lots rejected or blocked ÷ lots", "rejected lots ÷ lots × 100", "QM inspection lots"),
            kpi("Blocked stock value", blocked, "€", 0, "down", "Stock in blocked status at standard cost", "Σ blocked qty × cost", "MM stock status"),
            kpi("Stock in inspection", held, "€", None, "down", "Stock waiting for a usage decision", "Σ inspection qty × cost", "MM stock status", status="info"),
            kpi("Expiry loss", 100 * expired / value, "%", 0.5, "down", "Expired stock value ÷ inventory value", "expired value ÷ stock value × 100", "MM batch expiry dates"),
            kpi("Quality-release lead time", sum(waiting) / len(waiting) if waiting else 0, " d", 3, "down", "Days until lots in inspection are released", "Σ(expected release − today) ÷ lots", "QM inspection lots"),
        ]
        actions = []
        for a in f["quality"]["proposed_actions"]:
            if f["scope"] and a.get("material") not in f["scope"]:
                continue
            actions.append({"severity": "warning", "title": f"{a['action'].replace('_', ' ').capitalize()}: lot {a.get('lot', '')} ({a.get('material', '')})",
                            "why": f"needed for production; expected release {a.get('expected_release', 'n/a')}", "at_risk_eur": None, "fix_cost_eur": None,
                            "action": {"kind": "go", "label": "Open quality", "params": {"page": "suppliers"}}})
        for r in f["expiry"]:
            if r["days_left"] < 0:
                actions.append({"severity": "critical", "title": f"Block and write off expired batch {r['batch']}", "why": f"{r['material']} @ {r['plant']} expired {r['expiry']} but is unrestricted",
                                "at_risk_eur": r["value_eur"], "fix_cost_eur": None, "action": {"kind": "go", "label": "See stock", "params": {"page": "inventory"}}})
        status_count: dict[str, int] = {}
        for lot in lots:
            status_count[lot["status"]] = status_count.get(lot["status"], 0) + 1
        charts = [
            {"id": "lots", "type": "bar", "title": "Inspection lots by status", "subtitle": "QM lots in the snapshot", "unit": "",
             "rows": [{"label": k, "value": v, "status": {"blocked": "critical", "inspection": "warning", "released": "good"}.get(k, "info")} for k, v in sorted(status_count.items())]},
            {"id": "held", "type": "bar", "title": "Stock not usable, by material (€)", "subtitle": "blocked + in inspection, at standard cost", "unit": " €",
             "rows": [{"label": f"{s['material']} @ {s['plant']} ({s['status'].replace('_', ' ')})", "value": round(float(s["quantity"]) * f["cost"][s["material"]]),
                       "status": "critical" if s["status"] == "blocked" else "warning"} for s in stock if s["status"] != "unrestricted"]},
        ]
        return {"kpis": kpis, "predictions": self._quality_predictions(f), "actions": actions,
                "charts": charts + self._charts("inventory", material, {"expiry"})["charts"]}

    # -------------------------------------------------------------------- 8. finance
    def _finance(self, f, material) -> dict:
        value = self._inventory_value(f)
        excess = sum(r["excess_value_eur"] for r in f["positions"])
        sc = self._supply_chain_cost(f)
        learning = self.learning_summary(f)
        expedite = sum(i["fix_cost_eur"] or 0 for i in f["issues"] if i["severity"] != "info")
        kpis = [
            kpi("Working capital in stock", value, "€", None, "down", "Inventory value at standard cost", "Σ on hand × standard cost", "MM stock + material master", status="info"),
            kpi("Inventory carrying cost", value * CARRYING_COST_RATE, "€", None, "down", "Annual cost of holding the stock", "stock value × 25% per year (demo rate)", "MM stock + finance rate", status="info", hint="per year"),
            kpi("Expedite spending (proposed)", expedite, "€", None, "down", "Direct cost of the fixes proposed now", "Σ fix costs (transfers) of open issues", "lanes + proposals", status="warning" if expedite else "good"),
            kpi("Verified savings", learning["realized_impact_eur"], "€", None, "up", "Savings confirmed against SAP outcomes (not approvals)", "Σ realised impact of verified outcomes", "governance ledger + SAP documents",
                status="info", hint=f"{learning['verified']} verified outcome(s)"),
            kpi("Excess stock value", excess, "€", 0, "down", "Stock above 2× target, at cost", "Σ excess × cost", "MM stock + demand"),
            kpi("Cash-to-cash cycle", None, " d", None, "down", "Days inventory + days receivable − days payable", "DIO + DSO − DPO", "FI AR/AP ledgers", available=False),
        ]
        actions = sorted(self._issue_actions(f), key=lambda a: -((a["at_risk_eur"] or 0) - (a["fix_cost_eur"] or 0)))[:8]
        for a in actions:
            if a["at_risk_eur"] and a["fix_cost_eur"]:
                a["why"] += f" · protects €{a['at_risk_eur']:,.0f} for €{a['fix_cost_eur']:,.0f}"
        by_loc: dict[str, float] = {}
        for r in f["positions"]:
            by_loc[r["location"]] = by_loc.get(r["location"], 0) + r["stock_value_eur"]
        area_risk: dict[str, float] = {}
        for i in f["issues"]:
            if i["severity"] != "info":
                area_risk[i["area"]] = area_risk.get(i["area"], 0) + (i["at_risk_eur"] or 0)
        charts = [
            {"id": "wc", "type": "bar", "title": "Working capital in stock by location (€)", "subtitle": "stock value at standard cost", "unit": " €",
             "rows": [{"label": k, "value": round(v), "status": "info"} for k, v in sorted(by_loc.items(), key=lambda x: -x[1])]},
            {"id": "cost", "type": "bar", "title": "Supply-chain cost, next 30 days (€, estimate)", "subtitle": "procurement · transport · storage · expiry · exceptions", "unit": " €",
             "rows": [{"label": k, "value": v, "status": "info"} for k, v in sc["parts"].items()]},
            {"id": "risk", "type": "bar", "title": "Value at risk by area (€)", "subtitle": "open critical and warning issues, at standard cost (can overlap)", "unit": " €",
             "rows": [{"label": k, "value": round(v), "status": "warning"} for k, v in sorted(area_risk.items(), key=lambda x: -x[1])]},
        ]
        predictions = [{"severity": "warning", "area": "Cost", "what": f"Expected exception spend of €{expedite:,.0f} if the proposed transfers run", "when": None, "in_days": None,
                        "basis": "lane cost × proposed transfer quantities", "at_risk_eur": None}] if expedite else []
        predictions += [p for p in self._quality_predictions(f) if p["area"] == "Expiry"] + self._stock_predictions(f)[:4]
        return {"kpis": kpis, "predictions": predictions, "actions": actions, "charts": charts}

    # -------------------------------------------------------------------- 9. AI / MLOps
    def _mlops(self, f, material) -> dict:
        learning = self.learning_summary(f)
        models = f["models"]
        weight = sum(m["daily"] for m in models) or 1
        mae = sum(m["model"]["mae"] * m["daily"] for m in models) / weight if models else None
        kpis = [
            kpi("Prediction WAPE", self._wape(f), "%", 20, "down", "Forecast error, demand-weighted", "Σ|forecast − actual| ÷ Σ actual × 100", "holdout backtest (synthetic history)", hint=f"MAE {mae:.1f} units/day" if mae else None),
            kpi("Error vs baseline", learning["error_reduction_pct"], "%", 10, "up", "WAPE reduction vs same-weekday-last-week baseline", "1 − WAPE(model) ÷ WAPE(baseline)", "holdout backtest", hint="higher = model adds more value"),
            kpi("Model drift", learning["drift_max_pts"], " pts", 2, "down", "Largest WAPE increase, recent 7 days vs the 7 days before", "max(recent WAPE − earlier WAPE)", "holdout backtest"),
            kpi("Verified outcomes", learning["verified_pct"], "%", 80, "up", "Executed recommendations whose real result was observed", "observed ÷ executed × 100", "governance ledger + SAP documents",
                hint=f"{learning['observed']} of {learning['executed']}"),
            kpi("Recommendation acceptance", learning["acceptance_pct"], "%", None, "up", "Decided recommendations accepted by managers", "accepted ÷ decided × 100", "governance ledger",
                status="info", hint="approval ≠ proof: see verified outcomes"),
            kpi("Realised business impact", learning["realized_impact_eur"], "€", None, "up", "Impact confirmed against SAP outcomes", "Σ realised impact of verified outcomes", "governance ledger", status="info"),
        ]
        predictions = [{"severity": "warning", "area": "Model", "what": f"Forecast error rising for {m['material']} @ {m['warehouse']} (+{m['drift']['change_pts']} pts)",
                        "when": None, "in_days": None, "basis": f"recent WAPE {m['drift']['recent_wape_pct']}% vs {m['drift']['earlier_wape_pct']}%", "at_risk_eur": None}
                       for m in models if m["drift"]["change_pts"] >= 2]
        actions = []
        if learning["executed"] - learning["observed"]:
            actions.append(self._go("warning" if learning["overdue"] else "info", f"Record the real outcome of {learning['executed'] - learning['observed']} executed decision(s)",
                                    "Learning only counts outcomes observed in SAP, not approvals", "approvals", "Record outcomes"))
        for p in predictions:
            actions.append({"severity": "warning", "title": "Review and retrain the forecast for " + p["what"].split(" for ")[1].split(" (")[0],
                            "why": p["basis"], "at_risk_eur": None, "fix_cost_eur": None, "action": {"kind": "ask", "label": "Ask the Learning Agent", "params": {"question": f"Why is the {p['what'].lower()}?"}}})
        if learning["override_reasons"]:
            actions.append(self._go("info", f"Review {len(learning['override_reasons'])} manager override reason(s)", "Where experts knew something the model missed", "approvals", "See overrides"))
        rows = sorted(models, key=lambda m: m["error_reduction_pct"] or 0)
        charts = [
            {"id": "uplift", "type": "bar", "title": "Error reduction vs baseline by product and warehouse", "subtitle": "1 − WAPE(model) ÷ WAPE(same weekday last week)", "unit": "%", "reference": 10,
             "rows": [{"label": f"{m['material']} @ {m['warehouse']}", "value": m["error_reduction_pct"], "status": _status(m["error_reduction_pct"], 10, "up"),
                       "hint": f"model {m['model']['wape_pct']}% vs baseline {m['baseline']['wape_pct']}%"} for m in rows]},
            {"id": "drift", "type": "diverging", "title": "Drift: recent vs earlier forecast error (WAPE pts)", "subtitle": "+ = getting worse", "unit": " pts",
             "rows": [{"label": f"{m['material']} @ {m['warehouse']}", "value": m["drift"]["change_pts"]} for m in models]},
        ]
        return {"kpis": kpis, "predictions": predictions, "actions": actions, "charts": charts,
                "tables": [{"title": "Override reasons", "columns": ["Recommendation", "Kind", "Reason"],
                            "rows": [[r["recommendation_id"], r["kind"], r["reason"]] for r in learning["override_reasons"]]}] if learning["override_reasons"] else []}

    # ------------------------------------------------------------------ learning (data moat) view
    def learning(self) -> dict:
        f = self._facts(None)
        s = self.learning_summary(f)
        moat = [
            {"metric": "Prediction error reduction", "proves": "New models forecast more accurately than the previous approach",
             "status": "measured", "value": f"{s['error_reduction_pct']}% lower WAPE than the baseline" if s["error_reduction_pct"] is not None else "—"},
            {"metric": "Verified real-world outcomes", "proves": "Training data is linked to actual SAP transactions and results",
             "status": "measured" if s["observed"] else "awaiting data", "value": f"{s['observed']} of {s['executed']} executed decisions observed"},
            {"metric": "Human override rate and reasons", "proves": "Where experts know something the AI missed",
             "status": "measured" if s["decided"] else "awaiting data", "value": f"{s['override_pct']}% overridden" if s["override_pct"] is not None else "no decisions yet"},
            {"metric": "Recommendation performance", "proves": "Executed recommendations produce better measured outcomes",
             "status": "measured" if s["observed"] else "awaiting data", "value": f"{s['achieved_pct']}% achieved, €{s['realized_impact_eur']:,.0f} realised" if s["observed"] else "needs observed outcomes"},
            {"metric": "Customer-specific model improvement", "proves": "How well the system learns this company's supply chain",
             "status": "measured", "value": f"{s['error_reduction_pct']}% better than baseline on this customer's data (synthetic history)"},
            {"metric": "Industry model uplift", "proves": "Permitted multi-customer learning beats local-only models",
             "status": "not yet measured", "value": "needs customer permission and cross-customer training"},
            {"metric": "Generalisation to new customers", "proves": "Learning from previous companies helps a newly onboarded one",
             "status": "not yet measured", "value": "needs a second real customer onboarding"},
        ]
        return {"as_of": self.engine.sap.as_of.isoformat(), "summary": s, "data_moat": moat, "outcomes": f["outcomes"],
                "models": [{k: m[k] for k in ("material", "warehouse", "model", "baseline", "error_reduction_pct", "drift", "demand_cv_pct")} for m in f["models"]],
                "note": "A human approving a recommendation is not proof it was right: only outcomes observed in SAP count as verified."}
