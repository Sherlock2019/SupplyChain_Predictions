# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/schemas.py
# What this module is: the Pydantic request models of the SCInsight API. FastAPI validates every JSON body
# against one of these classes BEFORE the endpoint runs; a wrong type, a bad code or an unknown field -> HTTP 422.
# This is the first line of defence against malformed or prompt-injected tool arguments coming from an LLM.
# Only comment lines were added (AST-verified by code_explorer/tools/build_registry.py).
# ======================================================================================================

"""Request models. Strict (extra fields forbidden) so malformed or injected tool arguments are rejected with 422."""
from __future__ import annotations

# date / datetime: Pydantic parses "2026-10-27" into a date and ISO timestamps into a datetime.
from datetime import date, datetime
# Literal["a", "b"]: the value must be exactly one of the listed strings.
from typing import Literal

# BaseModel: base class of every model. ConfigDict: model options. Field: per-field constraints (pattern, gt, le, lengths).
# model_validator: a method that checks the whole object after the individual fields were validated.
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Regular expression shared by every SAP-style code (SKU, material, location, supplier, order):
# starts with an uppercase letter or digit, then 1-40 of A-Z, 0-9, "_" or "-". Lowercase, spaces or quotes are rejected.
CODE = r"^[A-Z0-9][A-Z0-9_-]{1,40}$"


# ===== CLASS: Strict =====
# ID: F0177 · pydantic_model · used (framework)
# ORIGINAL FILE: backend/scinsight/schemas.py:12-13
# ROLE: Common base of all request models: forbids unknown fields and trims whitespace around strings.
# FIELDS:
#   model_config -> extra="forbid" (an extra key such as "approve": true -> 422), str_strip_whitespace=True (" WH-B " -> "WH-B").
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# ===== CLASS: ContextRequest =====
# ID: F0178 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:16-17
# ROLE: Body of POST /api/v1/context/validate.
# FIELDS:
#   session_id: str -> 3-128 characters from [A-Za-z0-9_.:-] (Flowise chatId / LangGraph thread id).
# CALLED BY:
#   <- F0118 create_app.validate_context() (references)
#   <- F0118 create_app.validate_context() (validates_input)
# CALLS:
#   (none found)
class ContextRequest(Strict):
    session_id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")


# ===== CLASS: MaterialReadinessRequest =====
# ID: F0179 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:20-34
# ROLE: Body of POST /api/v1/optimizer/material-readiness (factory readiness).
# FIELDS:
#   production_order_id: str | None -> e.g. PRD-1001 (its SKU, quantity and date come from SAP).
#   sku: str | None                  -> finished good, e.g. SER-VITC-30 (when planning without an order).
#   quantity: float | None           -> units to produce; gt=0 (strictly positive), le=10,000,000.
#   need_date: date | None           -> date the materials are needed.
#   plant: str | None                -> producing plant, default FAC-1 in the service.
# CALLED BY:
#   <- F0126 create_app.material_readiness() (references)
#   <- F0126 create_app.material_readiness() (validates_input)
#   <- F0180 MaterialReadinessRequest._one_way() (references)
# CALLS:
#   (none found)
class MaterialReadinessRequest(Strict):
    production_order_id: str | None = Field(default=None, pattern=CODE)
    sku: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)
    need_date: date | None = None
    plant: str | None = Field(default=None, pattern=CODE)

    # ===== FUNCTION: MaterialReadinessRequest._one_way() =====
    # ID: F0180 · method · used (framework)
    # ORIGINAL FILE: backend/scinsight/schemas.py:27-34
    # ROLE: Cross-field rule: EITHER a production order alone, OR sku + quantity + need_date together.
    # INPUTS:
    #   self -> the model after field validation (mode="after").
    # OUTPUT:
    #   MaterialReadinessRequest -> self when valid; raising ValueError makes FastAPI answer 422 with the message.
    # @model_validator(mode="after") runs this method once all fields are parsed.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0179 MaterialReadinessRequest (references)
    @model_validator(mode="after")
    def _one_way(self) -> MaterialReadinessRequest:
        # A production order carries its own SKU, quantity and date from SAP; a caller (or a model) cannot override them.
        # SECURITY: an LLM cannot send "PRD-1001 but quantity 10" to make a shortage disappear.
        if self.production_order_id and (self.sku or self.quantity or self.need_date):
            raise ValueError("give production_order_id alone (its SKU, quantity and date come from SAP), or sku + quantity + need_date")
        # Without an order, all three planning fields are mandatory (no guessing of a quantity or a date).
        if not self.production_order_id and not (self.sku and self.quantity and self.need_date):
            raise ValueError("give production_order_id, or sku + quantity + need_date")
        return self


