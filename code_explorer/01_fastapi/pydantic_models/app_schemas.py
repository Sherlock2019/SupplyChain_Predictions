# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/schemas.py
# What this module is: the Pydantic request models of the SPARC / Aurelia gateway (backend/app/main.py). Every JSON body is
# validated here before any engine, store or agent code runs; extra fields are forbidden (422) except for the OpenAI-compatible
# embeddings request.
# Only comment lines were added (AST-verified).
# ======================================================================================================
from __future__ import annotations

from datetime import date
# Any: free-form values (Flowise form / human input). Literal: closed list of allowed strings.
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# SAP-style code for this gateway: uppercase letters/digits and "-", 2-40 characters (no "_" here, unlike SCInsight).
CODE = r"^[A-Z0-9][A-Z0-9-]{1,39}$"


# ===== CLASS: StrictModel =====
# ID: F0147 · pydantic_model · used (framework)
# ORIGINAL FILE: backend/app/schemas.py:11-12
# ROLE: Base model: unknown fields -> 422, strings stripped.
# FIELDS:
#   model_config.
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ===== CLASS: FactoryReadinessRequest =====
# ID: F0148 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:15-19
# ROLE: Body of POST /api/v1/analysis/factory-readiness and /optimizer/material-readiness.
# FIELDS:
#   plant, material: codes; quantity: 0 < q <= 10,000,000; need_by: date.
# CALLED BY:
#   <- F0040 create_app.factory_readiness() (references)
#   <- F0040 create_app.factory_readiness() (validates_input)
#   <- F0106 create_app.poc_material_readiness() (references)
#   <- F0106 create_app.poc_material_readiness() (validates_input)
# CALLS:
#   (none found)
class FactoryReadinessRequest(StrictModel):
    plant: str = Field(pattern=CODE)
    material: str = Field(pattern=CODE)
    quantity: float = Field(gt=0, le=10_000_000)
    need_by: date


# ===== CLASS: StockBalanceRequest =====
# ID: F0149 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:22-25
# ROLE: Body of POST /api/v1/analysis/stock-balance and /optimizer/warehouse-transfer.
# FIELDS:
#   material; horizon_days 1..120 (14); service_level 0.5..0.999 (0.95).
# CALLED BY:
#   <- F0041 create_app.stock_balance() (references)
#   <- F0041 create_app.stock_balance() (validates_input)
#   <- F0107 create_app.poc_warehouse_transfer() (references)
#   <- F0107 create_app.poc_warehouse_transfer() (validates_input)
# CALLS:
#   (none found)
class StockBalanceRequest(StrictModel):
    material: str = Field(pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=120)
    service_level: float = Field(default=0.95, ge=0.5, le=0.999)


# ===== CLASS: ForecastRequest =====
# ID: F0150 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:28-31
# ROLE: Body of POST /api/v1/analysis/forecast and /forecast/demand.
# FIELDS:
#   material; warehouse (optional); horizon_days 1..90 (14).
# CALLED BY:
#   <- F0042 create_app.demand_forecast() (references)
#   <- F0042 create_app.demand_forecast() (validates_input)
#   <- F0104 create_app.poc_forecast_demand() (references)
#   <- F0104 create_app.poc_forecast_demand() (validates_input)
# CALLS:
#   (none found)
class ForecastRequest(StrictModel):
    material: str = Field(pattern=CODE)
    warehouse: str | None = Field(default=None, pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=90)


# ===== CLASS: WhatIfRequest =====
# ID: F0151 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:34-38
# ROLE: Body of POST /api/v1/analysis/what-if (demand change and supplier delay scenario).
# FIELDS:
#   material; demand_change_pct -100..500; supplier_delay_days 0..180; horizon_days 1..120 (28).
# CALLED BY:
#   <- F0043 create_app.what_if() (references)
#   <- F0043 create_app.what_if() (validates_input)
# CALLS:
#   (none found)
class WhatIfRequest(StrictModel):
    material: str = Field(pattern=CODE)
    demand_change_pct: float = Field(ge=-100, le=500)
    supplier_delay_days: int = Field(default=0, ge=0, le=180)
    horizon_days: int = Field(default=28, ge=1, le=120)


