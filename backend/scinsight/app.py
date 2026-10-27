"""SupplyChain Insight AI — business-tool service (FastAPI, Swagger at /docs).

    uvicorn backend.scinsight.app:app --port 8100

Every route authenticates the caller from its API key (X-API-Key or Authorization: Bearer). The tenant and roles come from
the key; SAP is read-only (writes -> 405); recommendations need an authorised human review; nothing posts to SAP.
"""
from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request

from backend.scinsight import fixtures, learning
from backend.scinsight import schemas as s
from backend.scinsight.db import Database, ensure_postgres_database
from backend.scinsight.rag import KnowledgeBase, make_embedder
from backend.scinsight.rag_tuning import api as rag_tuning_api
from backend.scinsight.security import READ_ROLES, Principal, Security
from backend.scinsight.service import Service
from backend.scinsight.settings import SciSettings

TAGS = [
    {"name": "context", "description": "Who is calling: user, tenant and roles come from the API key, never from the request body or an LLM."},
    {"name": "sap", "description": "Read-only SAP data (synthetic snapshot in the POC). Any write verb returns 405."},
    {"name": "optimizer", "description": "Deterministic calculations: BOM readiness, warehouse balancing, replenishment options."},
    {"name": "forecast", "description": "Baseline demand forecast with back-test; empirical (or promoted-model) supplier lead time."},
    {"name": "quality", "description": "Batch status, expiry and FEFO validation."},
    {"name": "rag", "description": "Private, tenant-scoped knowledge retrieval with citations."},
    {"name": "decisions", "description": "Recommendations from stored calculations, authorised human review, SAP execution records."},
    {"name": "learning", "description": "Outcome reconciliation, learning records, metrics, governed model training and promotion."},
    {"name": "rag-tuning", "description": "RAG Tuning Console (administrators): chunking, embeddings, retrieval, benchmark, publish and rollback of the Company RAG Search."},
]


