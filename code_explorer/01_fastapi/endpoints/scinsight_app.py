# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/app.py
# What this module is: the SCInsight FastAPI application. It builds every HTTP route that the Flowise
# tools, the Flowise Custom Functions and the LangGraph mirror call (port 8100, Swagger at /docs).
# Only comment lines were added; code_explorer/tools/build_registry.py proves the logic is identical
# (AST comparison) and fills the ID / ORIGINAL FILE / CALLED BY / CALLS lines of every header.
# ======================================================================================================

"""SupplyChain Insight AI — business-tool service (FastAPI, Swagger at /docs).

    uvicorn backend.scinsight.app:app --port 8100

Every route authenticates the caller from its API key (X-API-Key or Authorization: Bearer). The tenant and roles come from
the key; SAP is read-only (writes -> 405); recommendations need an authorised human review; nothing posts to SAP.
"""
# Postpone evaluation of type hints (lets "SciSettings | None" work everywhere and speeds up import).
from __future__ import annotations

# `date` is the type of the business date (the SAP snapshot "as of" day) passed to RAG validity filtering.
from datetime import date

# FastAPI building blocks actually used in this file:
#   Depends       -> dependency injection: FastAPI runs principal()/reader() before the endpoint and passes the result in.
#   FastAPI       -> the application object (there is no APIRouter in this project: every route is declared on `app`).
#   Header        -> reads an HTTP header (x_api_key -> "X-API-Key", authorization -> "Authorization").
#   HTTPException -> stops the request and returns an HTTP error code + JSON {"detail": ...}.
#   Query         -> declares a query-string parameter with validation (regex pattern, min/max).
#   Request       -> the raw request (used to read the HTTP method of a blocked SAP write).
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request

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