# ===== CLASS: SupplierRiskRequest =====
# ID: F0152 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:41-42
# ROLE: Body of POST /api/v1/analysis/supplier-risk.
# FIELDS:
#   supplier: name or code, 2..160 chars.
# CALLED BY:
#   <- F0044 create_app.supplier_risk() (references)
#   <- F0044 create_app.supplier_risk() (validates_input)
# CALLS:
#   (none found)
class SupplierRiskRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160)


# ===== CLASS: QualityRequest =====
# ID: F0153 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:45-47
# ROLE: Body of POST /api/v1/analysis/quality.
# FIELDS:
#   plant, material: optional codes.
# CALLED BY:
#   <- F0045 create_app.quality() (references)
#   <- F0045 create_app.quality() (validates_input)
# CALLS:
#   (none found)
class QualityRequest(StrictModel):
    plant: str | None = Field(default=None, pattern=CODE)
    material: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: LogisticsRequest =====
# ID: F0154 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:50-52
# ROLE: Body of POST /api/v1/analysis/logistics.
# FIELDS:
#   warehouse, material: optional codes.
# CALLED BY:
#   <- F0046 create_app.logistics() (references)
#   <- F0046 create_app.logistics() (validates_input)
# CALLS:
#   (none found)
class LogisticsRequest(StrictModel):
    warehouse: str | None = Field(default=None, pattern=CODE)
    material: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: SalesOrderRequest =====
# ID: F0155 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:55-56
# ROLE: Body of POST /api/v1/analysis/sales-orders.
# FIELDS:
#   warehouse: optional code.
# CALLED BY:
#   <- F0047 create_app.sales_orders() (references)
#   <- F0047 create_app.sales_orders() (validates_input)
# CALLS:
#   (none found)
class SalesOrderRequest(StrictModel):
    warehouse: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: StocktakeRequest =====
# ID: F0156 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:59-60
# ROLE: Body of POST /api/v1/analysis/stocktake.
# FIELDS:
#   tolerance_pct 0..20 (1.0) -> count differences below this % are tolerated.
# CALLED BY:
#   <- F0048 create_app.stocktake() (references)
#   <- F0048 create_app.stocktake() (validates_input)
# CALLS:
#   (none found)
class StocktakeRequest(StrictModel):
    tolerance_pct: float = Field(default=1.0, ge=0, le=20)


# ===== CLASS: WatchRequest =====
# ID: F0157 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:63-67
# ROLE: Body of POST /api/v1/watches (a saved alert).
# FIELDS:
#   name; kind (one of six watch kinds); params: dict[str, str]; threshold: float.
# CALLED BY:
#   <- F0069 create_app.create_watch() (references)
#   <- F0069 create_app.create_watch() (validates_input)
# CALLS:
#   (none found)
class WatchRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["days_of_cover", "supplier_risk", "sales_orders_at_risk", "stocktake_unexplained", "shipment_delay", "question"]
    # default_factory=dict: each instance gets its own new empty dict.
    params: dict[str, str] = Field(default_factory=dict)
    threshold: float = 0


# ===== CLASS: RagQuery =====
# ID: F0158 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:70-73
# ROLE: Body of POST /api/v1/rag/search.
# FIELDS:
#   query 2..2000 chars; top_k 1..12 (4); category optional.
# CALLED BY:
#   <- F0076 create_app.rag_search() (references)
#   <- F0076 create_app.rag_search() (validates_input)
# CALLS:
#   (none found)
class RagQuery(StrictModel):
    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=12)
    category: str | None = Field(default=None, max_length=60)


# ===== CLASS: RagDocument =====
# ID: F0159 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:76-80
# ROLE: Body of POST /api/v1/rag/documents (manager adds a governed document).
# FIELDS:
#   title, category (closed list), source, text (10..100,000 chars).
# CALLED BY:
#   <- F0081 create_app.rag_add() (references)
#   <- F0081 create_app.rag_add() (validates_input)
# CALLS:
#   (none found)
class RagDocument(StrictModel):
    title: str = Field(min_length=1, max_length=240)
    category: Literal["contract", "sop", "quality", "product_spec", "logistics", "other"] = "other"
    source: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=10, max_length=100_000)