# ===== CLASS: WarehouseBalancingRequest =====
# ID: F0181 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:37-39
# ROLE: Body of POST /api/v1/optimizer/warehouse-balancing.
# FIELDS:
#   sku: str                      -> required finished good.
#   target_warehouse: str | None  -> receiving warehouse; None = the warehouse with the lowest cover.
# CALLED BY:
#   <- F0127 create_app.warehouse_balancing() (references)
#   <- F0127 create_app.warehouse_balancing() (validates_input)
# CALLS:
#   (none found)
class WarehouseBalancingRequest(Strict):
    sku: str = Field(pattern=CODE)
    target_warehouse: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: ReplenishmentRequest =====
# ID: F0182 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:42-46
# ROLE: Body of POST /api/v1/optimizer/replenishment.
# FIELDS:
#   item_id: str            -> SKU (product) or material code.
#   location: str | None    -> warehouse or factory.
#   quantity: float | None  -> material quantity to buy (required by the service for materials).
#   need_date: date | None  -> need date; default = snapshot date + 14 days.
# CALLED BY:
#   <- F0128 create_app.replenishment() (references)
#   <- F0128 create_app.replenishment() (validates_input)
# CALLS:
#   (none found)
class ReplenishmentRequest(Strict):
    item_id: str = Field(pattern=CODE)
    location: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)
    need_date: date | None = None


# ===== CLASS: DemandForecastRequest =====
# ID: F0183 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:49-52
# ROLE: Body of POST /api/v1/forecast/demand.
# FIELDS:
#   sku, warehouse: str -> required codes.
#   horizon_days: int   -> 1..90 days (ge = greater or equal, le = less or equal), default 14.
# CALLED BY:
#   <- F0129 create_app.forecast_demand() (references)
#   <- F0129 create_app.forecast_demand() (validates_input)
# CALLS:
#   (none found)
class DemandForecastRequest(Strict):
    sku: str = Field(pattern=CODE)
    warehouse: str = Field(pattern=CODE)
    horizon_days: int = Field(default=14, ge=1, le=90)


# ===== CLASS: LeadTimeRequest =====
# ID: F0184 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:55-58
# ROLE: Body of POST /api/v1/forecast/lead-time.
# FIELDS:
#   supplier_id: str          -> required supplier, e.g. SUP-A.
#   material_id: str | None   -> narrows receipts and contract lead time to one material.
#   quantity: float | None    -> needed only to use the promoted ML model.
# CALLED BY:
#   <- F0130 create_app.forecast_lead_time() (references)
#   <- F0130 create_app.forecast_lead_time() (validates_input)
# CALLS:
#   (none found)
class LeadTimeRequest(Strict):
    supplier_id: str = Field(pattern=CODE)
    material_id: str | None = Field(default=None, pattern=CODE)
    quantity: float | None = Field(default=None, gt=0, le=10_000_000)


# ===== CLASS: QualityCheckRequest =====
# ID: F0185 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:61-64
# ROLE: Body of POST /api/v1/quality/check-stock.
# FIELDS:
#   item_id: str           -> SKU or material.
#   location: str | None   -> one site, or all sites when None.
#   horizon_days: int      -> expiry-risk horizon 1..365 days, default 90.
# CALLED BY:
#   <- F0131 create_app.quality_check() (references)
#   <- F0131 create_app.quality_check() (validates_input)
# CALLS:
#   (none found)
class QualityCheckRequest(Strict):
    item_id: str = Field(pattern=CODE)
    location: str | None = Field(default=None, pattern=CODE)
    horizon_days: int = Field(default=90, ge=1, le=365)


