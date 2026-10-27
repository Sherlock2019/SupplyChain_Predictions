# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/moat.py
# What this module is: the "Customer Data Intelligence Flywheel" view of the SPARC gateway (GET /api/v1/moat): consent gate for
# industry learning, comparison of customer-only vs generic vs industry vs cold-start forecast models, evidence per data moat,
# flywheel stage counts, verified value by benefit line and the five moat-strength metrics.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Customer Data Intelligence Flywheel: how private data, human expertise and verified outcomes become intelligence.

private customer data -> AI prediction & optimisation -> real human decisions (approve / modify / reject + why)
  -> verified business outcomes -> validated labels -> evaluated models -> better predictions

Principles enforced here:
  * Customer data stays the customer's: industry learning uses a customer's data only with its recorded consent.
  * An approval is not a label of success; only outcomes observed in SAP are.
  * More data is not automatically better: industry and generic models are always compared with the customer-only
    model on the customer's own holdout, and a cold start measures generalisation to a newly onboarded customer.
"""
from __future__ import annotations

from backend.app.forecasting import evaluate_models, pooled_evaluation
from backend.app.store import Store
from backend.app.tenants import DEFAULT_TENANT, TenantRegistry

# (id, name, what it learns, potential) of the six data moats.
MOAT_POTENTIAL = [
    ("erp_history", "Historical ERP data", "Demand patterns, purchasing history, inventory movements, production schedules", "Medium"),
    ("supplier_reality", "Real supplier performance", "Actual lead times, reliability, price and quality variations", "Very high"),
    ("human_expertise", "Human decisions and expertise", "Why planners approve, modify or reject recommendations", "Very high"),
    ("verified_outcomes", "Verified business outcomes", "Which decisions actually reduced shortages, costs, delays and waste", "Very high"),
    ("operating_knowledge", "Company-specific operating knowledge", "Workflows, exceptions, constraints, production and logistics relationships", "High"),
    ("industry_learning", "Approved industry-wide learning", "Patterns learned across participating companies", "Potentially very high"),
]

# Where verified value lands in the financial model (recommendation kind -> benefit line).
VALUE_LINES = {
    "stock_balance": "Better warehouse stock balancing", "sales_orders": "Better warehouse stock balancing",
    "factory_readiness": "Fewer material shortages", "supplier_risk": "Improved supplier predictions", "quality": "Fewer material shortages",
    "logistics": "Improved supplier predictions", "stocktake": "Reduced expiry-related waste", "inventory": "Better demand forecasts",
}

# Who owns what (customer vs platform) — static table shown in the UI.
OWNERSHIP = [
    {"aspect": "Proprietary data", "customer": "Its confidential SAP and operational records", "platform": "No ownership of customer data"},
    {"aspect": "Human knowledge", "customer": "The expertise of its planners and managers", "platform": "Reusable methods for capturing and evaluating decisions"},
    {"aspect": "Trained intelligence", "customer": "Its own approved models and calibration", "platform": "Authorised industry models and evaluation methods"},
    {"aspect": "Competitive benefit", "customer": "Better cost, service and resilience", "platform": "Better product performance, industry expertise and differentiation"},
    {"aspect": "Growth", "customer": "More verified outcomes within the company", "platform": "More permitted learning across companies"},
]


# ===== CLASS: MoatEngine =====
# ID: F0250 · class · used
# ORIGINAL FILE: backend/app/moat.py:43-179
# ROLE: Builds the moat / flywheel view across tenants (needs the registry to compare customers).
# FIELDS:
#   registry: TenantRegistry, store: Store.
# CALLED BY:
#   <- F0017 create_app() (calls)
# CALLS:
#   (none found)
class MoatEngine:
    # ===== FUNCTION: MoatEngine.__init__() =====
    # ID: F0251 · method · used (framework)
    # ORIGINAL FILE: backend/app/moat.py:44-45
    # ROLE: Keep registry and store.
    # INPUTS:
    #   registry: TenantRegistry, store: Store.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0391 TenantRegistry (references)
    #   -> F0354 Store (references)
    def __init__(self, registry: TenantRegistry, store: Store):
        self.registry, self.store = registry, store

    # -------------------------------------------------------------- consent gate
    # ===== FUNCTION: MoatEngine.consent() =====
    # ID: F0252 · method · used
    # ORIGINAL FILE: backend/app/moat.py:48-54
    # ROLE: Consent of a tenant to industry learning: a recorded decision wins; otherwise synthetic demo customers are opted in and the
    #       primary customer is opted out.
    # INPUTS:
    #   tenant_id: str.
    # OUTPUT:
    #   dict -> {"tenant", "industry_learning": bool, "source"}.
    # CALLED BY:
    #   <- F0058 create_app.moat_consent() (calls)
    #   <- F0254 MoatEngine.model_comparison() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    # CALLS:
    #   -> F0384 Store.consent() (calls)
    def consent(self, tenant_id: str) -> dict:
        """Recorded consent wins; without a record, synthetic demo customers are opted in and real ones are opted out."""
        row = self.store.consent(tenant_id)
        if row:
            return {"tenant": tenant_id, "industry_learning": row["industry_learning"], "source": f"recorded by {row['updated_by']} {row['updated_at'][:10]}"}
        synthetic = tenant_id != DEFAULT_TENANT  # the generated demo customers; the primary customer starts opted out
        return {"tenant": tenant_id, "industry_learning": bool(synthetic), "source": "default: synthetic demo customer (simulated consent)" if synthetic else "default: not shared"}

    # ===== FUNCTION: MoatEngine._series() =====
    # ID: F0253 · method · used
    # ORIGINAL FILE: backend/app/moat.py:56-58
    # ROLE: The tenant's non-zero daily demand levels (one per material x DC), sorted, as a hashable tuple for the cached evaluations.
    # INPUTS:
    #   tenant_id: str.
    # OUTPUT:
    #   tuple[float, ...].
    # CALLED BY:
    #   <- F0254 MoatEngine.model_comparison() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    # CALLS:
    #   -> F0407 SapRepository.section() (calls)
    #   -> F0393 TenantRegistry.get() (calls)
    def _series(self, tenant_id: str) -> tuple[float, ...]:
        demand = self.registry.get(tenant_id).sap.section("warehouse_demand_daily")
        return tuple(sorted(float(v) for by_dc in demand.values() for v in by_dc.values() if float(v)))

    # -------------------------------------------------------------- model comparison
    # ===== FUNCTION: MoatEngine.model_comparison() =====
    # ID: F0254 · method · used
    # ORIGINAL FILE: backend/app/moat.py:61-89
    # ROLE: Demand-weighted WAPE of customer-only XGBoost vs naive baseline vs generic (all consenting customers) vs industry (same
    #       industry, + own history if this customer consents) vs cold start.
    # INPUTS:
    #   tenant_id: str.
    # OUTPUT:
    #   dict -> customer_only_wape, baseline_wape, generic_wape, industry_wape, cold_start_wape, participants, notes.
    # CALLED BY:
    #   <- F0255 MoatEngine.view() (calls)
    # CALLS:
    #   -> F0393 TenantRegistry.get() (calls)
    #   -> F0253 MoatEngine._series() (calls)
    #   -> F0529 evaluate_models() (calls)
    #   -> F0252 MoatEngine.consent() (calls)
    #   -> F0530 pooled_evaluation() (calls)
    def model_comparison(self, tenant_id: str) -> dict:
        ctx = self.registry.get(tenant_id)
        target = self._series(tenant_id)
        evals = [evaluate_models(b) for b in target]
        weight = sum(target) or 1
        # Weighted average of per-series WAPE by demand volume.
        customer_only = sum(e["model"]["wape_pct"] * b for e, b in zip(evals, target, strict=True)) / weight
        baseline = sum(e["baseline"]["wape_pct"] * b for e, b in zip(evals, target, strict=True)) / weight
        others = [t for t in self.registry.files if t != tenant_id]
        # CONSENT GATE: only customers that agreed can contribute their data.
        consenting = [t for t in others if self.consent(t)["industry_learning"]]
        same_industry = [t for t in consenting if self.registry.get(t).industry == ctx.industry]
        own_consent = self.consent(tenant_id)["industry_learning"]
        donors = lambda ids: tuple(sorted(b for t in ids for b in self._series(t)))  # noqa: E731
        generic = pooled_evaluation(target, donors(consenting), False) if consenting else None
        industry = pooled_evaluation(target, donors(same_industry), own_consent) if same_industry else None
        cold = pooled_evaluation(target, donors(same_industry), False, scale_by_history=False) if same_industry else None
        wape = lambda r: None if r is None else r["wape_pct"]  # noqa: E731
        return {
            "customer_only_wape": round(customer_only, 2), "baseline_wape": round(baseline, 2),
            "generic_wape": wape(generic), "industry_wape": wape(industry), "cold_start_wape": wape(cold),
            "participants": {"industry": ctx.industry, "same_industry_consenting": same_industry, "all_consenting": len(consenting),
                             "this_customer_contributes": own_consent},
            "notes": [
                "Customer-only = XGBoost per series on this customer's history; baseline = same weekday last week.",
                "Generic = one model trained on every consenting customer of every industry (not this customer), scaled to this customer's demand level.",
                f"Industry = consenting {ctx.industry_label} customers" + (" plus this customer's history" if own_consent else " (this customer does not contribute)") + ".",
                "Cold start = industry model with none of this customer's history, scaled by its planned daily demand (a newly onboarded customer).",
                "Caution: the demo histories are synthetic and share one seasonal shape, which flatters pooled models; real customers differ, so validate on real holdouts before promoting an industry model.",
            ],
        }

    # -------------------------------------------------------------- the view
    # ===== FUNCTION: MoatEngine.view() =====
    # ID: F0255 · method · used
    # ORIGINAL FILE: backend/app/moat.py:92-179
    # ROLE: The full moat page: value proposition, evidence per moat, flywheel stage counts, the five moat metrics, model comparison,
    #       consent of this and peer customers, verified value by benefit line, ownership, decisions and outcomes.
    # INPUTS:
    #   tenant_id: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0057 create_app.moat_view() (calls)
    # CALLS:
    #   -> F0393 TenantRegistry.get() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0290 RoleCenter.learning() (calls)
    #   -> F0388 Store.decision_stats() (calls)
    #   -> F0380 Store.list_outcomes() (calls)
    #   -> F0367 Store.list_recommendations() (calls)
    #   -> F0254 MoatEngine.model_comparison() (calls)
    #   -> F0252 MoatEngine.consent() (calls)
    #   -> F0407 SapRepository.section() (calls)
    #   -> F0406 SapRepository.has() (calls)
    #   -> F0224 SupplyChainEngine.network_map() (calls)
    #   -> F0253 MoatEngine._series() (calls)
    def view(self, tenant_id: str) -> dict:
        ctx = self.registry.get(tenant_id)
        sap, engine, roles = ctx.sap, ctx.engine, ctx.roles
        snapshot = sap.snapshot["id"]
        learning = roles.learning()
        s = learning["summary"]
        decisions = self.store.decision_stats(snapshot)
        outcomes = self.store.list_outcomes(snapshot)
        recs = self.store.list_recommendations(snapshot_id=snapshot)
        kinds = {r["id"]: r["kind"] for r in recs}
        models = self.model_comparison(tenant_id)
        consent = self.consent(tenant_id)

        # 1. evidence per data moat
        records = sum(len(sap.section(k)) for k in ("sales_orders", "purchase_orders", "po_history", "stock", "production_orders", "shipments", "quality_lots", "stocktake_counts", "goods_movements") if sap.has(k))
        net = engine.network_map()
        gaps = sorted(net["suppliers"], key=lambda x: -(x["learned_vs_sap_days"] or 0))
        reality = [f"{x['name']}: SAP promises {x['sap_lead_time_days']} d, actually {x['learned_time_to_deliver_days']:g} d" for x in gaps if (x["learned_vs_sap_days"] or 0) > 0][:3]
        lanes = sap.section("lanes")
        evidence = {
            "erp_history": {"value": f"{records} SAP records · {len(self._series(tenant_id))} demand series × 180 days",
                            "learned": f"forecast WAPE {models['customer_only_wape']}% vs {models['baseline_wape']}% for the simple baseline"},
            "supplier_reality": {"value": f"{len(sap.section('po_history'))} receipts from {len(net['suppliers'])} suppliers",
                                 "learned": "; ".join(reality) or "suppliers deliver on promise"},
            "human_expertise": {"value": f"{decisions['decided']} decisions · {decisions['modified']} modified · {decisions['rejected']} rejected",
                                "learned": (", ".join(f"{k.replace('_', ' ')} ×{v}" for k, v in decisions["reason_codes"].items()) or "no override reasons recorded yet")},
            "verified_outcomes": {"value": f"{s['observed']} of {s['executed']} executed decisions observed in SAP",
                                  "learned": f"{s['achieved_pct']}% achieved · €{s['realized_impact_eur']:,.0f} realised" if s["observed"] else "awaiting the first observed outcome"},
            "operating_knowledge": {"value": f"{len(sap.section('bom'))} BOM rules · {len(lanes)} transfer lanes · {len(sap.section('plants'))} sites with contacts",
                                    "learned": "constraints used by every optimisation (lanes, BOM, safety stock, quality status)"},
            "industry_learning": {"value": f"{len(models['participants']['same_industry_consenting'])} other consenting {ctx.industry_label} customer(s)",
                                  "learned": ("industry model WAPE " + (f"{models['industry_wape']}%" if models["industry_wape"] is not None else "n/a") +
                                              f" vs customer-only {models['customer_only_wape']}%")},
        }
        moats = [{"id": mid, "name": name, "learns": learns, "potential": potential, **evidence[mid]} for mid, name, learns, potential in MOAT_POTENTIAL]

        # 2. flywheel stages with live counts
        labels = [o for o in outcomes if o["status"] != "awaiting_observation"]
        flywheel = [
            {"stage": "Private customer data", "detail": "SAP · suppliers · inventory · demand · production", "count": records, "unit": "records"},
            {"stage": "AI prediction & optimisation", "detail": "forecast shortages, compare suppliers, recommend replenishment",
             "count": self.store.counts(snapshot)["analyses"], "unit": "analyses"},
            {"stage": "Real human decisions", "detail": "approve · modify · reject · explain why", "count": decisions["decided"], "unit": "decisions"},
            {"stage": "Verified business outcomes", "detail": "actual delivery · costs · delays · stock-outs · quality", "count": len(labels), "unit": "outcomes"},
            {"stage": "Supervised learning + MLOps", "detail": "validated labels → better datasets → evaluated models", "count": len(labels), "unit": "validated labels",
             "extra": f"{len(learning['models'])} models evaluated on holdout"},
        ]

        # 3. value realised so far, by benefit line (verified outcomes only)
        realised: dict[str, float] = {}
        for o in outcomes:
            if o["achieved"] and o["realized_impact_eur"]:
                line = VALUE_LINES.get(kinds.get(o["recommendation_id"], ""), "Faster planning")
                realised[line] = realised.get(line, 0) + o["realized_impact_eur"]

        # 4. the five moat-strength metrics
        uplift = None if models["baseline_wape"] == 0 else round(100 * (1 - models["customer_only_wape"] / models["baseline_wape"]), 1)
        personal = None if models["generic_wape"] is None else round(models["generic_wape"] - models["customer_only_wape"], 2)
        industry_adv = None if models["industry_wape"] is None else round(models["customer_only_wape"] - models["industry_wape"], 2)
        metrics = [
            {"name": "Verified decision outcomes", "value": s["observed"], "unit": "", "display": f"{s['observed']} of {s['executed']}",
             "question": "How many AI recommendations have complete, reliable real-world result records?"},
            {"name": "Model accuracy uplift", "value": uplift, "unit": "%", "display": f"{uplift}% lower error than baseline" if uplift is not None else "—",
             "question": "How much does the trained model outperform the existing baseline?"},
            {"name": "Business value realised", "value": s["realized_impact_eur"], "unit": "€", "display": f"€{s['realized_impact_eur']:,.0f} verified",
             "question": "How much verified cost reduction or service improvement did the AI help achieve?"},
            {"name": "Customer personalisation advantage", "value": personal, "unit": " pts",
             "display": f"{personal:+} WAPE pts vs generic model" if personal is not None else "no consenting data for a generic model",
             "question": "How much better is the customer-specific model than a generic model? (+ = customer model better)"},
            {"name": "Industry learning advantage", "value": industry_adv, "unit": " pts",
             "display": (f"{industry_adv:+} WAPE pts vs customer-only; cold start {models['cold_start_wape']}%" if industry_adv is not None else "needs other consenting customers in this industry"),
             "question": "Does authorised industry data improve predictions, particularly for newly onboarded customers? (+ = industry model better)"},
        ]
        return {
            "as_of": sap.as_of.isoformat(), "tenant": tenant_id, "customer": ctx.customer, "industry": ctx.industry, "industry_label": ctx.industry_label,
            "value_proposition": {
                "title": "Turning real supply-chain experience into competitive intelligence",
                "text": ("Every customer builds its own private intelligence moat from proprietary business data, human expertise and verified "
                         "operational outcomes. With controlled, permission-based industry learning, the platform turns these experiences into "
                         "increasingly effective prediction and optimisation models across verticals."),
                "moat": "The moat is not the SAP data itself: it is the continuously validated ability to turn real business experience into better decisions.",
            },
            "moats": moats, "flywheel": flywheel, "metrics": metrics, "models": models, "consent": consent,
            "industry_customers": [{"tenant": t, "customer": self.registry.labels[t][2], **self.consent(t)} for t in self.registry.files
                                   if self.registry.labels[t][0] == ctx.industry],
            "realised_by_line": realised, "ownership": OWNERSHIP,
            "decisions": decisions, "outcomes": outcomes[:20], "data_moat": learning["data_moat"],
        }