# ===== CLASS: RecommendationRequest =====
# ID: F0160 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:83-86
# ROLE: Body of POST /api/v1/recommendations and /decisions: submit a stored analysis for human review.
# FIELDS:
#   analysis_id: "AN-" + 12 hex chars; explanation; source (where the submission came from).
# CALLED BY:
#   <- F0095 create_app.submit_recommendation() (references)
#   <- F0095 create_app.submit_recommendation() (validates_input)
#   <- F0108 create_app.poc_decisions() (references)
#   <- F0108 create_app.poc_decisions() (validates_input)
# CALLS:
#   (none found)
class RecommendationRequest(StrictModel):
    analysis_id: str = Field(pattern=r"^AN-[0-9a-f]{12}$")
    explanation: str = Field(min_length=1, max_length=12_000)
    source: Literal["api", "dashboard", "flowise", "langgraph", "mcp"] = "api"


# ===== CLASS: RecommendationFromTextRequest =====
# ID: F0161 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:89-96
# ROLE: Body of POST /api/v1/recommendations/from-agent: the agent's text; the GATEWAY picks the referenced analysis.
# FIELDS:
#   text; expected_kind (analysis kind to look for); source; comment.
# CALLED BY:
#   <- F0096 create_app.submit_from_agent() (references)
#   <- F0096 create_app.submit_from_agent() (validates_input)
# CALLS:
#   (none found)
class RecommendationFromTextRequest(StrictModel):
    """Agent hand-off (Flowise HumanInput 'proceed'): the gateway, not the LLM, picks the analysis to submit."""

    text: str = Field(min_length=1, max_length=40_000)
    expected_kind: Literal["factory_readiness", "stock_balance", "supplier_risk", "quality_status", "logistics_status",
                           "sales_order_fulfilment", "stocktake_reconciliation"]
    source: Literal["flowise", "langgraph", "mcp", "api"] = "flowise"
    comment: str = Field(default="", max_length=2000)


# Allowed reason codes when a manager deviates from a recommendation (human expertise capture).
REASON_CODES = ("supplier_risk", "capacity", "cost", "timing", "customer_priority", "data_quality", "quality", "other")


# ===== CLASS: DecisionRequest =====
# ID: F0162 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:102-107
# ROLE: Body of POST /api/v1/recommendations/{id}/decision and /decisions/{id}/human-review (manager decision).
# FIELDS:
#   decision "accepted" | "rejected"; comment; modified (accepted with changes); reason_code.
# CALLED BY:
#   <- F0098 create_app.decide() (references)
#   <- F0098 create_app.decide() (validates_input)
#   <- F0109 create_app.poc_human_review() (references)
#   <- F0109 create_app.poc_human_review() (validates_input)
# CALLS:
#   (none found)
class DecisionRequest(StrictModel):
    decision: Literal["accepted", "rejected"]
    comment: str = Field(default="", max_length=4000)
    # Human expertise capture: "modified" = accepted with changes; reason_code explains why the expert deviated.
    modified: bool = False
    reason_code: Literal["supplier_risk", "capacity", "cost", "timing", "customer_priority", "data_quality", "quality", "other"] | None = None


# ===== CLASS: ConsentRequest =====
# ID: F0163 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:110-111
# ROLE: Body of POST /api/v1/moat/consent.
# FIELDS:
#   industry_learning: bool -> may this customer's data contribute to industry learning?
# CALLED BY:
#   <- F0058 create_app.moat_consent() (references)
#   <- F0058 create_app.moat_consent() (validates_input)
# CALLS:
#   (none found)
class ConsentRequest(StrictModel):
    industry_learning: bool


