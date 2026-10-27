"""SupplyChain Insight AI — the SCInsight API routes (an APIRouter of the ONE FastAPI app, backend/app/main.py).

    Included under /scinsight: http://localhost:8000/scinsight/api/v1/... · Swagger (tag "SCInsight API"): http://localhost:8000/docs

Every route authenticates the caller from its API key (X-API-Key or Authorization: Bearer). The tenant and roles come from
the key; SAP is read-only (writes -> 405); recommendations need an authorised human review; nothing posts to SAP.
"""
# Postpone evaluation of type hints (lets "SciSettings | None" work everywhere and speeds up import).
from __future__ import annotations

# `date` is the type of the business date (the SAP snapshot "as of" day) passed to RAG validity filtering.
from datetime import date
from types import SimpleNamespace

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

# Project modules: synthetic SAP data loader + governed ML learning functions.
from backend.scinsight import fixtures, learning
# Pydantic request models, imported under the short alias `s` (s.MaterialReadinessRequest, s.CODE, ...).
from backend.scinsight import schemas as s
# Database wrapper (SQLite or PostgreSQL) and a helper that creates the PostgreSQL database when missing.
from backend.scinsight.db import Database, ensure_postgres_database
# Private RAG knowledge base and the embedding-model factory.
from backend.scinsight.rag import KnowledgeBase, make_embedder
from backend.scinsight.rag_tuning import api as rag_tuning_api
# Security: READ_ROLES (who may read), Principal (the authenticated caller), Security (auth + roles + audit chain).
from backend.scinsight.security import READ_ROLES, Principal, Security
# Service = all use cases (calculations, decisions, learning) called by the routes below.
from backend.scinsight.service import Service
# Environment-driven settings (database URL, feature flags, API keys of the synthetic users).
from backend.scinsight.settings import SciSettings

# OpenAPI tag descriptions: they group the routes in Swagger (/docs). Pure documentation, no behaviour.
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