def create_app(settings: SciSettings | None = None, db: Database | None = None) -> FastAPI:
    settings = settings or SciSettings()
    if settings.sap_write_enabled:
        raise RuntimeError("SAP_WRITE_ENABLED=true is not allowed in Phase 1: SupplyChain Insight AI is read-only towards SAP")
    if settings.sci_database_url.startswith(("postgresql://", "postgres://")):
        # Deployments never fall back to the public sci-dev-* keys (those exist only for hermetic SQLite tests).
        if settings.sci_load_fixtures and settings.missing_keys():
            raise RuntimeError("missing user keys (run scripts/gen-env.py --add-missing): " + ", ".join(settings.missing_keys()))
        if db is None:
            ensure_postgres_database(settings.sci_database_url)
    db = db or Database(settings.sci_database_url)
    db.migrate()
    if settings.sci_load_fixtures:
        fixtures.load(db, settings.user_keys())
    security = Security(db)
    service = Service(db, settings, security)
    kb = KnowledgeBase(db, make_embedder(settings.sci_embedding_backend), settings.sci_embedding_backend)
    ingest_report = kb.ingest_dir(settings.sci_knowledge_dir) if settings.rag_enabled else {}

    app = FastAPI(title="SupplyChain Insight AI — business tools", version="1.0.0", openapi_tags=TAGS,
                  description="Cosmetics supply-chain POC: synthetic SAP data, deterministic calculations, human-approved decisions, verified-outcome learning.")
    app.state.db, app.state.service, app.state.security, app.state.kb, app.state.ingest_report = db, service, security, kb, ingest_report

    def principal(request: Request, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None),
                  x_tenant: str | None = Header(default=None)) -> Principal:
        bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
        return security.authenticate(x_api_key or bearer, x_tenant)

    def reader(p: Principal = Depends(principal)) -> Principal:
        security.require(p, READ_ROLES, "This endpoint")
        return p

    def biz_date(p: Principal) -> date:
        return service.snapshot(p.tenant_id)["as_of"]

    @app.get("/health", tags=["context"])
    def health() -> dict:
        return {"status": "ok", "sap_mode": settings.sap_mode, "sap_write_enabled": False, "human_approval_required": settings.human_approval_required,
                "industry_sharing_enabled": settings.industry_sharing_enabled, "database": db.dialect}

    # ------------------------------------------------------------------ context
    @app.get("/api/v1/context", tags=["context"])
    def context(p: Principal = Depends(reader)) -> dict:
        snap = service.snapshot(p.tenant_id)
        return {"user_id": p.user_id, "name": p.name, "tenant_id": p.tenant_id, "roles": sorted(p.roles), "is_human": p.is_human,
                "snapshot": {"id": snap["id"], "as_of": snap["as_of_date"], "age_days": snap["age_days"], "synthetic": bool(snap["synthetic"])}}

    @app.post("/api/v1/context/validate", tags=["context"])
    def validate_context(body: s.ContextRequest, p: Principal = Depends(reader)) -> dict:
        snap = service.snapshot(p.tenant_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "context.validated", {"session_id": body.session_id})
        return {"valid": True, "session_id": body.session_id, "tenant_id": p.tenant_id, "user_id": p.user_id, "roles": sorted(p.roles),
                "can_approve": p.is_human, "snapshot_id": snap["id"], "snapshot_as_of": snap["as_of_date"],
                "authorized_context_ref": f"{p.tenant_id}:{p.user_id}:{body.session_id}", "catalog": service.catalog(p.tenant_id)}

    # ------------------------------------------------------------------ SAP (read-only)
    @app.get("/api/v1/sap/inventory", tags=["sap"])
    def sap_inventory(location: str | None = Query(default=None, pattern=s.CODE), item_id: str | None = Query(default=None, pattern=s.CODE),
                      include_unusable: bool = True, p: Principal = Depends(reader)) -> dict:
        return service.inventory(p, location, item_id, include_unusable)

    @app.get("/api/v1/sap/bom/{sku}", tags=["sap"])
    def sap_bom(sku: str, on: date | None = None, p: Principal = Depends(reader)) -> dict:
        return service.bom(p, sku, on)

    @app.get("/api/v1/sap/production-orders", tags=["sap"])
    def sap_production_orders(sku: str | None = Query(default=None, pattern=s.CODE), status: str | None = None, p: Principal = Depends(reader)) -> dict:
        return service.table(p, "production_orders", {"sku": sku, "status": status})

    @app.get("/api/v1/sap/purchase-orders", tags=["sap"])
    def sap_purchase_orders(material_id: str | None = Query(default=None, pattern=s.CODE), supplier_id: str | None = Query(default=None, pattern=s.CODE),
                            status: str | None = None, p: Principal = Depends(reader)) -> dict:
        return service.table(p, "purchase_orders", {"material_id": material_id, "supplier_id": supplier_id, "status": status})

    @app.get("/api/v1/sap/warehouses", tags=["sap"])
    def sap_warehouses(p: Principal = Depends(reader)) -> dict:
        return service.table(p, "warehouses", {})

    @app.get("/api/v1/sap/suppliers", tags=["sap"])
    def sap_suppliers(p: Principal = Depends(reader)) -> dict:
        return service.suppliers(p)

    @app.api_route("/api/v1/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"], tags=["sap"], include_in_schema=False)
    def sap_write_blocked(path: str, request: Request, p: Principal = Depends(principal)) -> dict:
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "sap.write_blocked", {"path": path, "method": request.method})
        raise HTTPException(status_code=405, detail="SAP is read-only in Phase 1 (SAP_WRITE_ENABLED=false). Record approved actions instead.")

    # ------------------------------------------------------------------ calculations
    @app.post("/api/v1/optimizer/material-readiness", tags=["optimizer"])
    def material_readiness(body: s.MaterialReadinessRequest, p: Principal = Depends(reader)) -> dict:
        return service.material_readiness(p, body.model_dump(mode="json", exclude_none=True))

    @app.post("/api/v1/optimizer/warehouse-balancing", tags=["optimizer"])
    def warehouse_balancing(body: s.WarehouseBalancingRequest, p: Principal = Depends(reader)) -> dict:
        return service.warehouse_balancing(p, body.model_dump(exclude_none=True))

    @app.post("/api/v1/optimizer/replenishment", tags=["optimizer"])
    def replenishment(body: s.ReplenishmentRequest, p: Principal = Depends(reader)) -> dict:
        return service.replenishment(p, body.model_dump(mode="json", exclude_none=True))

    @app.post("/api/v1/forecast/demand", tags=["forecast"])
    def forecast_demand(body: s.DemandForecastRequest, p: Principal = Depends(reader)) -> dict:
        return service.forecast_demand(p, body.model_dump())

    @app.post("/api/v1/forecast/lead-time", tags=["forecast"])
    def forecast_lead_time(body: s.LeadTimeRequest, p: Principal = Depends(reader)) -> dict:
        return service.lead_time(p, body.model_dump(exclude_none=True))

    @app.post("/api/v1/quality/check-stock", tags=["quality"])
    def quality_check(body: s.QualityCheckRequest, p: Principal = Depends(reader)) -> dict:
        return service.quality_check(p, body.model_dump(exclude_none=True))

    @app.get("/api/v1/calculations/{calculation_id}", tags=["optimizer"])
    def calculation(calculation_id: str, p: Principal = Depends(reader)) -> dict:
        return service.calculation(p, calculation_id)

    # ------------------------------------------------------------------ RAG
    @app.post("/api/v1/rag/search", tags=["rag"])
    def rag_search(body: s.RagSearchRequest, p: Principal = Depends(reader)) -> dict:
        if not settings.rag_enabled:
            raise HTTPException(status_code=503, detail="RAG is disabled (RAG_ENABLED=false)")
        return kb.search(p.tenant_id, p.roles, body.query, body.top_k, biz_date(p))

    @app.get("/api/v1/rag/documents", tags=["rag"])
    def rag_documents(p: Principal = Depends(reader)) -> dict:
        return {"documents": db.query("select doc_id, version, title, category, valid_from, valid_to, flags, source_path from rag_documents where tenant_id=?", (p.tenant_id,)),
                "last_ingestion": ingest_report}

    # ------------------------------------------------------------------ RAG tuning console (administrators)
    rag_tuning_api.register(app, db=db, kb=kb, security=security, settings=settings, principal_dep=principal, biz_date=biz_date)

    # ------------------------------------------------------------------ decisions
    @app.post("/api/v1/decisions", tags=["decisions"], status_code=201)
    def create_decision(body: s.DecisionCreateRequest, p: Principal = Depends(reader)) -> dict:
        security.require(p, {"agent_service", "planner"}, "Creating a recommendation")
        return service.create_decision(p, body.model_dump(exclude_none=True))

    @app.get("/api/v1/decisions", tags=["decisions"])
    def list_decisions(status: str | None = Query(default=None, pattern=r"^[a-z_]+$"), p: Principal = Depends(reader)) -> list[dict]:
        return service.list_decisions(p, status)

    @app.get("/api/v1/decisions/{rec_id}", tags=["decisions"])
    def get_decision(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.get_decision(p, rec_id)

    @app.post("/api/v1/decisions/{rec_id}/review", tags=["decisions"])
    def review(rec_id: str, body: s.ReviewRequest, p: Principal = Depends(principal)) -> dict:
        return service.review(p, rec_id, body.model_dump(exclude_none=True))

    @app.post("/api/v1/decisions/{rec_id}/withdraw", tags=["decisions"])
    def withdraw(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.withdraw(p, rec_id)

    @app.post("/api/v1/decisions/{rec_id}/sap-execution", tags=["decisions"])
    def sap_execution(rec_id: str, body: s.SapExecutionRequest, p: Principal = Depends(principal)) -> dict:
        return service.record_sap_execution(p, rec_id, body.model_dump(mode="json"))

    # ------------------------------------------------------------------ learning
    @app.post("/api/v1/outcomes/reconcile", tags=["learning"])
    def reconcile(body: s.ReconcileRequest, p: Principal = Depends(principal)) -> dict:
        return service.reconcile(p, body.recommendation_id)

    @app.get("/api/v1/learning/metrics", tags=["learning"])
    def learning_metrics(p: Principal = Depends(reader)) -> dict:
        return service.learning_metrics(p)

    @app.post("/api/v1/learning/train-lead-time-model", tags=["learning"])
    def train(p: Principal = Depends(principal)) -> dict:
        security.require(p, {"mlops_engineer"}, "Training a model")
        result = learning.train_lead_time_model(db, p.tenant_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.trained", {"model_version_id": result["model_version_id"]})
        return result

    @app.post("/api/v1/learning/models/{model_id}/promote", tags=["learning"])
    def promote(model_id: str, p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Promoting a model (manual gate)")
        result = learning.promote(db, p.tenant_id, model_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.promoted", {"model_version_id": model_id})
        return result

    @app.post("/api/v1/learning/retraining-requests", tags=["learning"], status_code=201)
    def retraining(body: s.RetrainingRequest, p: Principal = Depends(reader)) -> dict:
        result = learning.retraining_request(db, p.tenant_id, p.user_id, body.reason)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.retraining_requested", {"id": result["id"]})
        return result

    @app.get("/api/v1/audit", tags=["learning"])
    def audit(limit: int = Query(default=50, ge=1, le=500), p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Reading the audit log")
        return {"chain_valid": security.verify_chain(),
                "events": db.query("select * from audit_events where tenant_id=? order by id desc limit ?", (p.tenant_id, limit))}

    return app
# Entry point: `uvicorn backend.scinsight.app:create_app --factory --port 8100` (tests call create_app() with their own settings).