# ===== CLASS: ChatRequest =====
# ID: F0164 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:114-117
# ROLE: Body of POST /api/v1/chat and /api/v1/langgraph/agentflow.
# FIELDS:
#   message 1..8000 chars; thread_id (conversation); role (specialised role agent).
# CALLED BY:
#   <- F0083 create_app.chat() (references)
#   <- F0083 create_app.chat() (validates_input)
#   <- F0085 create_app.langgraph_agentflow() (references)
#   <- F0085 create_app.langgraph_agentflow() (validates_input)
# CALLS:
#   (none found)
class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)
    role: Literal["director", "demand", "production", "procurement", "warehouse", "logistics", "quality", "finance", "mlops"] | None = None


# ===== CLASS: OutcomeRequest =====
# ID: F0165 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:120-126
# ROLE: Body of POST /api/v1/recommendations/{id}/outcome: the observed result of an executed recommendation.
# FIELDS:
#   achieved; observed (free dict); realized_impact_eur; source_document (SAP document, restricted characters); note.
# CALLED BY:
#   <- F0059 create_app.record_outcome() (references)
#   <- F0059 create_app.record_outcome() (validates_input)
# CALLS:
#   (none found)
class OutcomeRequest(StrictModel):
    """The real result of an executed recommendation, observed in SAP (approval alone is never proof)."""
    achieved: bool
    observed: dict = Field(default_factory=dict)
    realized_impact_eur: float | None = Field(default=None, ge=-10_000_000, le=10_000_000)
    source_document: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9\-_/.]+$")
    note: str = Field(default="", max_length=2000)


# ===== CLASS: BusinessWorkflowRequest =====
# ID: F0166 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:129-140
# ROLE: Body of POST /api/v1/workflows/business (LangGraph business workflow): free text or structured fields.
# FIELDS:
#   request_text, request_type, plant, material, quantity, need_by, horizon_days, service_level, supplier, warehouse, thread_id.
# CALLED BY:
#   <- F0087 create_app.business_start() (references)
#   <- F0087 create_app.business_start() (validates_input)
# CALLS:
#   (none found)
class BusinessWorkflowRequest(StrictModel):
    request_text: str | None = Field(default=None, max_length=4000)
    request_type: Literal["factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "inventory"] | None = None
    plant: str | None = Field(default=None, pattern=CODE)
    material: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)
    need_by: date | None = None
    horizon_days: int | None = Field(default=None, ge=1, le=120)
    service_level: float | None = Field(default=None, ge=0.5, le=0.999)
    supplier: str | None = Field(default=None, max_length=160)
    warehouse: str | None = Field(default=None, pattern=CODE)
    thread_id: str | None = Field(default=None, max_length=128)


# ===== CLASS: ResumeRequest =====
# ID: F0167 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:143-145
# ROLE: Body of the LangGraph resume endpoints (planner decision at the interrupt).
# FIELDS:
#   decision "submit" | "discard"; comment.
# CALLED BY:
#   <- F0086 create_app.langgraph_agentflow_resume() (references)
#   <- F0086 create_app.langgraph_agentflow_resume() (validates_input)
#   <- F0088 create_app.business_resume() (references)
#   <- F0088 create_app.business_resume() (validates_input)
# CALLS:
#   (none found)
class ResumeRequest(StrictModel):
    decision: Literal["submit", "discard"]
    comment: str = Field(default="", max_length=2000)


# ===== CLASS: EmbeddingsRequest =====
# ID: F0168 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:148-160
# ROLE: Body of POST /v1/embeddings (OpenAI-compatible): extra fields are IGNORED because OpenAI clients send e.g. "user".
# FIELDS:
#   input: str | list[str]; model; encoding_format "float" | "base64".
# CALLED BY:
#   <- F0078 create_app.embeddings() (references)
#   <- F0078 create_app.embeddings() (validates_input)
#   <- F0169 EmbeddingsRequest._limits() (references)
# CALLS:
#   (none found)
class EmbeddingsRequest(BaseModel):
    """OpenAI-compatible embeddings request (extra fields such as `user` are ignored, as OpenAI clients send them)."""
    model_config = ConfigDict(extra="ignore")
    input: str | list[str] = Field(description="text or list of texts (max 256 items, 8000 characters each)")
    model: str | None = None
    encoding_format: Literal["float", "base64"] | None = None

    # ===== FUNCTION: EmbeddingsRequest._limits() =====
    # ID: F0169 · method · used (framework)
    # ORIGINAL FILE: backend/app/schemas.py:155-160
    # ROLE: Size limits: 1..256 texts of at most 8000 characters.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   EmbeddingsRequest (ValueError -> 422).
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0168 EmbeddingsRequest (references)
    @model_validator(mode="after")
    def _limits(self) -> EmbeddingsRequest:
        items = [self.input] if isinstance(self.input, str) else self.input
        if not items or len(items) > 256 or any(len(t) > 8000 for t in items):
            raise ValueError("input must be 1-256 texts of at most 8000 characters")
        return self