def create_router(settings: SciSettings | None = None, db: Database | None = None) -> APIRouter:
    """Database, fixtures, security, RAG and every SCInsight route; backend/app/main.py includes it at /scinsight."""
    # SIMPLE: use the given settings, or read them from the environment.
    # TECH: `a or b` returns b when a is None; SciSettings() is a pydantic-settings model that reads env vars + .env.
    settings = settings or SciSettings()
    # BUSINESS RULE (safety): Phase 1 is read-only towards SAP. Refuse to even start if someone enabled writes.
    if settings.sap_write_enabled:
        raise RuntimeError("SAP_WRITE_ENABLED=true is not allowed in Phase 1: SupplyChain Insight AI is read-only towards SAP")
    # Deployment path (PostgreSQL). str.startswith accepts a tuple: matches either URL scheme.
    if settings.sci_database_url.startswith(("postgresql://", "postgres://")):
        # Deployments never fall back to the public sci-dev-* keys (those exist only for hermetic SQLite tests).
        # SECURITY: if fixtures (synthetic users) are loaded, every user must have a real, generated API key.
        if settings.sci_load_fixtures and settings.missing_keys():
            raise RuntimeError("missing user keys (run scripts/gen-env.py --add-missing): " + ", ".join(settings.missing_keys()))
        # Create the PostgreSQL database itself if it does not exist yet (only when we open our own connection).
        if db is None:
            ensure_postgres_database(settings.sci_database_url)
    # Open the database (SQLite file/in-memory or PostgreSQL pool) unless one was injected.
    db = db or Database(settings.sci_database_url)
    # Apply the versioned SQL migrations (backend/scinsight/migrations/*.sql) that were not applied yet.
    db.migrate()
    # Load the synthetic SAP snapshot, users and role assignments (idempotent: existing rows are kept).
    if settings.sci_load_fixtures:
        fixtures.load(db, settings.user_keys())
    # Create the shared service objects (one instance each for the whole app, captured by the route closures below).
    security = Security(db)
    service = Service(db, settings, security)
    kb = KnowledgeBase(db, make_embedder(settings.sci_embedding_backend), settings.sci_embedding_backend)
    # Ingest the governed policy documents at start-up (skipped documents keep their stored chunks). {} = RAG disabled.
    ingest_report = kb.ingest_dir(settings.sci_knowledge_dir) if settings.rag_enabled else {}

    router = APIRouter()
    # shared objects, reachable as app.state.scinsight in the gateway app (tests and the RAG tuning routes use them)
    router.state = SimpleNamespace(db=db, service=service, security=security, kb=kb, ingest_report=ingest_report)

    # ===== FUNCTION: create_router.principal() =====
    # ID: F1994 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:61-64
    # ROLE: FastAPI dependency that authenticates EVERY request: turns the API key into a Principal (user, tenant, roles).
    # INPUTS:
    #   request: Request             -> the HTTP request (required by FastAPI's signature, not read here).
    #   x_api_key: str | None        -> header "X-API-Key" (Header() converts the parameter name to the header name).
    #   authorization: str | None    -> header "Authorization: Bearer <key>" (OpenAI-style clients).
    #   x_tenant: str | None         -> header "X-Tenant"; only CHECKED against the key's tenant, never trusted.
    # OUTPUT:
    #   Principal -> frozen dataclass (user_id, tenant_id, roles, name). 401 if no/invalid key, 403 if the tenant is forged.
    # CALLED BY:
    #   <- F1993 create_router() (references)
    #   <- F1995 create_router.reader() (references)
    #   <- F1995 create_router.reader() (depends_on)
    #   <- F2006 create_router.sap_write_blocked() (references)
    #   <- F2006 create_router.sap_write_blocked() (depends_on)
    #   <- F2019 create_router.review() (references)
    #   <- F2019 create_router.review() (depends_on)
    #   <- F2021 create_router.sap_execution() (references)
    #   <- F2021 create_router.sap_execution() (depends_on)
    #   <- F2022 create_router.reconcile() (references)
    #   <- F2022 create_router.reconcile() (depends_on)
    #   <- F2024 create_router.train() (references)
    # CALLS:
    #   -> F0776 Security.authenticate() (calls)
    #   -> F0772 Principal (references)
    def principal(request: Request, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None),
                  x_tenant: str | None = Header(default=None)) -> Principal:
        # Extract the token after "Bearer " (7 characters) when an Authorization header is present; otherwise None.
        bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
        # Prefer X-API-Key, fall back to the bearer token; Security.authenticate looks up the hashed key in the users table.
        return security.authenticate(x_api_key or bearer, x_tenant)

    # ===== FUNCTION: create_router.reader() =====
    # ID: F1995 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:66-68
    # ROLE: Second-level dependency: an authenticated caller that ALSO has a read role (humans, agent_service, mlops_engineer).
    # INPUTS:
    #   p: Principal -> injected by FastAPI: Depends(principal) runs principal() first and passes its result here.
    # OUTPUT:
    #   Principal -> the same caller, after the role check (403 if none of READ_ROLES).
    # CALLED BY:
    #   <- F1998 create_router.context() (references)
    #   <- F1998 create_router.context() (depends_on)
    #   <- F1999 create_router.validate_context() (references)
    #   <- F1999 create_router.validate_context() (depends_on)
    #   <- F2000 create_router.sap_inventory() (references)
    #   <- F2000 create_router.sap_inventory() (depends_on)
    #   <- F2001 create_router.sap_bom() (references)
    #   <- F2001 create_router.sap_bom() (depends_on)
    #   <- F2002 create_router.sap_production_orders() (references)
    #   <- F2002 create_router.sap_production_orders() (depends_on)
    #   <- F2003 create_router.sap_purchase_orders() (references)
    #   <- F2003 create_router.sap_purchase_orders() (depends_on)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F1994 create_router.principal() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F1994 create_router.principal() (depends_on)
    def reader(p: Principal = Depends(principal)) -> Principal:
        # Raises HTTPException(403) when the caller has none of the read roles. "This endpoint" is used in the error text.
        security.require(p, READ_ROLES, "This endpoint")
        return p

    # ===== FUNCTION: create_router.biz_date() =====
    # ID: F1996 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:70-71
    # ROLE: Business date of the caller's tenant = the "as of" day of its current SAP snapshot (used to filter RAG by validity).
    # INPUTS:
    #   p: Principal -> the caller (only its tenant_id is used).
    # OUTPUT:
    #   date -> snapshot as-of date (409 from service.snapshot when no fresh snapshot exists).
    # CALLED BY:
    #   <- F1993 create_router() (references)
    #   <- F2014 create_router.rag_search() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    def biz_date(p: Principal) -> date:
        return service.snapshot(p.tenant_id)["as_of"]

    @router.get("/health", tags=["context"])
    def health() -> dict:
        # Returning a dict -> FastAPI serialises it to JSON with status 200.
        return {"status": "ok", "sap_mode": settings.sap_mode, "sap_write_enabled": False, "human_approval_required": settings.human_approval_required,
                "industry_sharing_enabled": settings.industry_sharing_enabled, "database": db.dialect}

    # ------------------------------------------------------------------ context
    @router.get("/api/v1/context", tags=["context"])
    def context(p: Principal = Depends(reader)) -> dict:
        # Current valid snapshot of the tenant (409 if missing or older than SCI_SNAPSHOT_MAX_AGE_DAYS).
        snap = service.snapshot(p.tenant_id)
        # sorted(p.roles): roles is a frozenset (unordered); sorting gives a stable JSON list.
        return {"user_id": p.user_id, "name": p.name, "tenant_id": p.tenant_id, "roles": sorted(p.roles), "is_human": p.is_human,
                "snapshot": {"id": snap["id"], "as_of": snap["as_of_date"], "age_days": snap["age_days"], "synthetic": bool(snap["synthetic"])}}

    @router.post("/api/v1/context/validate", tags=["context"])
    def validate_context(body: s.ContextRequest, p: Principal = Depends(reader)) -> dict:
        snap = service.snapshot(p.tenant_id)
        # Append an entry to the tamper-evident audit chain (who validated which session).
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "context.validated", {"session_id": body.session_id})
        # can_approve = p.is_human: an agent key can never approve (only humans with a reviewer role can).
        return {"valid": True, "session_id": body.session_id, "tenant_id": p.tenant_id, "user_id": p.user_id, "roles": sorted(p.roles),
                "can_approve": p.is_human, "snapshot_id": snap["id"], "snapshot_as_of": snap["as_of_date"],
                "authorized_context_ref": f"{p.tenant_id}:{p.user_id}:{body.session_id}", "catalog": service.catalog(p.tenant_id)}

    # ------------------------------------------------------------------ SAP (read-only)
    @router.get("/api/v1/sap/inventory", tags=["sap"])
    def sap_inventory(location: str | None = Query(default=None, pattern=s.CODE), item_id: str | None = Query(default=None, pattern=s.CODE),
                      include_unusable: bool = True, p: Principal = Depends(reader)) -> dict:
        # Thin route: all logic lives in Service.inventory (testable without HTTP).
        return service.inventory(p, location, item_id, include_unusable)

    @router.get("/api/v1/sap/bom/{sku}", tags=["sap"])
    def sap_bom(sku: str, on: date | None = None, p: Principal = Depends(reader)) -> dict:
        return service.bom(p, sku, on)

    @router.get("/api/v1/sap/production-orders", tags=["sap"])
    def sap_production_orders(sku: str | None = Query(default=None, pattern=s.CODE), status: str | None = None, p: Principal = Depends(reader)) -> dict:
        # The table name is fixed HERE by the route (never by the client) -> no SQL injection through the table name.
        return service.table(p, "production_orders", {"sku": sku, "status": status})

    @router.get("/api/v1/sap/purchase-orders", tags=["sap"])
    def sap_purchase_orders(material_id: str | None = Query(default=None, pattern=s.CODE), supplier_id: str | None = Query(default=None, pattern=s.CODE),
                            status: str | None = None, p: Principal = Depends(reader)) -> dict:
        return service.table(p, "purchase_orders", {"material_id": material_id, "supplier_id": supplier_id, "status": status})

    @router.get("/api/v1/sap/warehouses", tags=["sap"])
    def sap_warehouses(p: Principal = Depends(reader)) -> dict:
        # {} = no filters.
        return service.table(p, "warehouses", {})

    @router.get("/api/v1/sap/suppliers", tags=["sap"])
    def sap_suppliers(p: Principal = Depends(reader)) -> dict:
        return service.suppliers(p)

    @router.api_route("/api/v1/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"], tags=["sap"], include_in_schema=False)
    def sap_write_blocked(path: str, request: Request, p: Principal = Depends(principal)) -> dict:
        # Audit first, so the blocked attempt is recorded even though the request fails.
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "sap.write_blocked", {"path": path, "method": request.method})
        # 405 Method Not Allowed: the API itself refuses writes; the detail tells the caller what to do instead.
        raise HTTPException(status_code=405, detail="SAP is read-only in Phase 1 (SAP_WRITE_ENABLED=false). Record approved actions instead.")

    # ------------------------------------------------------------------ calculations
    @router.post("/api/v1/optimizer/material-readiness", tags=["optimizer"])
    def material_readiness(body: s.MaterialReadinessRequest, p: Principal = Depends(reader)) -> dict:
        # model_dump(mode="json") converts dates to "YYYY-MM-DD" strings; exclude_none drops fields the caller did not send.
        return service.material_readiness(p, body.model_dump(mode="json", exclude_none=True))

    @router.post("/api/v1/optimizer/warehouse-balancing", tags=["optimizer"])
    def warehouse_balancing(body: s.WarehouseBalancingRequest, p: Principal = Depends(reader)) -> dict:
        return service.warehouse_balancing(p, body.model_dump(exclude_none=True))

    @router.post("/api/v1/optimizer/replenishment", tags=["optimizer"])
    def replenishment(body: s.ReplenishmentRequest, p: Principal = Depends(reader)) -> dict:
        return service.replenishment(p, body.model_dump(mode="json", exclude_none=True))

    @router.post("/api/v1/forecast/demand", tags=["forecast"])
    def forecast_demand(body: s.DemandForecastRequest, p: Principal = Depends(reader)) -> dict:
        # No exclude_none here: horizon_days always has a value (default 14).
        return service.forecast_demand(p, body.model_dump())

    @router.post("/api/v1/forecast/lead-time", tags=["forecast"])
    def forecast_lead_time(body: s.LeadTimeRequest, p: Principal = Depends(reader)) -> dict:
        return service.lead_time(p, body.model_dump(exclude_none=True))

    @router.post("/api/v1/quality/check-stock", tags=["quality"])
    def quality_check(body: s.QualityCheckRequest, p: Principal = Depends(reader)) -> dict:
        return service.quality_check(p, body.model_dump(exclude_none=True))

    @router.get("/api/v1/calculations/{calculation_id}", tags=["optimizer"])
    def calculation(calculation_id: str, p: Principal = Depends(reader)) -> dict:
        return service.calculation(p, calculation_id)

    # ------------------------------------------------------------------ RAG
    @router.post("/api/v1/rag/search", tags=["rag"])
    def rag_search(body: s.RagSearchRequest, p: Principal = Depends(reader)) -> dict:
        # 503 Service Unavailable when the RAG feature switch is off.
        if not settings.rag_enabled:
            raise HTTPException(status_code=503, detail="RAG is disabled (RAG_ENABLED=false)")
        # biz_date(p): documents are only valid between valid_from and valid_to on the SAP business date.
        return kb.search(p.tenant_id, p.roles, body.query, body.top_k, biz_date(p))

    @router.get("/api/v1/rag/documents", tags=["rag"])
    def rag_documents(p: Principal = Depends(reader)) -> dict:
        # SQL with a "?" placeholder: the tenant id is passed as a parameter (never concatenated) -> no SQL injection.
        return {"documents": db.query("select doc_id, version, title, category, valid_from, valid_to, flags, source_path from rag_documents where tenant_id=?", (p.tenant_id,)),
                "last_ingestion": ingest_report}

    # ------------------------------------------------------------------ RAG tuning console (administrators)
    rag_tuning_api.register(router, db=db, kb=kb, security=security, settings=settings, principal_dep=principal, biz_date=biz_date)

    # ------------------------------------------------------------------ decisions
    @router.post("/api/v1/decisions", tags=["decisions"], status_code=201)
    def create_decision(body: s.DecisionCreateRequest, p: Principal = Depends(reader)) -> dict:
        # AUTHORIZATION: only the agent service or a planner may create recommendations (403 otherwise).
        security.require(p, {"agent_service", "planner"}, "Creating a recommendation")
        return service.create_decision(p, body.model_dump(exclude_none=True))

    @router.get("/api/v1/decisions", tags=["decisions"])
    def list_decisions(status: str | None = Query(default=None, pattern=r"^[a-z_]+$"), p: Principal = Depends(reader)) -> list[dict]:
        return service.list_decisions(p, status)

    @router.get("/api/v1/decisions/{rec_id}", tags=["decisions"])
    def get_decision(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.get_decision(p, rec_id)

    @router.post("/api/v1/decisions/{rec_id}/review", tags=["decisions"])
    def review(rec_id: str, body: s.ReviewRequest, p: Principal = Depends(principal)) -> dict:
        return service.review(p, rec_id, body.model_dump(exclude_none=True))

    @router.post("/api/v1/decisions/{rec_id}/withdraw", tags=["decisions"])
    def withdraw(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.withdraw(p, rec_id)

    @router.post("/api/v1/decisions/{rec_id}/sap-execution", tags=["decisions"])
    def sap_execution(rec_id: str, body: s.SapExecutionRequest, p: Principal = Depends(principal)) -> dict:
        return service.record_sap_execution(p, rec_id, body.model_dump(mode="json"))

    # ------------------------------------------------------------------ learning
    @router.post("/api/v1/outcomes/reconcile", tags=["learning"])
    def reconcile(body: s.ReconcileRequest, p: Principal = Depends(principal)) -> dict:
        return service.reconcile(p, body.recommendation_id)

    @router.get("/api/v1/learning/metrics", tags=["learning"])
    def learning_metrics(p: Principal = Depends(reader)) -> dict:
        return service.learning_metrics(p)

    @router.post("/api/v1/learning/train-lead-time-model", tags=["learning"])
    def train(p: Principal = Depends(principal)) -> dict:
        security.require(p, {"mlops_engineer"}, "Training a model")
        result = learning.train_lead_time_model(db, p.tenant_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.trained", {"model_version_id": result["model_version_id"]})
        return result

    @router.post("/api/v1/learning/models/{model_id}/promote", tags=["learning"])
    def promote(model_id: str, p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Promoting a model (manual gate)")
        result = learning.promote(db, p.tenant_id, model_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.promoted", {"model_version_id": model_id})
        return result

    @router.post("/api/v1/learning/retraining-requests", tags=["learning"], status_code=201)
    def retraining(body: s.RetrainingRequest, p: Principal = Depends(reader)) -> dict:
        result = learning.retraining_request(db, p.tenant_id, p.user_id, body.reason)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.retraining_requested", {"id": result["id"]})
        return result

    @router.get("/api/v1/audit", tags=["learning"])
    def audit(limit: int = Query(default=50, ge=1, le=500), p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Reading the audit log")
        return {"chain_valid": security.verify_chain(),
                "events": db.query("select * from audit_events where tenant_id=? order by id desc limit ?", (p.tenant_id, limit))}

    return router
# Included at /scinsight by backend.app.main:create_app (the one FastAPI app); tests wrap create_router() in tests/scinsight/conftest.py.
