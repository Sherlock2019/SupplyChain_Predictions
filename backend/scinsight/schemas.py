"""Request models. Strict (extra fields forbidden) so malformed or injected tool arguments are rejected with 422."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CODE = r"^[A-Z0-9][A-Z0-9_-]{1,40}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContextRequest(Strict):
    session_id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")


class MaterialReadinessRequest(Strict):
    production_order_id: str | None = Field(default=None, pattern=CODE)
    sku: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)
    need_date: date | None = None
    plant: str | None = Field(default=None, pattern=CODE)

    @model_validator(mode="after")
    def _one_way(self) -> MaterialReadinessRequest:
        # A production order carries its own SKU, quantity and date from SAP; a caller (or a model) cannot override them.
        if self.production_order_id and (self.sku or self.quantity or self.need_date):
            raise ValueError("give production_order_id alone (its SKU, quantity and date come from SAP), or sku + quantity + need_date")
        if not self.production_order_id and not (self.sku and self.quantity and self.need_date):
            raise ValueError("give production_order_id, or sku + quantity + need_date")
        return self


class WarehouseBalancingRequest(Strict):
    sku: str = Field(pattern=CODE)
    target_warehouse: str | None = Field(default=None, pattern=CODE)


class ReplenishmentRequest(Strict):
    item_id: str = Field(pattern=CODE)
    location: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)
    need_date: date | None = None


class DemandForecastRequest(Strict):
    sku: str = Field(pattern=CODE)
    warehouse: str = Field(pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=90)


class LeadTimeRequest(Strict):
    supplier_id: str = Field(pattern=CODE)
    material_id: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)


class QualityCheckRequest(Strict):
    item_id: str = Field(pattern=CODE)
    location: str | None = Field(default=None, pattern=CODE)
    horizon_days: int = Field(default=90, ge=1, le=365)


class RagSearchRequest(Strict):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)


class DecisionCreateRequest(Strict):
    calculation_id: str = Field(pattern=r"^CALC-[A-Z0-9-]{4,40}$")
    title: str | None = Field(default=None, max_length=300)
    idempotency_key: str | None = Field(default=None, min_length=4, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    po_id: str | None = Field(default=None, pattern=CODE)


class ReviewRequest(Strict):
    decision: Literal["approve", "reject", "modify", "defer"]
    explanation: str = Field(min_length=3, max_length=4000)
    modifications: dict | None = None


class SapExecutionRequest(Strict):
    sap_document: str = Field(min_length=3, max_length=40, pattern=CODE)
    doc_type: Literal["purchase_order", "stock_transport_order", "production_order_change", "goods_movement", "purchase_requisition"]
    executed_at: datetime


class ReconcileRequest(Strict):
    recommendation_id: str = Field(pattern=r"^REC-[A-Z0-9-]{4,40}$")


class RetrainingRequest(Strict):
    reason: str = Field(min_length=10, max_length=1000)