# ===== CLASS: SupplierLeadTimeRequest =====
# ID: F0170 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:163-165
# ROLE: Body of POST /forecast/supplier-lead-time (POC contract).
# FIELDS:
#   supplier (name or vendor code); material (optional code).
# CALLED BY:
#   <- F0105 create_app.poc_forecast_lead_time() (references)
#   <- F0105 create_app.poc_forecast_lead_time() (validates_input)
# CALLS:
#   (none found)
class SupplierLeadTimeRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160, description="supplier name or vendor code")
    material: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: ReconcileRequest =====
# ID: F0171 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:168-175
# ROLE: Body of POST /outcomes/reconcile (POC contract): what SAP shows happened after an executed decision.
# FIELDS:
#   decision_id >= 1; sap_document; actual_quantity; actual_date; realized_impact_eur; note.
# CALLED BY:
#   <- F0110 create_app.poc_reconcile() (references)
#   <- F0110 create_app.poc_reconcile() (validates_input)
#   <- F0141 create_app.reconcile() (validates_input)
# CALLS:
#   (none found)
class ReconcileRequest(StrictModel):
    """What SAP shows actually happened after an executed decision (goods receipt, delivery or posting)."""
    decision_id: int = Field(ge=1)
    sap_document: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9\-_/.]+$")
    actual_quantity: float | None = Field(default=None, ge=0)
    actual_date: date | None = None
    realized_impact_eur: float | None = Field(default=None, ge=-10_000_000, le=10_000_000)
    note: str = Field(default="", max_length=2000)


# Options of the Deep Agent harness (subagents and data tools it may use).
DEEP_SUBAGENTS = ("contract-analyst", "quality-analyst", "logistics-analyst")
DEEP_TOOLS = ("supplier_risk", "sap_snapshot", "search_governed_knowledge", "quality_status", "logistics_status", "factory_material_readiness")


