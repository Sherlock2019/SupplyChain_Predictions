from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CODE = r"^[A-Z0-9][A-Z0-9-]{1,39}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FactoryReadinessRequest(StrictModel):
    plant: str = Field(pattern=CODE)
    material: str = Field(pattern=CODE)
    quantity: float = Field(gt=0, le=10_000_000)
    need_by: date


class StockBalanceRequest(StrictModel):
    material: str = Field(pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=120)
    service_level: float = Field(default=0.95, ge=0.5, le=0.999)


class ForecastRequest(StrictModel):
    material: str = Field(pattern=CODE)
    warehouse: str | None = Field(default=None, pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=90)


class WhatIfRequest(StrictModel):
    material: str = Field(pattern=CODE)
    demand_change_pct: float = Field(ge=-100, le=500)
    supplier_delay_days: int = Field(default=0, ge=0, le=180)
    horizon_days: int = Field(default=28, ge=1, le=120)


class SupplierRiskRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160)


class QualityRequest(StrictModel):
    plant: str | None = Field(default=None, pattern=CODE)
    material: str | None = Field(default=None, pattern=CODE)


class LogisticsRequest(StrictModel):
    warehouse: str | None = Field(default=None, pattern=CODE)
    material: str | None = Field(default=None, pattern=CODE)


class SalesOrderRequest(StrictModel):
    warehouse: str | None = Field(default=None, pattern=CODE)


class StocktakeRequest(StrictModel):
    tolerance_pct: float = Field(default=1.0, ge=0, le=20)


class WatchRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["days_of_cover", "supplier_risk", "sales_orders_at_risk", "stocktake_unexplained", "shipment_delay", "question"]
    params: dict[str, str] = Field(default_factory=dict)
    threshold: float = 0


class RagQuery(StrictModel):
    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=12)
    category: str | None = Field(default=None, max_length=60)


class RagDocument(StrictModel):
    title: str = Field(min_length=1, max_length=240)
    category: Literal["contract", "sop", "quality", "product_spec", "logistics", "other"] = "other"
    source: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=10, max_length=100_000)


class RecommendationRequest(StrictModel):
    analysis_id: str = Field(pattern=r"^AN-[0-9a-f]{12}$")
    explanation: str = Field(min_length=1, max_length=12_000)
    source: Literal["api", "dashboard", "flowise", "langgraph", "mcp"] = "api"


class RecommendationFromTextRequest(StrictModel):
    """Agent hand-off (Flowise HumanInput 'proceed'): the gateway, not the LLM, picks the analysis to submit."""

    text: str = Field(min_length=1, max_length=40_000)
    expected_kind: Literal["factory_readiness", "stock_balance", "supplier_risk", "quality_status", "logistics_status",
                           "sales_order_fulfilment", "stocktake_reconciliation"]
    source: Literal["flowise", "langgraph", "mcp", "api"] = "flowise"
    comment: str = Field(default="", max_length=2000)


REASON_CODES = ("supplier_risk", "capacity", "cost", "timing", "customer_priority", "data_quality", "quality", "other")


class DecisionRequest(StrictModel):
    decision: Literal["accepted", "rejected"]
    comment: str = Field(default="", max_length=4000)
    # Human expertise capture: "modified" = accepted with changes; reason_code explains why the expert deviated.
    modified: bool = False
    reason_code: Literal["supplier_risk", "capacity", "cost", "timing", "customer_priority", "data_quality", "quality", "other"] | None = None


class ConsentRequest(StrictModel):
    industry_learning: bool


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)
    role: Literal["director", "demand", "production", "procurement", "warehouse", "logistics", "quality", "finance", "mlops"] | None = None


class OutcomeRequest(StrictModel):
    """The real result of an executed recommendation, observed in SAP (approval alone is never proof)."""
    achieved: bool
    observed: dict = Field(default_factory=dict)
    realized_impact_eur: float | None = Field(default=None, ge=-10_000_000, le=10_000_000)
    source_document: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9\-_/.]+$")
    note: str = Field(default="", max_length=2000)


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


class ResumeRequest(StrictModel):
    decision: Literal["submit", "discard"]
    comment: str = Field(default="", max_length=2000)


class SupplierLeadTimeRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160, description="supplier name or vendor code")
    material: str | None = Field(default=None, pattern=CODE)


class ReconcileRequest(StrictModel):
    """What SAP shows actually happened after an executed decision (goods receipt, delivery or posting)."""
    decision_id: int = Field(ge=1)
    sap_document: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9\-_/.]+$")
    actual_quantity: float | None = Field(default=None, ge=0)
    actual_date: date | None = None
    realized_impact_eur: float | None = Field(default=None, ge=-10_000_000, le=10_000_000)
    note: str = Field(default="", max_length=2000)


DEEP_SUBAGENTS = ("contract-analyst", "quality-analyst", "logistics-analyst")
DEEP_TOOLS = ("supplier_risk", "sap_snapshot", "search_governed_knowledge", "quality_status", "logistics_status", "factory_material_readiness")


class DeepAgentHarness(StrictModel):
    """Harness settings of the Deep Agents supplier-research agent (model, step budget, subagents, tools, output rules)."""
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1500, ge=256, le=4000)
    max_steps: int = Field(default=60, ge=20, le=200, description="LangGraph recursion limit: total model + tool steps per run")
    subagents: list[Literal["contract-analyst", "quality-analyst", "logistics-analyst"]] = Field(default_factory=lambda: list(DEEP_SUBAGENTS))
    tools: list[Literal["supplier_risk", "sap_snapshot", "search_governed_knowledge", "quality_status", "logistics_status", "factory_material_readiness"]] = Field(
        default_factory=lambda: list(DEEP_TOOLS), min_length=1)
    require_plan: bool = True
    require_citations: bool = True
    report_style: Literal["full", "executive"] = "full"

    @model_validator(mode="after")
    def _unique(self) -> DeepAgentHarness:
        self.subagents = list(dict.fromkeys(self.subagents))
        self.tools = list(dict.fromkeys(self.tools))
        return self


class SupplierResearchRequest(StrictModel):
    supplier: str = Field(min_length=2, max_length=160)
    material: str | None = Field(default=None, pattern=CODE)
    question: str = Field(default="Assess supply continuity, quality, and contract risk.", max_length=2000)
    thread_id: str | None = Field(default=None, max_length=128)


class FlowisePredictRequest(StrictModel):
    question: str = Field(default="", max_length=8000)
    session_id: str | None = Field(default=None, max_length=128)
    form: dict[str, Any] | None = None
    human_input: dict[str, Any] | None = None

    @model_validator(mode="after")
    def question_or_resume(self) -> "FlowisePredictRequest":
        # A Human Input resume carries no new question; every other call must ask something.
        if not self.question and not self.human_input:
            raise ValueError("question is required unless resuming a human input")
        return self