# ===== CLASS: RagSearchRequest =====
# ID: F0186 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:67-69
# ROLE: Body of POST /api/v1/rag/search.
# FIELDS:
#   query: str  -> 2..1000 characters.
#   top_k: int  -> 1..10 hits, default 4.
# CALLED BY:
#   <- F0133 create_app.rag_search() (references)
#   <- F0133 create_app.rag_search() (validates_input)
# CALLS:
#   (none found)
class RagSearchRequest(Strict):
    query: str = Field(min_length=2, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)  # None = the active RAG configuration's top_k (4 before tuning)


# ===== CLASS: DecisionCreateRequest =====
# ID: F0187 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:72-76
# ROLE: Body of POST /api/v1/decisions (create a recommendation from a stored calculation).
# FIELDS:
#   calculation_id: str         -> CALC-... returned by a calculation endpoint (the ONLY source of quantities).
#   title: str | None           -> optional title (max 300 chars).
#   idempotency_key: str | None -> repeated calls with the same key return the same recommendation.
#   po_id: str | None           -> SAP purchase order that will later verify the lead-time prediction.
# CALLED BY:
#   <- F0135 create_app.create_decision() (references)
#   <- F0135 create_app.create_decision() (validates_input)
# CALLS:
#   (none found)
class DecisionCreateRequest(Strict):
    calculation_id: str = Field(pattern=r"^CALC-[A-Z0-9-]{4,40}$")
    title: str | None = Field(default=None, max_length=300)
    idempotency_key: str | None = Field(default=None, min_length=4, max_length=120, pattern=r"^[A-Za-z0-9_.:-]+$")
    po_id: str | None = Field(default=None, pattern=CODE)


# ===== CLASS: ReviewRequest =====
# ID: F0188 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:79-82
# ROLE: Body of POST /api/v1/decisions/{rec_id}/review (the human decision).
# FIELDS:
#   decision: Literal -> exactly "approve", "reject", "modify" or "defer".
#   explanation: str  -> mandatory justification, 3..4000 chars (stored in the audit trail).
#   modifications: dict | None -> required by the service when decision == "modify".
# CALLED BY:
#   <- F0138 create_app.review() (references)
#   <- F0138 create_app.review() (validates_input)
# CALLS:
#   (none found)
class ReviewRequest(Strict):
    decision: Literal["approve", "reject", "modify", "defer"]
    explanation: str = Field(min_length=3, max_length=4000)
    modifications: dict | None = None


# ===== CLASS: SapExecutionRequest =====
# ID: F0189 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:85-88
# ROLE: Body of POST /api/v1/decisions/{rec_id}/sap-execution (manual SAP execution record).
# FIELDS:
#   sap_document: str -> SAP document number (CODE pattern, 3..40 chars).
#   doc_type: Literal -> one of the five SAP document kinds.
#   executed_at: datetime -> when the SAP user executed it.
# CALLED BY:
#   <- F0140 create_app.sap_execution() (references)
#   <- F0140 create_app.sap_execution() (validates_input)
# CALLS:
#   (none found)
class SapExecutionRequest(Strict):
    sap_document: str = Field(min_length=3, max_length=40, pattern=CODE)
    doc_type: Literal["purchase_order", "stock_transport_order", "production_order_change", "goods_movement", "purchase_requisition"]
    executed_at: datetime


# ===== CLASS: ReconcileRequest =====
# ID: F0190 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:91-92
# ROLE: Body of POST /api/v1/outcomes/reconcile.
# FIELDS:
#   recommendation_id: str -> REC-...
# CALLED BY:
#   <- F0141 create_app.reconcile() (references)
# CALLS:
#   (none found)
class ReconcileRequest(Strict):
    recommendation_id: str = Field(pattern=r"^REC-[A-Z0-9-]{4,40}$")


# ===== CLASS: RetrainingRequest =====
# ID: F0191 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/schemas.py:95-96
# ROLE: Body of POST /api/v1/learning/retraining-requests.
# FIELDS:
#   reason: str -> 10..1000 characters explaining why retraining is requested.
# CALLED BY:
#   <- F0145 create_app.retraining() (references)
#   <- F0145 create_app.retraining() (validates_input)
# CALLS:
#   (none found)
class RetrainingRequest(Strict):
    reason: str = Field(min_length=10, max_length=1000)