# ===== CLASS: DeepAgentHarness =====
# ID: F0172 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:182-208
# ROLE: Harness settings of the Deep Agents supplier-research agent (body of PUT /api/v1/deep-agents/harness): model,
#       step budget, loop controls, reliability, allowed subagents and tools, output rules.
# FIELDS:
#   temperature, max_tokens, max_steps, max_model_calls, max_tool_calls, max_calls_per_tool, max_subagent_calls,
#   model_timeout_seconds, model_retries, tool_retries, subagents, tools, require_plan, require_citations, report_style.
# CALLED BY:
#   <- F0554 harness_of() (calls)
#   <- F0017 create_app() (references)
#   <- F0089 create_app.current_harness() (calls)
#   <- F0090 create_app.deep_harness() (calls)
#   <- F0091 create_app.set_deep_harness() (references)
#   <- F0091 create_app.set_deep_harness() (validates_input)
#   <- F0173 DeepAgentHarness._unique() (references)
# CALLS:
#   (none found)
class DeepAgentHarness(StrictModel):
    """Harness settings of the Deep Agents supplier-research agent (model, step budget, subagents, tools, output rules)."""
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="Randomness of the model: 0 = same answer every time")
    max_tokens: int = Field(default=1500, ge=256, le=4000, description="Longest answer of one model call")
    max_steps: int = Field(default=60, ge=20, le=200, description="LangGraph recursion limit: total model + tool steps per run")
    # loop controls (enforced by HarnessGuard in deep_agent.py; reaching one ends the run gracefully, with the work done so far)
    max_model_calls: int = Field(default=15, ge=3, le=50, description="Thinking turns: model calls of the main agent per run")
    max_tool_calls: int = Field(default=20, ge=1, le=60, description="Data-tool and subagent calls per run, all together")
    max_calls_per_tool: int = Field(default=6, ge=1, le=20, description="Repeat guard: calls of any single data tool per run")
    max_subagent_calls: int = Field(default=4, ge=0, le=10, description="Delegations to subagents per run; 0 = no delegation at all")
    # reliability
    model_timeout_seconds: int = Field(default=120, ge=15, le=600, description="Give up on one model call after this long")
    model_retries: int = Field(default=1, ge=0, le=5, description="Retries of a failed model call")
    tool_retries: int = Field(default=1, ge=0, le=3, description="Retries of a failed tool call")
    subagents: list[Literal["contract-analyst", "quality-analyst", "logistics-analyst"]] = Field(
        default_factory=lambda: list(DEEP_SUBAGENTS), description="Specialist subagents the agent may delegate to")
    tools: list[Literal["supplier_risk", "sap_snapshot", "search_governed_knowledge", "quality_status", "logistics_status", "factory_material_readiness"]] = Field(
        default_factory=lambda: list(DEEP_TOOLS), min_length=1, description="Read-only data tools the agent may call")
    require_plan: bool = Field(default=True, description="Write a to-do plan before researching")
    require_citations: bool = Field(default=True, description="Cite the evidence id for every claim")
    report_style: Literal["full", "executive"] = Field(default="full", description="full report, or executive summary of at most 8 bullets")

    # ===== FUNCTION: DeepAgentHarness._unique() =====
    # ID: F0173 · method · used (framework)
    # ORIGINAL FILE: backend/app/schemas.py:204-208
    # ROLE: Remove duplicate subagents / tools while keeping order.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   DeepAgentHarness.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0172 DeepAgentHarness (references)
    @model_validator(mode="after")
    def _unique(self) -> DeepAgentHarness:
        self.subagents = list(dict.fromkeys(self.subagents))
        self.tools = list(dict.fromkeys(self.tools))
        return self


# ===== CLASS: SupplierResearchRequest =====
# ID: F0174 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:211-215
# ROLE: Body of POST /api/v1/deep-agents/supplier-research.
# FIELDS:
#   supplier; material (optional); question (default task); thread_id.
# CALLED BY:
#   <- F0092 create_app.supplier_research() (references)
#   <- F0092 create_app.supplier_research() (validates_input)
# CALLS:
#   (none found)
class SupplierResearchRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160)
    material: str | None = Field(default=None, pattern=CODE)
    question: str = Field(default="Assess supply continuity, quality, and contract risk.", max_length=2000)
    thread_id: str | None = Field(default=None, max_length=128)


# ===== CLASS: FlowisePredictRequest =====
# ID: F0175 · pydantic_model · used
# ORIGINAL FILE: backend/app/schemas.py:218-229
# ROLE: Body of POST /api/v1/flowise/{flow}/predict (gateway proxy to a Flowise flow).
# FIELDS:
#   question; session_id; form (Flowise form input); human_input (resume of a Human Input node).
# CALLED BY:
#   <- F0094 create_app.flowise_predict() (references)
#   <- F0094 create_app.flowise_predict() (validates_input)
# CALLS:
#   (none found)
class FlowisePredictRequest(StrictModel):
    question: str = Field(default="", max_length=8000)
    session_id: str | None = Field(default=None, max_length=128)
    form: dict[str, Any] | None = None
    human_input: dict[str, Any] | None = None

    # ===== FUNCTION: FlowisePredictRequest.question_or_resume() =====
    # ID: F0176 · method · used (framework)
    # ORIGINAL FILE: backend/app/schemas.py:224-229
    # ROLE: A question is required unless the call resumes a paused Human Input.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   FlowisePredictRequest (ValueError -> 422).
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @model_validator(mode="after")
    def question_or_resume(self) -> "FlowisePredictRequest":
        # A Human Input resume carries no new question; every other call must ask something.
        if not self.question and not self.human_input:
            raise ValueError("question is required unless resuming a human input")
        return self