# ===== FUNCTION: create_app() =====
# ID: F0112 · function · used
# ORIGINAL FILE: backend/scinsight/app.py:36-228
# ROLE: Application factory. Builds the database, loads the synthetic SAP data, creates the Security, Service and
#       KnowledgeBase objects, ingests the policy documents, then declares all 33 HTTP routes as nested functions
#       (closures) that share those objects. Tests call it with their own settings/database; uvicorn calls it with none.
# INPUTS:
#   settings: SciSettings | None -> configuration; None = read the environment / .env file.
#   db: Database | None          -> an existing database (tests pass an in-memory SQLite one); None = open settings.sci_database_url.
# OUTPUT:
#   FastAPI -> the ready application (routes registered, app.state holding db/service/security/kb/ingest_report).
# RAISES:
#   RuntimeError when SAP writes are enabled (forbidden in Phase 1) or when deployment API keys are missing.
# CALLED BY:
#   <- F0909 app() (calls)
#   <- F1928 client() (calls)
#   <- F0846 test_configured_keys_rotate_out_stored_dev_keys() (calls)
#   <- F0847 test_postgres_deployment_refuses_to_start_without_all_keys() (calls)
#   <- F0851 test_sap_write_enabled_refuses_to_start() (calls)
#   <- F0852 test_expired_snapshot_blocks_calculations() (calls)
# CALLS:
#   -> F0013 SciSettings (references)
#   -> F0418 Database (references)
#   -> F0013 SciSettings (calls)
#   -> F0015 SciSettings.missing_keys() (calls)
#   -> F0417 ensure_postgres_database() (calls)
#   -> F0418 Database (calls)
#   -> F0429 Database.migrate() (calls)
#   -> F0432 load() (calls)
#   -> F0014 SciSettings.user_keys() (calls)
#   -> F0774 Security (calls)
#   -> F0311 Service (calls)
#   -> F0763 KnowledgeBase (calls)
def create_app(settings: SciSettings | None = None, db: Database | None = None) -> FastAPI:
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

    # FastAPI() creates the application. title/version/description/openapi_tags only feed the Swagger documentation.
    app = FastAPI(title="SupplyChain Insight AI — business tools", version="1.0.0", openapi_tags=TAGS,
                  description="Cosmetics supply-chain POC: synthetic SAP data, deterministic calculations, human-approved decisions, verified-outcome learning.")
    # app.state is a free-form namespace: tests read app.state.db / app.state.service directly. Tuple assignment sets 5 attributes at once.
    app.state.db, app.state.service, app.state.security, app.state.kb, app.state.ingest_report = db, service, security, kb, ingest_report

    # ===== FUNCTION: create_app.principal() =====
    # ID: F0113 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:59-62
    # ROLE: FastAPI dependency that authenticates EVERY request: turns the API key into a Principal (user, tenant, roles).
    # INPUTS:
    #   request: Request             -> the HTTP request (required by FastAPI's signature, not read here).
    #   x_api_key: str | None        -> header "X-API-Key" (Header() converts the parameter name to the header name).
    #   authorization: str | None    -> header "Authorization: Bearer <key>" (OpenAI-style clients).
    #   x_tenant: str | None         -> header "X-Tenant"; only CHECKED against the key's tenant, never trusted.
    # OUTPUT:
    #   Principal -> frozen dataclass (user_id, tenant_id, roles, name). 401 if no/invalid key, 403 if the tenant is forged.
    # CALLED BY:
    #   <- F0112 create_app() (references)
    #   <- F0114 create_app.reader() (references)
    #   <- F0114 create_app.reader() (depends_on)
    #   <- F0125 create_app.sap_write_blocked() (references)
    #   <- F0125 create_app.sap_write_blocked() (depends_on)
    #   <- F0138 create_app.review() (references)
    #   <- F0138 create_app.review() (depends_on)
    #   <- F0140 create_app.sap_execution() (references)
    #   <- F0140 create_app.sap_execution() (depends_on)
    #   <- F0141 create_app.reconcile() (references)
    #   <- F0141 create_app.reconcile() (depends_on)
    #   <- F0143 create_app.train() (references)
    # CALLS:
    #   -> F0776 Security.authenticate() (calls)
    #   -> F0772 Principal (references)
    def principal(request: Request, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None),
                  x_tenant: str | None = Header(default=None)) -> Principal:
        # Extract the token after "Bearer " (7 characters) when an Authorization header is present; otherwise None.
        bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
        # Prefer X-API-Key, fall back to the bearer token; Security.authenticate looks up the hashed key in the users table.
        return security.authenticate(x_api_key or bearer, x_tenant)

    # ===== FUNCTION: create_app.reader() =====
    # ID: F0114 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:64-66
    # ROLE: Second-level dependency: an authenticated caller that ALSO has a read role (humans, agent_service, mlops_engineer).
    # INPUTS:
    #   p: Principal -> injected by FastAPI: Depends(principal) runs principal() first and passes its result here.
    # OUTPUT:
    #   Principal -> the same caller, after the role check (403 if none of READ_ROLES).
    # CALLED BY:
    #   <- F0117 create_app.context() (references)
    #   <- F0117 create_app.context() (depends_on)
    #   <- F0118 create_app.validate_context() (references)
    #   <- F0118 create_app.validate_context() (depends_on)
    #   <- F0119 create_app.sap_inventory() (references)
    #   <- F0119 create_app.sap_inventory() (depends_on)
    #   <- F0120 create_app.sap_bom() (references)
    #   <- F0120 create_app.sap_bom() (depends_on)
    #   <- F0121 create_app.sap_production_orders() (references)
    #   <- F0121 create_app.sap_production_orders() (depends_on)
    #   <- F0122 create_app.sap_purchase_orders() (references)
    #   <- F0122 create_app.sap_purchase_orders() (depends_on)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    def reader(p: Principal = Depends(principal)) -> Principal:
        # Raises HTTPException(403) when the caller has none of the read roles. "This endpoint" is used in the error text.
        security.require(p, READ_ROLES, "This endpoint")
        return p

    # ===== FUNCTION: create_app.biz_date() =====
    # ID: F0115 · nested · used
    # ORIGINAL FILE: backend/scinsight/app.py:68-69
    # ROLE: Business date of the caller's tenant = the "as of" day of its current SAP snapshot (used to filter RAG by validity).
    # INPUTS:
    #   p: Principal -> the caller (only its tenant_id is used).
    # OUTPUT:
    #   date -> snapshot as-of date (409 from service.snapshot when no fresh snapshot exists).
    # CALLED BY:
    #   <- F0112 create_app() (references)
    #   <- F0133 create_app.rag_search() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0313 Service.snapshot() (calls)
    def biz_date(p: Principal) -> date:
        return service.snapshot(p.tenant_id)["as_of"]

    # ===== FUNCTION: create_app.health() =====
    # ID: F0116 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:71-74
    # ROLE: Liveness probe (no authentication): shows the safety switches so an operator can see SAP is read-only.
    # INPUTS:
    #   none.
    # OUTPUT:
    #   dict -> {"status": "ok", "sap_mode", "sap_write_enabled": False, "human_approval_required", "industry_sharing_enabled", "database"}.
    # Decorator @app.get(path) registers the function below as the handler of HTTP GET /health; tags group it in Swagger.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @app.get("/health", tags=["context"])
    def health() -> dict:
        # Returning a dict -> FastAPI serialises it to JSON with status 200.
        return {"status": "ok", "sap_mode": settings.sap_mode, "sap_write_enabled": False, "human_approval_required": settings.human_approval_required,
                "industry_sharing_enabled": settings.industry_sharing_enabled, "database": db.dialect}

    # ------------------------------------------------------------------ context
    # ===== FUNCTION: create_app.context() =====
    # ID: F0117 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:77-81
    # ROLE: "Who am I?" — identity, tenant, roles and the freshness of the tenant's SAP snapshot.
    # INPUTS:
    #   p: Principal -> injected by Depends(reader) (authenticated + read role).
    # OUTPUT:
    #   dict -> user_id, name, tenant_id, roles (sorted list), is_human, snapshot {id, as_of, age_days, synthetic}.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/context", tags=["context"])
    def context(p: Principal = Depends(reader)) -> dict:
        # Current valid snapshot of the tenant (409 if missing or older than SCI_SNAPSHOT_MAX_AGE_DAYS).
        snap = service.snapshot(p.tenant_id)
        # sorted(p.roles): roles is a frozenset (unordered); sorting gives a stable JSON list.
        return {"user_id": p.user_id, "name": p.name, "tenant_id": p.tenant_id, "roles": sorted(p.roles), "is_human": p.is_human,
                "snapshot": {"id": snap["id"], "as_of": snap["as_of_date"], "age_days": snap["age_days"], "synthetic": bool(snap["synthetic"])}}

    # ===== FUNCTION: create_app.validate_context() =====
    # ID: F0118 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:83-89
    # ROLE: Context check that EVERY Flowise / LangGraph run performs first ("2 · Check access"): validates the caller,
    #       audits the session, and returns the identifier catalog the LLM uses to map names to codes.
    # INPUTS:
    #   body: s.ContextRequest -> JSON body {"session_id": "..."} validated by Pydantic (3-128 safe characters).
    #   p: Principal           -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> valid, session_id, tenant_id, user_id, roles, can_approve, snapshot_id, snapshot_as_of,
    #           authorized_context_ref "tenant:user:session", catalog {products, materials, locations, suppliers, production_orders}.
    # CALLED BY:
    #   <- F0656 context() (http_request)
    #   <- Decision-Outcome-Learning-Agentflow · 2 · Check access (http_request)
    #   <- Factory-Planning-Agentflow · 2 · Check access (http_request)
    #   <- Inventory-Optimizer-Agentflow · 2 · Check access (http_request)
    #   <- Logistics-Agentflow · 2 · Check access (http_request)
    #   <- Procurement-Agentflow · 2 · Check access (http_request)
    #   <- Quality-Agentflow · 2 · Check access (http_request)
    #   <- Supervisor-Agentflow · 2 · Check access (http_request)
    #   <- Warehouse-Agentflow · 2 · Check access (http_request)
    # CALLS:
    #   -> F0178 ContextRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0313 Service.snapshot() (calls)
    #   -> F0779 Security.audit() (calls)
    #   -> F0322 Service.catalog() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0178 ContextRequest (validates_input)
    @app.post("/api/v1/context/validate", tags=["context"])
    def validate_context(body: s.ContextRequest, p: Principal = Depends(reader)) -> dict:
        snap = service.snapshot(p.tenant_id)
        # Append an entry to the tamper-evident audit chain (who validated which session).
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "context.validated", {"session_id": body.session_id})
        # can_approve = p.is_human: an agent key can never approve (only humans with a reviewer role can).
        return {"valid": True, "session_id": body.session_id, "tenant_id": p.tenant_id, "user_id": p.user_id, "roles": sorted(p.roles),
                "can_approve": p.is_human, "snapshot_id": snap["id"], "snapshot_as_of": snap["as_of_date"],
                "authorized_context_ref": f"{p.tenant_id}:{p.user_id}:{body.session_id}", "catalog": service.catalog(p.tenant_id)}

    # ------------------------------------------------------------------ SAP (read-only)
    # ===== FUNCTION: create_app.sap_inventory() =====
    # ID: F0119 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:92-95
    # ROLE: Read-only SAP stock by batch, with a per (location, item) summary of usable vs excluded stock.
    # INPUTS:
    #   location: str | None    -> query ?location=WH-B (validated by the regex s.CODE, else 422).
    #   item_id: str | None     -> query ?item_id=SUN-SPF50-100 (same regex).
    #   include_unusable: bool  -> query ?include_unusable=false hides non-released batches (default True).
    #   p: Principal            -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> snapshot, as_of, items (summaries), batches (raw rows), rules.
    # Called by the Flowise Custom Tool get_sap_inventory (GET /api/v1/sap/inventory).
    # CALLED BY:
    #   <- F0845 test_unauthenticated_and_invalid_keys() (http_request)
    #   <- F0849 test_cross_tenant_data_is_invisible() (http_request)
    #   <- F0853 test_missing_snapshot_blocks_calculations() (http_request)
    #   <- Flowise Custom Tool · get_sap_inventory (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0319 Service.inventory() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/inventory", tags=["sap"])
    def sap_inventory(location: str | None = Query(default=None, pattern=s.CODE), item_id: str | None = Query(default=None, pattern=s.CODE),
                      include_unusable: bool = True, p: Principal = Depends(reader)) -> dict:
        # Thin route: all logic lives in Service.inventory (testable without HTTP).
        return service.inventory(p, location, item_id, include_unusable)

    # ===== FUNCTION: create_app.sap_bom() =====
    # ID: F0120 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:97-99
    # ROLE: Read-only bill of materials of a finished good, plus the requirements for ONE unit from the valid approved version.
    # INPUTS:
    #   sku: str          -> path parameter /api/v1/sap/bom/{sku}.
    #   on: date | None   -> query ?on=YYYY-MM-DD (FastAPI parses it into a date); None = snapshot date.
    #   p: Principal      -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> sku, snapshot, current_for_one_unit (or {"error": ...}), versions (all BOM rows).
    # CALLED BY:
    #   <- Flowise Custom Tool · get_material_bom (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0320 Service.bom() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/bom/{sku}", tags=["sap"])
    def sap_bom(sku: str, on: date | None = None, p: Principal = Depends(reader)) -> dict:
        return service.bom(p, sku, on)

    # ===== FUNCTION: create_app.sap_production_orders() =====
    # ID: F0121 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:101-103
    # ROLE: Read-only SAP production orders, optionally filtered by SKU and status.
    # INPUTS:
    #   sku: str | None     -> query ?sku= (regex-validated).
    #   status: str | None  -> query ?status=released|planned.
    #   p: Principal        -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"snapshot", "as_of", "items": [production order rows]}.
    # CALLED BY:
    #   <- F0669 calc_factory() (http_request)
    #   <- Flowise Custom Tool · get_production_orders (http_request)
    #   <- Factory-Planning-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0321 Service.table() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/production-orders", tags=["sap"])
    def sap_production_orders(sku: str | None = Query(default=None, pattern=s.CODE), status: str | None = None, p: Principal = Depends(reader)) -> dict:
        # The table name is fixed HERE by the route (never by the client) -> no SQL injection through the table name.
        return service.table(p, "production_orders", {"sku": sku, "status": status})

    # ===== FUNCTION: create_app.sap_purchase_orders() =====
    # ID: F0122 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:105-108
    # ROLE: Read-only SAP purchase orders, filtered by material, supplier and/or status.
    # INPUTS:
    #   material_id, supplier_id: str | None -> regex-validated query parameters.
    #   status: str | None                   -> open | confirmed | received | cancelled.
    #   p: Principal                         -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"snapshot", "as_of", "items": [purchase order rows]}.
    # CALLED BY:
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0850 test_sap_writes_are_blocked() (http_request)
    #   <- Flowise Custom Tool · get_open_purchase_orders (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0321 Service.table() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/purchase-orders", tags=["sap"])
    def sap_purchase_orders(material_id: str | None = Query(default=None, pattern=s.CODE), supplier_id: str | None = Query(default=None, pattern=s.CODE),
                            status: str | None = None, p: Principal = Depends(reader)) -> dict:
        return service.table(p, "purchase_orders", {"material_id": material_id, "supplier_id": supplier_id, "status": status})

    # ===== FUNCTION: create_app.sap_warehouses() =====
    # ID: F0123 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:110-112
    # ROLE: Read-only list of the tenant's sites (factory + warehouses with target cover days).
    # INPUTS:
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"snapshot", "as_of", "items": [warehouse rows]}.
    # CALLED BY:
    #   <- F0846 test_configured_keys_rotate_out_stored_dev_keys() (http_request)
    #   <- F0848 test_forged_tenant_is_rejected_and_audited() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0321 Service.table() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/warehouses", tags=["sap"])
    def sap_warehouses(p: Principal = Depends(reader)) -> dict:
        # {} = no filters.
        return service.table(p, "warehouses", {})

    # ===== FUNCTION: create_app.sap_suppliers() =====
    # ID: F0124 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:114-116
    # ROLE: Read-only suppliers with their supplier items (price, MOQ, contract lead time).
    # INPUTS:
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"snapshot", "items": [supplier rows, each with "items": [...]]}.
    # CALLED BY:
    #   <- F0670 calc_procurement() (http_request)
    #   <- Procurement-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0323 Service.suppliers() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/suppliers", tags=["sap"])
    def sap_suppliers(p: Principal = Depends(reader)) -> dict:
        return service.suppliers(p)

    # ===== FUNCTION: create_app.sap_write_blocked() =====
    # ID: F0125 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:118-121
    # ROLE: Safety net: ANY write verb on /api/v1/sap/... is refused with 405 and audited (SAP is read-only in Phase 1).
    # INPUTS:
    #   path: str        -> everything after /api/v1/sap/ ("{path:path}" lets the parameter contain slashes).
    #   request: Request -> used to log the HTTP method.
    #   p: Principal     -> Depends(principal): authenticated (the attempt is attributed to a user), no role needed.
    # OUTPUT:
    #   never returns normally: always raises HTTPException(405).
    # @app.api_route registers one handler for several methods at once; include_in_schema=False hides it from Swagger.
    # CALLED BY:
    #   <- F0017 create_app() (http_request)
    #   <- F0100 create_app.sap_documents() (http_request)
    #   <- F0669 calc_factory() (http_request)
    #   <- F0670 calc_procurement() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0845 test_unauthenticated_and_invalid_keys() (http_request)
    #   <- F0846 test_configured_keys_rotate_out_stored_dev_keys() (http_request)
    #   <- F0848 test_forged_tenant_is_rejected_and_audited() (http_request)
    #   <- F0849 test_cross_tenant_data_is_invisible() (http_request)
    #   <- F0850 test_sap_writes_are_blocked() (http_request)
    #   <- F0853 test_missing_snapshot_blocks_calculations() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0779 Security.audit() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    @app.api_route("/api/v1/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"], tags=["sap"], include_in_schema=False)
    def sap_write_blocked(path: str, request: Request, p: Principal = Depends(principal)) -> dict:
        # Audit first, so the blocked attempt is recorded even though the request fails.
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "sap.write_blocked", {"path": path, "method": request.method})
        # 405 Method Not Allowed: the API itself refuses writes; the detail tells the caller what to do instead.
        raise HTTPException(status_code=405, detail="SAP is read-only in Phase 1 (SAP_WRITE_ENABLED=false). Record approved actions instead.")

    # ------------------------------------------------------------------ calculations
    # ===== FUNCTION: create_app.material_readiness() =====
    # ID: F0126 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:124-126
    # ROLE: Factory material readiness: BOM explosion + usable stock + purchase orders -> shortages, supply options, actions.
    # INPUTS:
    #   body: s.MaterialReadinessRequest -> production_order_id ALONE, or sku + quantity + need_date (model validator enforces it).
    #   p: Principal                     -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (calculation_id CALC-..., kind "material_readiness", lines, shortages, proposed_actions, provenance).
    # Called by the Flowise tool check_material_readiness, the Factory specialist Custom Function and the LangGraph mirror.
    # CALLED BY:
    #   <- F0669 calc_factory() (http_request)
    #   <- F0834 test_scenario_1_factory_material_shortage() (http_request)
    #   <- F0835 test_production_order_quantity_cannot_be_overridden() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0852 test_expired_snapshot_blocks_calculations() (http_request)
    #   <- F0854 test_invalid_bom_and_unit_mismatch_are_explained() (http_request)
    #   <- F0855 test_malformed_and_injected_tool_arguments() (http_request)
    #   <- Flowise Custom Tool · check_material_readiness (http_request)
    #   <- Factory-Planning-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0179 MaterialReadinessRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0325 Service.material_readiness() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0179 MaterialReadinessRequest (validates_input)
    @app.post("/api/v1/optimizer/material-readiness", tags=["optimizer"])
    def material_readiness(body: s.MaterialReadinessRequest, p: Principal = Depends(reader)) -> dict:
        # model_dump(mode="json") converts dates to "YYYY-MM-DD" strings; exclude_none drops fields the caller did not send.
        return service.material_readiness(p, body.model_dump(mode="json", exclude_none=True))

    # ===== FUNCTION: create_app.warehouse_balancing() =====
    # ID: F0127 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:128-130
    # ROLE: Three-warehouse balancing for one SKU: days of cover, donor surplus, lanes, non-transferable batches.
    # INPUTS:
    #   body: s.WarehouseBalancingRequest -> {"sku", optional "target_warehouse"}.
    #   p: Principal                      -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (kind "warehouse_balancing": positions, ranked options, proposed stock_transfer).
    # CALLED BY:
    #   <- F0671 _balancing() (http_request)
    #   <- F0836 test_scenario_2_three_warehouse_balancing() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0855 test_malformed_and_injected_tool_arguments() (http_request)
    #   <- F0857 test_roles_are_enforced_server_side() (http_request)
    #   <- F0860 test_concurrent_reviews_cannot_both_win() (http_request)
    #   <- Flowise Custom Tool · optimize_warehouse_transfer (http_request)
    #   <- Logistics-Agentflow · 4 · Calculate with SAP data (http_request)
    #   <- Warehouse-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0181 WarehouseBalancingRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0327 Service.warehouse_balancing() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0181 WarehouseBalancingRequest (validates_input)
    @app.post("/api/v1/optimizer/warehouse-balancing", tags=["optimizer"])
    def warehouse_balancing(body: s.WarehouseBalancingRequest, p: Principal = Depends(reader)) -> dict:
        return service.warehouse_balancing(p, body.model_dump(exclude_none=True))

    # ===== FUNCTION: create_app.replenishment() =====
    # ID: F0128 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:132-134
    # ROLE: Replenishment: for a product -> warehouse balancing; for a material (+ quantity) -> ranked approved suppliers.
    # INPUTS:
    #   body: s.ReplenishmentRequest -> {"item_id", optional "location", "quantity", "need_date"}.
    #   p: Principal                 -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (kind "replenishment" or "warehouse_balancing").
    # CALLED BY:
    #   <- F0670 calc_procurement() (http_request)
    #   <- F0674 calc_inventory() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- Flowise Custom Tool · calculate_stock_cover (http_request)
    #   <- Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data (http_request)
    #   <- Procurement-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0182 ReplenishmentRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0328 Service.replenishment() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0182 ReplenishmentRequest (validates_input)
    @app.post("/api/v1/optimizer/replenishment", tags=["optimizer"])
    def replenishment(body: s.ReplenishmentRequest, p: Principal = Depends(reader)) -> dict:
        return service.replenishment(p, body.model_dump(mode="json", exclude_none=True))

    # ===== FUNCTION: create_app.forecast_demand() =====
    # ID: F0129 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:136-138
    # ROLE: Baseline daily demand forecast (28-day mean x weekday index) with a 14-day back-test (WAPE vs naive).
    # INPUTS:
    #   body: s.DemandForecastRequest -> {"sku", "warehouse", "horizon_days" 1-90 (default 14)}.
    #   p: Principal                  -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (kind "demand_forecast": forecast[], total, backtest).
    # CALLED BY:
    #   <- F0674 calc_inventory() (http_request)
    #   <- F0843 test_demand_forecast_has_backtest_and_feeds_metrics() (http_request)
    #   <- F0855 test_malformed_and_injected_tool_arguments() (http_request)
    #   <- F0856 test_unknown_calculation_and_no_action_calculation() (http_request)
    #   <- Flowise Custom Tool · forecast_demand (http_request)
    #   <- Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0183 DemandForecastRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0330 Service.forecast_demand() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0183 DemandForecastRequest (validates_input)
    @app.post("/api/v1/forecast/demand", tags=["forecast"])
    def forecast_demand(body: s.DemandForecastRequest, p: Principal = Depends(reader)) -> dict:
        # No exclude_none here: horizon_days always has a value (default 14).
        return service.forecast_demand(p, body.model_dump())

    # ===== FUNCTION: create_app.forecast_lead_time() =====
    # ID: F0130 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:140-142
    # ROLE: Supplier lead time from goods receipts (mean, p90, on-time rate) or from the promoted ML model.
    # INPUTS:
    #   body: s.LeadTimeRequest -> {"supplier_id", optional "material_id", "quantity"}.
    #   p: Principal            -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (kind "lead_time_estimate": estimate, predicted_lead_time_days, basis, model_version).
    # CALLED BY:
    #   <- F0670 calc_procurement() (http_request)
    #   <- F0842 test_reconcile_requires_executed_recommendation() (http_request)
    #   <- Flowise Custom Tool · get_supplier_reliability (http_request)
    #   <- Procurement-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0184 LeadTimeRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0332 Service.lead_time() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0184 LeadTimeRequest (validates_input)
    @app.post("/api/v1/forecast/lead-time", tags=["forecast"])
    def forecast_lead_time(body: s.LeadTimeRequest, p: Principal = Depends(reader)) -> dict:
        return service.lead_time(p, body.model_dump(exclude_none=True))

    # ===== FUNCTION: create_app.quality_check() =====
    # ID: F0131 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:144-146
    # ROLE: Quality check of stock: usable vs excluded batches (with reasons), expiry risks, FEFO order.
    # INPUTS:
    #   body: s.QualityCheckRequest -> {"item_id", optional "location", "horizon_days" (default 90)}.
    #   p: Principal                -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> stored calculation (kind "quality_check").
    # CALLED BY:
    #   <- F0675 calc_quality() (http_request)
    #   <- F0837 test_scenario_3_expiry_and_quality_protection() (http_request)
    #   <- Flowise Custom Tool · check_batch_quality (http_request)
    #   <- Quality-Agentflow · 4 · Calculate with SAP data (http_request)
    # CALLS:
    #   -> F0185 QualityCheckRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0329 Service.quality_check() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0185 QualityCheckRequest (validates_input)
    @app.post("/api/v1/quality/check-stock", tags=["quality"])
    def quality_check(body: s.QualityCheckRequest, p: Principal = Depends(reader)) -> dict:
        return service.quality_check(p, body.model_dump(exclude_none=True))

    # ===== FUNCTION: create_app.calculation() =====
    # ID: F0132 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:148-150
    # ROLE: Read back a stored calculation by id (used by the supervisor "Save recommendation" step to verify a CALC id).
    # INPUTS:
    #   calculation_id: str -> path parameter, e.g. CALC-4DC2A103412B.
    #   p: Principal        -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> the stored calculation body (404 if it belongs to another tenant or does not exist).
    # CALLED BY:
    #   <- F0683 save() (http_request)
    #   <- F0519 check_facts() (http_request)
    #   <- F0790 calculation_of() (http_request)
    #   <- F0808 calc_of() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0315 Service.calculation() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/calculations/{calculation_id}", tags=["optimizer"])
    def calculation(calculation_id: str, p: Principal = Depends(reader)) -> dict:
        return service.calculation(p, calculation_id)

    # ------------------------------------------------------------------ RAG
    # ===== FUNCTION: create_app.rag_search() =====
    # ID: F0133 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:153-157
    # ROLE: Governed policy search: tenant-, role- and validity-filtered retrieval with citations and injection flags.
    # INPUTS:
    #   body: s.RagSearchRequest -> {"query" 2-1000 chars, "top_k" 1-10 (default 4)}.
    #   p: Principal             -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"query", "tenant", "results": [{text, score, flags, citation}], "note", "embedding_model"}.
    # CALLED BY:
    #   <- F0481 ApiBackend.search_knowledge() (http_request)
    #   <- F0017 create_app() (http_request)
    #   <- F0076 create_app.rag_search() (http_request)
    #   <- F0077 create_app.rag_search_get() (http_request)
    #   <- F0629 search_supply_chain_policy() (http_request)
    #   <- F0678 policy() (http_request)
    #   <- F0890 Smoke.rag() (http_request)
    #   <- F0844 test_rag_is_tenant_scoped_cited_and_flags_injection() (http_request)
    #   <- F1937 test_candidate_index_is_separate_and_active_search_is_unchanged() (http_request)
    #   <- F1939 test_unauthorized_tenant_never_sees_other_documents() (http_request)
    #   <- F1944 test_publish_needs_director_benchmark_and_confirm_then_rollback() (http_request)
    #   <- F0868 test_rag_search_and_manager_only_ingest() (http_request)
    # CALLS:
    #   -> F0186 RagSearchRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0766 KnowledgeBase.search() (calls)
    #   -> F0115 create_app.biz_date() (calls)
    #   -> F0076 create_app.rag_search() (http_request)
    #   -> F0077 create_app.rag_search_get() (http_request)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0186 RagSearchRequest (validates_input)
    @app.post("/api/v1/rag/search", tags=["rag"])
    def rag_search(body: s.RagSearchRequest, p: Principal = Depends(reader)) -> dict:
        # 503 Service Unavailable when the RAG feature switch is off.
        if not settings.rag_enabled:
            raise HTTPException(status_code=503, detail="RAG is disabled (RAG_ENABLED=false)")
        # biz_date(p): documents are only valid between valid_from and valid_to on the SAP business date.
        return kb.search(p.tenant_id, p.roles, body.query, body.top_k, biz_date(p))

    # ===== FUNCTION: create_app.rag_documents() =====
    # ID: F0134 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:159-162
    # ROLE: List the ingested documents of the caller's tenant and the last ingestion report.
    # INPUTS:
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"documents": [rag_documents rows], "last_ingestion": {ingested, skipped, rejected}}.
    # CALLED BY:
    #   <- F0017 create_app() (http_request)
    #   <- F0081 create_app.rag_add() (http_request)
    #   <- F0868 test_rag_search_and_manager_only_ingest() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0421 Database.query() (calls)
    #   -> F0081 create_app.rag_add() (http_request)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/rag/documents", tags=["rag"])
    def rag_documents(p: Principal = Depends(reader)) -> dict:
        # SQL with a "?" placeholder: the tenant id is passed as a parameter (never concatenated) -> no SQL injection.
        return {"documents": db.query("select doc_id, version, title, category, valid_from, valid_to, flags, source_path from rag_documents where tenant_id=?", (p.tenant_id,)),
                "last_ingestion": ingest_report}

    # ------------------------------------------------------------------ RAG tuning console (administrators)
    rag_tuning_api.register(app, db=db, kb=kb, security=security, settings=settings, principal_dep=principal, biz_date=biz_date)

    # ------------------------------------------------------------------ decisions
    # ===== FUNCTION: create_app.create_decision() =====
    # ID: F0135 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:168-171
    # ROLE: Create a recommendation (status pending_review) FROM a stored calculation; quantities are copied server-side.
    # INPUTS:
    #   body: s.DecisionCreateRequest -> {"calculation_id", optional "title", "idempotency_key", "po_id"}.
    #   p: Principal                  -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> the recommendation with review_authority, reviews, sap_execution, outcomes (status 201 Created).
    # status_code=201 overrides FastAPI's default 200 for a successful POST that creates a resource.
    # CALLED BY:
    #   <- F0683 save() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0855 test_malformed_and_injected_tool_arguments() (http_request)
    #   <- F0856 test_unknown_calculation_and_no_action_calculation() (http_request)
    #   <- F0857 test_roles_are_enforced_server_side() (http_request)
    #   <- F0860 test_concurrent_reviews_cannot_both_win() (http_request)
    #   <- Flowise Custom Tool · save_recommendation (http_request)
    #   <- Supervisor-Agentflow · 7 · Save recommendation (http_request)
    # CALLS:
    #   -> F0187 DecisionCreateRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0333 Service.create_decision() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0187 DecisionCreateRequest (validates_input)
    @app.post("/api/v1/decisions", tags=["decisions"], status_code=201)
    def create_decision(body: s.DecisionCreateRequest, p: Principal = Depends(reader)) -> dict:
        # AUTHORIZATION: only the agent service or a planner may create recommendations (403 otherwise).
        security.require(p, {"agent_service", "planner"}, "Creating a recommendation")
        return service.create_decision(p, body.model_dump(exclude_none=True))

    # ===== FUNCTION: create_app.list_decisions() =====
    # ID: F0136 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:173-175
    # ROLE: List recommendations of the tenant, optionally by status.
    # INPUTS:
    #   status: str | None -> query ?status=pending_review (regex ^[a-z_]+$).
    #   p: Principal       -> injected by Depends(reader).
    # OUTPUT:
    #   list[dict] -> recommendations, newest first.
    # CALLED BY:
    #   <- F0683 save() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0855 test_malformed_and_injected_tool_arguments() (http_request)
    #   <- F0856 test_unknown_calculation_and_no_action_calculation() (http_request)
    #   <- F0857 test_roles_are_enforced_server_side() (http_request)
    #   <- F0860 test_concurrent_reviews_cannot_both_win() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0336 Service.list_decisions() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/decisions", tags=["decisions"])
    def list_decisions(status: str | None = Query(default=None, pattern=r"^[a-z_]+$"), p: Principal = Depends(reader)) -> list[dict]:
        return service.list_decisions(p, status)

    # ===== FUNCTION: create_app.get_decision() =====
    # ID: F0137 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:177-179
    # ROLE: Read one recommendation with its verified human reviews, SAP execution record and observed outcomes.
    # INPUTS:
    #   rec_id: str  -> path parameter REC-...
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> recommendation + reviews + sap_execution + outcomes + verified_review flag.
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0684 verify() (http_request)
    #   <- F0685 withdraw() (http_request)
    #   <- F0520 approval_cycle() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0797 test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval() (http_request)
    #   <- F0798 test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager() (http_request)
    #   <- F0799 test_scenario_3_quality_exclusions_and_reject_withdraws() (http_request)
    #   <- F0800 test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time() (http_request)
    #   <- F0801 test_learning_reports_the_verified_plus_four_day_error() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0335 Service.get_decision() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/decisions/{rec_id}", tags=["decisions"])
    def get_decision(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.get_decision(p, rec_id)

    # ===== FUNCTION: create_app.review() =====
    # ID: F0138 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:181-183
    # ROLE: THE human approval: an authorised human reviewer records approve / reject / modify / defer.
    # INPUTS:
    #   rec_id: str             -> path parameter REC-...
    #   body: s.ReviewRequest   -> {"decision", "explanation", optional "modifications"}.
    #   p: Principal            -> Depends(principal) only: the per-domain reviewer check happens in Service.review.
    # OUTPUT:
    #   dict -> updated recommendation + {"sap_written": False, "next_step": ...}.
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0684 verify() (http_request)
    #   <- F0685 withdraw() (http_request)
    #   <- F0520 approval_cycle() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0797 test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval() (http_request)
    #   <- F0798 test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager() (http_request)
    #   <- F0799 test_scenario_3_quality_exclusions_and_reject_withdraws() (http_request)
    #   <- F0800 test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time() (http_request)
    #   <- F0810 test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api() (http_request)
    # CALLS:
    #   -> F0188 ReviewRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0337 Service.review() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    #   -> F0188 ReviewRequest (validates_input)
    @app.post("/api/v1/decisions/{rec_id}/review", tags=["decisions"])
    def review(rec_id: str, body: s.ReviewRequest, p: Principal = Depends(principal)) -> dict:
        return service.review(p, rec_id, body.model_dump(exclude_none=True))

    # ===== FUNCTION: create_app.withdraw() =====
    # ID: F0139 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:185-187
    # ROLE: Withdraw a pending recommendation (creator or director only). Used by the supervisor "Reject" branch.
    # INPUTS:
    #   rec_id: str  -> path parameter REC-...
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> the recommendation with status "withdrawn".
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0684 verify() (http_request)
    #   <- F0685 withdraw() (http_request)
    #   <- F0520 approval_cycle() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0797 test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval() (http_request)
    #   <- F0798 test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager() (http_request)
    #   <- F0799 test_scenario_3_quality_exclusions_and_reject_withdraws() (http_request)
    #   <- F0800 test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time() (http_request)
    #   <- F0810 test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0339 Service.withdraw() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.post("/api/v1/decisions/{rec_id}/withdraw", tags=["decisions"])
    def withdraw(rec_id: str, p: Principal = Depends(reader)) -> dict:
        return service.withdraw(p, rec_id)

    # ===== FUNCTION: create_app.sap_execution() =====
    # ID: F0140 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:189-191
    # ROLE: Record that an authorised SAP user executed an approved recommendation manually in SAP (document number).
    # INPUTS:
    #   rec_id: str                  -> path parameter REC-...
    #   body: s.SapExecutionRequest  -> {"sap_document", "doc_type", "executed_at"}.
    #   p: Principal                 -> Depends(principal); Service checks the sap_executor / director role.
    # OUTPUT:
    #   dict -> the recommendation with status "executed".
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0684 verify() (http_request)
    #   <- F0685 withdraw() (http_request)
    #   <- F0520 approval_cycle() (http_request)
    #   <- F0838 test_decision_lifecycle_requires_an_authorised_human() (http_request)
    #   <- F0839 test_defer_then_review_and_withdraw() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0797 test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval() (http_request)
    #   <- F0798 test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager() (http_request)
    #   <- F0799 test_scenario_3_quality_exclusions_and_reject_withdraws() (http_request)
    #   <- F0800 test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time() (http_request)
    #   <- F0810 test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api() (http_request)
    # CALLS:
    #   -> F0189 SapExecutionRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0340 Service.record_sap_execution() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    #   -> F0189 SapExecutionRequest (validates_input)
    @app.post("/api/v1/decisions/{rec_id}/sap-execution", tags=["decisions"])
    def sap_execution(rec_id: str, body: s.SapExecutionRequest, p: Principal = Depends(principal)) -> dict:
        return service.record_sap_execution(p, rec_id, body.model_dump(mode="json"))

    # ------------------------------------------------------------------ learning
    # ===== FUNCTION: create_app.reconcile() =====
    # ID: F0141 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:194-196
    # ROLE: Compare an executed recommendation's prediction with the SAP goods receipt; create the learning record.
    # INPUTS:
    #   body: s.ReconcileRequest -> {"recommendation_id": "REC-..."}.
    #   p: Principal             -> Depends(principal); Service checks the allowed roles.
    # OUTPUT:
    #   dict -> outcome (verified / incomplete / pending / missing / already_reconciled) with the prediction error.
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0840 test_outcome_learning_loop_and_model_governance() (http_request)
    #   <- F0841 test_purchase_request_carries_a_reconcilable_lead_time_prediction() (http_request)
    #   <- F0842 test_reconcile_requires_executed_recommendation() (http_request)
    #   <- F0858 test_incomplete_outcome_is_not_used_for_training() (http_request)
    #   <- F0859 test_pending_outcome_is_reported_not_invented() (http_request)
    #   <- Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data (http_request)
    # CALLS:
    #   -> F0190 ReconcileRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0341 Service.reconcile() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    #   -> F0171 ReconcileRequest (validates_input)
    @app.post("/api/v1/outcomes/reconcile", tags=["learning"])
    def reconcile(body: s.ReconcileRequest, p: Principal = Depends(principal)) -> dict:
        return service.reconcile(p, body.recommendation_id)

    # ===== FUNCTION: create_app.learning_metrics() =====
    # ID: F0142 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:198-200
    # ROLE: Learning metrics computed ONLY from verified outcomes (lead-time MAE, WAPE, acceptance / execution rates, models).
    # INPUTS:
    #   p: Principal -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> metric objects {"value", ...} + models + learning_records.
    # CALLED BY:
    #   <- F0676 calc_learning() (http_request)
    #   <- F0840 test_outcome_learning_loop_and_model_governance() (http_request)
    #   <- F0843 test_demand_forecast_has_backtest_and_feeds_metrics() (http_request)
    #   <- F0801 test_learning_reports_the_verified_plus_four_day_error() (http_request)
    #   <- Flowise Custom Tool · get_verified_outcomes (http_request)
    #   <- Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0343 Service.learning_metrics() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    @app.get("/api/v1/learning/metrics", tags=["learning"])
    def learning_metrics(p: Principal = Depends(reader)) -> dict:
        return service.learning_metrics(p)

    # ===== FUNCTION: create_app.train() =====
    # ID: F0143 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:202-207
    # ROLE: Train a candidate supplier lead-time model (MLOps engineer only) and audit it.
    # INPUTS:
    #   p: Principal -> Depends(principal) + explicit role check below.
    # OUTPUT:
    #   dict -> model_version_id, version, status "candidate", metrics, baselines, beats_best_baseline.
    # CALLED BY:
    #   <- F0840 test_outcome_learning_loop_and_model_governance() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0534 train_lead_time_model() (calls)
    #   -> F0779 Security.audit() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    @app.post("/api/v1/learning/train-lead-time-model", tags=["learning"])
    def train(p: Principal = Depends(principal)) -> dict:
        security.require(p, {"mlops_engineer"}, "Training a model")
        result = learning.train_lead_time_model(db, p.tenant_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.trained", {"model_version_id": result["model_version_id"]})
        return result

    # ===== FUNCTION: create_app.promote() =====
    # ID: F0144 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:209-214
    # ROLE: Manual promotion gate: the supply-chain director promotes a candidate model (only if it beats the best baseline).
    # INPUTS:
    #   model_id: str -> path parameter MV-...
    #   p: Principal  -> Depends(principal) + director role check.
    # OUTPUT:
    #   dict -> the promoted model_versions row + {"gate": "passed: ..."} (409 if the gate fails).
    # CALLED BY:
    #   <- F0840 test_outcome_learning_loop_and_model_governance() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0535 promote() (calls)
    #   -> F0779 Security.audit() (calls)
    #   -> F0113 create_app.principal() (depends_on)
    @app.post("/api/v1/learning/models/{model_id}/promote", tags=["learning"])
    def promote(model_id: str, p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Promoting a model (manual gate)")
        result = learning.promote(db, p.tenant_id, model_id, p.user_id)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.promoted", {"model_version_id": model_id})
        return result

    # ===== FUNCTION: create_app.retraining() =====
    # ID: F0145 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:216-220
    # ROLE: File a retraining request (evidence = verified learning records); training itself stays a separate, manual step.
    # INPUTS:
    #   body: s.RetrainingRequest -> {"reason": 10-1000 chars}.
    #   p: Principal              -> injected by Depends(reader).
    # OUTPUT:
    #   dict -> {"id": "RR-...", "status": "pending_human_approval", "evidence", "note"} (201 Created).
    # CALLED BY:
    #   <- F0840 test_outcome_learning_loop_and_model_governance() (http_request)
    # CALLS:
    #   -> F0191 RetrainingRequest (references)
    #   -> F0772 Principal (references)
    #   -> F0114 create_app.reader() (references)
    #   -> F0537 retraining_request() (calls)
    #   -> F0779 Security.audit() (calls)
    #   -> F0114 create_app.reader() (depends_on)
    #   -> F0191 RetrainingRequest (validates_input)
    @app.post("/api/v1/learning/retraining-requests", tags=["learning"], status_code=201)
    def retraining(body: s.RetrainingRequest, p: Principal = Depends(reader)) -> dict:
        result = learning.retraining_request(db, p.tenant_id, p.user_id, body.reason)
        security.audit(p.tenant_id, p.user_id, sorted(p.roles), "model.retraining_requested", {"id": result["id"]})
        return result

    # ===== FUNCTION: create_app.audit() =====
    # ID: F0146 · route · used
    # ORIGINAL FILE: backend/scinsight/app.py:222-226
    # ROLE: Read the audit log of the tenant and verify the whole hash chain (director only).
    # INPUTS:
    #   limit: int   -> query ?limit= 1..500 (default 50); Query(ge=, le=) returns 422 outside the range.
    #   p: Principal -> Depends(principal) + director role check.
    # OUTPUT:
    #   dict -> {"chain_valid": bool, "events": [newest audit rows first]}.
    # CALLED BY:
    #   <- F0017 create_app() (http_request)
    #   <- F0101 create_app.audit() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F1944 test_publish_needs_director_benchmark_and_confirm_then_rollback() (http_request)
    #   <- F0848 test_forged_tenant_is_rejected_and_audited() (http_request)
    #   <- F0862 test_sap_odata_reads_and_blocks_writes() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0874 test_deep_agent_harness_settings_are_governed() (http_request)
    #   <- F0878 test_tenant_scoped_authorization() (http_request)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0113 create_app.principal() (references)
    #   -> F0777 Security.require() (calls)
    #   -> F0781 Security.verify_chain() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0101 create_app.audit() (http_request)
    #   -> F0113 create_app.principal() (depends_on)
    @app.get("/api/v1/audit", tags=["learning"])
    def audit(limit: int = Query(default=50, ge=1, le=500), p: Principal = Depends(principal)) -> dict:
        security.require(p, {"supply_chain_director"}, "Reading the audit log")
        return {"chain_valid": security.verify_chain(),
                "events": db.query("select * from audit_events where tenant_id=? order by id desc limit ?", (p.tenant_id, limit))}

    # All routes are registered on `app`: hand the application back to uvicorn / the tests.
    return app
# Entry point: `uvicorn backend.scinsight.app:create_app --factory --port 8100` (tests call create_app() with their own settings).
