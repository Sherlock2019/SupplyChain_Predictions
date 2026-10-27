# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/main.py
# What this module is: the SPARC / Aurelia FastAPI gateway (port 8000): one create_app() factory registers middleware
# (correlation id, tenant, metrics), dependencies (principal -> reader / manager), the SAP OData facade (read-only, writes -> 405),
# deterministic analyses, role views, RAG, LangGraph / Deep Agent / Flowise proxies, recommendations with human decision and
# sandbox execution, outcomes, audit, and the short POC-contract routes. All routes are declared on `app` (no APIRouter).
# Header blocks above each function were added; ID / ORIGINAL FILE lines / CALLED BY / CALLS are filled by the generator.
# Only comment lines were added (AST-verified).
# ======================================================================================================
from __future__ import annotations

import asyncio
import base64
import os
import re
import struct
import time
import uuid
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import httpx
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.app.auth import ApiKeyAuth, Principal
from backend.app.code_editor import CodeEditor
from backend.app.config import ROOT, Settings, get_settings
from backend.app.dashboards import PERSONAS
from backend.app.erp.emulator import router as erp_emulator
from backend.app.erp.routes import register as register_erp
from backend.app.erp.service import ErpService
from backend.app.insights import WATCH_KINDS
from backend.app.llm import llm_health
from backend.app.moat import MoatEngine
from backend.app.observability import ANALYSES, DENIALS, LATENCY, REQUESTS
from backend.app.rag import create_rag
from backend.app.roles import ROLES
from backend.app.runner import GraphRunner
from backend.app.schemas import (
    DEEP_SUBAGENTS,
    DEEP_TOOLS,
    BusinessWorkflowRequest,
    ChatRequest,
    CodeUpdateRequest,
    ConsentRequest,
    DecisionRequest,
    DeepAgentHarness,
    EmbeddingsRequest,
    FactoryReadinessRequest,
    FlowisePredictRequest,
    ForecastRequest,
    LogisticsRequest,
    OutcomeRequest,
    QualityRequest,
    RagDocument,
    RagQuery,
    RecommendationFromTextRequest,
    RecommendationRequest,
    ReconcileRequest,
    ResumeRequest,
    SalesOrderRequest,
    StockBalanceRequest,
    StocktakeRequest,
    SupplierLeadTimeRequest,
    SupplierResearchRequest,
    SupplierRiskRequest,
    WatchRequest,
    WhatIfRequest,
)
from backend.app.store import Store
from backend.app.tenants import DEFAULT_TENANT, TenantProxy, TenantRegistry

FLOW_NAMES = {
    "chatflow": "Aurelia Supply Chain Copilot - Chatflow",
    "agentflow": "Aurelia Supply Chain Supervisor - AgentFlow V2",
}


# ===== FUNCTION: _expectation() =====
# ID: F0016 · function · used
# ORIGINAL FILE: backend/app/main.py:75-82
# ROLE: Plain-language expected result of one executed action (what the outcome check will look for in SAP).
# INPUTS:
#   action
# OUTPUT:
#   str
# CALLED BY:
#   <- F0059 create_app.record_outcome() (calls)
#   <- F0099 create_app.execute() (calls)
#   <- F0110 create_app.poc_reconcile() (calls)
# CALLS:
#   (none found)
def _expectation(action: dict) -> str:
    """Plain-language expected result of one executed action (what the outcome check will look for in SAP)."""
    kind = action.get("action", "action")
    if kind == "stock_transfer":
        return f"{action.get('quantity', 0):,.0f} {action.get('material', '')} from {action.get('from')} to {action.get('to')} by {action.get('arrives', 'the planned date')}"
    if kind == "expedite_purchase_order":
        return f"PO {action.get('po', '')} delivered by {action.get('new_delivery_date') or action.get('need_by', 'the need date')}"
    return kind.replace("_", " ") + (f" for {action['material']}" if action.get("material") else "")


# ===== FUNCTION: create_app() =====
# ID: F0017 · function · used
# ORIGINAL FILE: backend/app/main.py:85-1016
# ROLE: Application factory of the SPARC / Aurelia gateway: builds the store, tenant registry + proxies, moat, RAG, auth and graph runner, then registers middleware, dependencies and ~95 routes as closures.
# INPUTS:
#   settings, store, runner, scinsight_router
# OUTPUT:
#   FastAPI
# CALLED BY:
#   <- F0905 client() (calls)
#   <- F0872 test_demo_session_disabled_by_default_and_enabled_for_local_demo() (calls)
#   <- F2176 app() (calls)
#   <- F2187 test_activation_survives_restart() (calls)
#   <- F1985 fused() (calls)
# CALLS:
#   -> F0001 Settings (references)
#   -> F0354 Store (references)
#   -> F0621 GraphRunner (references)
#   -> F0008 get_settings() (calls)
#   -> F1993 create_router() (calls)
#   -> F0354 Store (calls)
#   -> F0391 TenantRegistry (calls)
#   -> F0393 TenantRegistry.get() (calls)
#   -> F0398 TenantProxy (calls)
#   -> F0250 MoatEngine (calls)
#   -> F0756 create_rag() (calls)
#   -> F0768 ApiKeyAuth (calls)
def create_app(settings: Settings | None = None, store: Store | None = None, runner: GraphRunner | None = None,
               scinsight_router: APIRouter | None = None) -> FastAPI:
    settings = settings or get_settings()
    # THE FastAPI app of the backend. The SCInsight API (backend of the Flowise chatflow and agentflows) is one of its routers,
    # included below at /scinsight with its own keys, roles, database and audit chain. Built from SCI_* settings unless a test
    # passes its own router.
    if scinsight_router is None and settings.scinsight_enabled:
        from backend.scinsight.app import create_router as create_scinsight_router
        scinsight_router = create_scinsight_router()
    store = store or Store(settings.database_url)
    # One SAP snapshot + engine stack per industry/customer; the request's X-Tenant header selects it.
    tenants = TenantRegistry(settings.data_file, store)
    tenants.get(DEFAULT_TENANT)  # validate the default snapshot at startup
    sap = TenantProxy(tenants, "sap")
    engine = TenantProxy(tenants, "engine")
    insight_engine = TenantProxy(tenants, "insights")
    dashboards = TenantProxy(tenants, "dashboards")
    roles = TenantProxy(tenants, "roles")
    moat = MoatEngine(tenants, store)
    rag = create_rag(settings.rag_backend, settings.postgres_url, settings.knowledge_dir, settings.embedding_backend, settings.embedding_model)
    auth = ApiKeyAuth(settings)
    runner = runner or GraphRunner(settings)
    flow_ids: dict[str, str] = {"chatflow": settings.flowise_chatflow_id, "agentflow": settings.flowise_agentflow_id}

    app = FastAPI(
        title="SPARC — Smart Supply Chain Performer Copilot",
        version="1.0.0",
        description="Read-only SAP data, deterministic analytics, governed LangGraph / Deep Agents / Flowise workflows, and human approval.",
    )
    app.state.settings, app.state.sap, app.state.engine, app.state.store, app.state.rag, app.state.runner = settings, sap, engine, store, rag, runner
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env in ("development", "test") else [settings.public_base_url],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key", "X-Correlation-ID", "X-Tenant"],
    )

    # ===== FUNCTION: create_app.request_context() =====
    # ID: F0018 · nested · used
    # ORIGINAL FILE: backend/app/main.py:123-141
    # ROLE: HTTP middleware: correlation id, active tenant (X-Tenant or ?tenant=), Prometheus request count + latency.
    # INPUTS:
    #   request, call_next
    # OUTPUT:
    #   see code
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0395 TenantRegistry.activate() (calls)
    #   -> F0391 TenantRegistry (references)
    #   -> F0396 TenantRegistry.deactivate() (calls)
    @app.middleware("http")
    async def request_context(request: Request, call_next):
        started = time.perf_counter()
        correlation_id = (request.headers.get("X-Correlation-ID") or str(uuid.uuid4()))[:128]
        request.state.correlation_id = correlation_id
        token = TenantRegistry.activate(request.headers.get("X-Tenant") or request.query_params.get("tenant"))
        try:
            response = await call_next(request)
        except Exception:
            REQUESTS.labels(request.method, "unhandled", "500").inc()
            raise
        finally:
            TenantRegistry.deactivate(token)
        route = request.scope.get("route")
        path = getattr(route, "path", "static")
        response.headers["X-Correlation-ID"] = correlation_id
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
        return response

    # ===== FUNCTION: create_app.principal() =====
    # ID: F0019 · nested · used
    # ORIGINAL FILE: backend/app/main.py:143-156
    # ROLE: Dependency: authenticate X-API-Key (401) and enforce tenant scope (403); every denial is counted and audited.
    # INPUTS:
    #   request, x_api_key
    # OUTPUT:
    #   Principal
    # CALLED BY:
    #   <- F0020 create_app.manager() (references)
    #   <- F0020 create_app.manager() (depends_on)
    #   <- F0021 create_app.reader() (references)
    #   <- F0021 create_app.reader() (depends_on)
    #   <- F0078 create_app.embeddings() (calls)
    # CALLS:
    #   -> F0770 ApiKeyAuth.authenticate() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0005 Settings.tenants_for() (calls)
    #   -> F0397 TenantRegistry.current_id() (calls)
    #   -> F0391 TenantRegistry (references)
    #   -> F0767 Principal (references)
    def principal(request: Request, x_api_key: str | None = Header(default=None)) -> Principal:
        try:
            who = auth.authenticate(request, x_api_key)
        except HTTPException:
            DENIALS.labels("invalid_key").inc()
            store.audit("anonymous", "none", "auth.denied", {"path": request.url.path}, request.state.correlation_id)
            raise
        allowed = settings.tenants_for(who.identity)  # tenant-scoped authorization
        tenant = TenantRegistry.current_id()
        if allowed is not None and tenant not in allowed:
            DENIALS.labels("tenant").inc()
            store.audit(who.identity, who.role, "auth.tenant_forbidden", {"path": request.url.path, "tenant": tenant}, request.state.correlation_id)
            raise HTTPException(status_code=403, detail=f"{who.identity} is not authorized for tenant {tenant}")
        return who

    # ===== FUNCTION: create_app.manager() =====
    # ID: F0020 · nested · used
    # ORIGINAL FILE: backend/app/main.py:158-164
    # ROLE: Dependency: authenticated caller with the manager role (403 otherwise, audited).
    # INPUTS:
    #   request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Principal
    # CALLED BY:
    #   <- F0017 create_app() (references)
    #   <- F0029 create_app.demo_session() (references)
    #   <- F0058 create_app.moat_consent() (references)
    #   <- F0058 create_app.moat_consent() (depends_on)
    #   <- F0059 create_app.record_outcome() (references)
    #   <- F0059 create_app.record_outcome() (depends_on)
    #   <- F0081 create_app.rag_add() (references)
    #   <- F0081 create_app.rag_add() (depends_on)
    #   <- F0987 create_app.code_update() (references)
    #   <- F0987 create_app.code_update() (depends_on)
    #   <- F0091 create_app.set_deep_harness() (references)
    #   <- F0091 create_app.set_deep_harness() (depends_on)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0019 create_app.principal() (references)
    #   -> F0771 ApiKeyAuth.require() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0019 create_app.principal() (depends_on)
    def manager(request: Request, who: Principal = Depends(principal)) -> Principal:
        try:
            return auth.require(who, "manager")
        except HTTPException:
            DENIALS.labels("role").inc()
            store.audit(who.identity, who.role, "auth.forbidden", {"path": request.url.path}, request.state.correlation_id)
            raise

    # ===== FUNCTION: create_app.reader() =====
    # ID: F0021 · nested · used
    # ORIGINAL FILE: backend/app/main.py:166-167
    # ROLE: Dependency: authenticated caller with the assistant or manager role.
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Principal
    # CALLED BY:
    #   <- F0017 create_app() (references)
    #   <- F0031 create_app.status() (references)
    #   <- F0031 create_app.status() (depends_on)
    #   <- F0033 create_app.snapshot() (references)
    #   <- F0033 create_app.snapshot() (depends_on)
    #   <- F0035 create_app.network_map() (references)
    #   <- F0035 create_app.network_map() (depends_on)
    #   <- F0036 create_app.sap_metadata() (references)
    #   <- F0036 create_app.sap_metadata() (depends_on)
    #   <- F0037 create_app.sap_sandbox_documents() (references)
    #   <- F0037 create_app.sap_sandbox_documents() (depends_on)
    #   <- F0038 create_app.sap_odata() (references)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0019 create_app.principal() (references)
    #   -> F0771 ApiKeyAuth.require() (calls)
    #   -> F0019 create_app.principal() (depends_on)
    def reader(who: Principal = Depends(principal)) -> Principal:
        return auth.require(who, "assistant", "manager")

    # ===== FUNCTION: create_app.watch_owner() =====
    # ID: F0022 · nested · used
    # ORIGINAL FILE: backend/app/main.py:169-170
    # ROLE: Owner key of a watch: identity@tenant.
    # INPUTS:
    #   who
    # OUTPUT:
    #   str
    # CALLED BY:
    #   <- F0068 create_app.list_watches() (calls)
    #   <- F0069 create_app.create_watch() (calls)
    #   <- F0070 create_app.delete_watch() (calls)
    #   <- F0071 create_app.evaluate_watches() (calls)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0397 TenantRegistry.current_id() (calls)
    #   -> F0391 TenantRegistry (references)
    def watch_owner(who: Principal) -> str:
        return f"{who.identity}@{TenantRegistry.current_id()}"  # watches belong to a user within one customer

    # ===== FUNCTION: create_app.save() =====
    # ID: F0023 · nested · used
    # ORIGINAL FILE: backend/app/main.py:172-182
    # ROLE: Store an analysis (AN-...), audit it, count it, and return it with snapshot provenance and read_only=True.
    # INPUTS:
    #   kind, payload, result, who, request
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0040 create_app.factory_readiness() (calls)
    #   <- F0041 create_app.stock_balance() (calls)
    #   <- F0042 create_app.demand_forecast() (calls)
    #   <- F0043 create_app.what_if() (calls)
    #   <- F0044 create_app.supplier_risk() (calls)
    #   <- F0045 create_app.quality() (calls)
    #   <- F0046 create_app.logistics() (calls)
    #   <- F0047 create_app.sales_orders() (calls)
    #   <- F0048 create_app.stocktake() (calls)
    #   <- F0104 create_app.poc_forecast_demand() (calls)
    #   <- F0105 create_app.poc_forecast_lead_time() (calls)
    #   <- F0106 create_app.poc_material_readiness() (calls)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0361 Store.save_analysis() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0358 Store.audit() (calls)
    def save(kind: str, payload: dict, result: dict, who: Principal, request: Request) -> dict:
        analysis_id = store.save_analysis(kind, payload, result, sap.snapshot["id"], who.identity)
        store.audit(
            who.identity,
            who.role,
            f"analysis.{kind}",
            {"analysis_id": analysis_id, "proposed_action_count": len(result.get("proposed_actions", []))},
            request.state.correlation_id,
        )
        ANALYSES.labels(kind).inc()
        return {"analysis_id": analysis_id, "snapshot": sap.snapshot, "read_only": True, **result}

    # ===== FUNCTION: create_app.value_error_handler() =====
    # ID: F0024 · nested · used
    # ORIGINAL FILE: backend/app/main.py:184-186
    # ROLE: Exception handler: any ValueError from the engine becomes HTTP 422 with a VALIDATION_ERROR body.
    # INPUTS:
    #   request, exc
    # OUTPUT:
    #   see code
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "correlation_id": request.state.correlation_id}})

    # ------------------------------------------------------------- platform
    # ===== FUNCTION: create_app.health() =====
    # ID: F0025 · route · used
    # ORIGINAL FILE: backend/app/main.py:189-191
    # ROLE: HTTP GET /health
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0405 SapRepository.snapshot() (references)
    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "supply-chain-copilot", "snapshot": sap.snapshot["id"], "cloud": settings.cloud_provider}

    # ===== FUNCTION: create_app.ready() =====
    # ID: F0026 · route · used
    # ORIGINAL FILE: backend/app/main.py:193-195
    # ROLE: HTTP GET /ready
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0357 Store.dialect() (references)
    #   -> F0747 MemoryRag.stats() (calls)
    #   -> F0753 PgVectorRag.stats() (calls)
    @app.get("/ready")
    def ready() -> dict:
        return {"ready": True, "sap_snapshot_valid": sap.snapshot["validated"], "store": store.dialect, "rag": rag.stats()}

    # ===== FUNCTION: create_app.metrics() =====
    # ID: F0027 · route · used
    # ORIGINAL FILE: backend/app/main.py:197-199
    # ROLE: HTTP GET /metrics
    # INPUTS:
    #   none
    # OUTPUT:
    #   Response
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # ===== FUNCTION: create_app.public_config() =====
    # ID: F0028 · route · used
    # ORIGINAL FILE: backend/app/main.py:201-229
    # ROLE: HTTP GET /api/v1/config/public — Non-secret links for the dashboard header.
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0871 test_status_and_public_config() (http_request)
    #   <- F0872 test_demo_session_disabled_by_default_and_enabled_for_local_demo() (http_request)
    # CALLS:
    #   -> F0030 create_app._public() (calls)
    #   -> F0624 GraphRunner.mode() (references)
    #   -> F0404 SapRepository.as_of() (references)
    @app.get("/api/v1/config/public")
    def public_config() -> dict:
        """Non-secret links for the dashboard header."""
        base = settings.public_base_url.rstrip("/")
        return {
            "cloud": settings.cloud_provider,
            "environment": settings.app_env,
            "api_docs": f"{base}/docs",
            "links": {
                "flowise": _public("flowise"),
                "langgraph_api": _public("langgraph"),
                "langsmith_studio": f"https://smith.langchain.com/studio/?baseUrl={_public('langgraph')}" if _public("langgraph") else "",
                "mcp": _public("mcp") + "/mcp" if _public("mcp") else "",
                "grafana": _public("grafana"),
                "langfuse": _public("langfuse"),
            },
            "graph_runtime": runner.mode,
            "llm_model": settings.qwen_model if settings.llm_enabled else None,
            "demo_auto_login": settings.demo_auto_login,
            "as_of": sap.as_of.isoformat(),
            "sap_execution_mode": settings.sap_execution_mode,
            # Direct access to both agent backends: Flowise canvases and LangGraph graphs (Studio).
            "flowise": {
                "login": os.environ.get("FLOWISE_ADMIN_EMAIL", "admin@aurelia.local"),
                "chatflow_canvas": f"{_public('flowise')}/canvas/{flow_ids['chatflow']}" if _public("flowise") and flow_ids.get("chatflow") else "",
                "agentflow_canvas": f"{_public('flowise')}/v2/agentcanvas/{flow_ids['agentflow']}" if _public("flowise") and flow_ids.get("agentflow") else "",
            },
            "langgraph": {"graphs": ["supply_chain_chat", "supply_chain_agentflow", "supply_chain_business", "supplier_deep_agent"]},
        }

    # ===== FUNCTION: create_app.demo_session() =====
    # ID: F0029 · route · used
    # ORIGINAL FILE: backend/app/main.py:231-238
    # ROLE: HTTP GET /api/v1/demo/session — Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the UI needs no login.
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0872 test_demo_session_disabled_by_default_and_enabled_for_local_demo() (http_request)
    # CALLS:
    #   -> F0020 create_app.manager() (references)
    @app.get("/api/v1/demo/session", include_in_schema=False)
    def demo_session() -> dict:
        """Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the UI needs no login."""
        if not settings.demo_auto_login:
            raise HTTPException(status_code=404, detail="Not found")
        planner = next((k for k, who in settings.assistants.items() if who == "planner"), next(iter(settings.assistants), ""))
        manager = next(iter(settings.managers), "")
        return {"planner": planner, "manager": manager}

    # ===== FUNCTION: create_app._public() =====
    # ID: F0030 · nested · used
    # ORIGINAL FILE: backend/app/main.py:240-241
    # ROLE: Public URL of a companion service from PUBLIC_<SERVICE>_URL.
    # INPUTS:
    #   service
    # OUTPUT:
    #   str
    # CALLED BY:
    #   <- F0028 create_app.public_config() (calls)
    # CALLS:
    #   (none found)
    def _public(service: str) -> str:
        return os.environ.get(f"PUBLIC_{service.upper()}_URL", "")

    # ===== FUNCTION: create_app.status() =====
    # ID: F0031 · route · used
    # ORIGINAL FILE: backend/app/main.py:243-276
    # ROLE: HTTP GET /api/v1/status
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0097 create_app.recommendations() (references)
    #   <- F0887 Smoke.platform() (http_request)
    #   <- F0871 test_status_and_public_config() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0032 create_app.status.probe() (calls)
    #   -> F0729 llm_health() (references)
    #   -> F0747 MemoryRag.stats() (calls)
    #   -> F0753 PgVectorRag.stats() (calls)
    #   -> F0357 Store.dialect() (references)
    #   -> F0389 Store.counts() (calls)
    #   -> F0359 Store.verify_chain() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0624 GraphRunner.mode() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/status")
    async def status(who: Principal = Depends(reader)) -> dict:
        del who

        # ===== FUNCTION: create_app.status.probe() =====
        # ID: F0032 · nested · used
        # ORIGINAL FILE: backend/app/main.py:247-255
        # ROLE: Probe one service URL asynchronously (up / error / down / not_configured).
        # INPUTS:
        #   name, url, headers
        # OUTPUT:
        #   tuple[str, dict]
        # CALLED BY:
        #   <- F0031 create_app.status() (calls)
        # CALLS:
        #   (none found)
        async def probe(name: str, url: str, headers: dict | None = None) -> tuple[str, dict]:
            if not url:
                return name, {"status": "not_configured"}
            try:
                async with httpx.AsyncClient(timeout=4) as client:
                    response = await client.get(url, headers=headers or {})
                return name, {"status": "up" if response.status_code < 500 else "error", "http": response.status_code}
            except Exception as exc:  # noqa: BLE001
                return name, {"status": "down", "error": str(exc)[:160]}

        probes = await asyncio.gather(
            probe("langgraph_server", f"{settings.langgraph_url.rstrip('/')}/ok" if settings.langgraph_url else ""),
            probe("flowise", f"{settings.flowise_url.rstrip('/')}/api/v1/ping" if settings.flowise_url else ""),
            probe("mcp_server", f"{settings.mcp_url.rstrip('/')}/health" if settings.mcp_url else ""),
            probe("langfuse", f"{settings.langfuse_host.rstrip('/')}/api/public/health" if settings.langfuse_host else ""),
            probe("grafana", f"{settings.grafana_url.rstrip('/')}/api/health" if settings.grafana_url else ""),
        )
        components = dict(probes)
        components["qwen_llm"] = await asyncio.to_thread(llm_health, settings)
        try:
            components["rag"] = {"status": "up", **rag.stats()}
        except Exception as exc:  # noqa: BLE001
            components["rag"] = {"status": "down", "error": str(exc)[:160]}
        try:
            components["governance_store"] = {"status": "up", "dialect": store.dialect, **store.counts(), "audit_chain_valid": store.verify_chain()}
        except Exception as exc:  # noqa: BLE001
            components["governance_store"] = {"status": "down", "error": str(exc)[:160]}
        components["sap_mock"] = {"status": "up", "snapshot": sap.snapshot["id"], "read_only": True}
        components["analytics"] = {"status": "up", "forecast": "xgboost", "optimizer": "ortools-glop"}
        return {"cloud": settings.cloud_provider, "graph_runtime": runner.mode, "components": components}

    # ----------------------------------------------------------- SAP mock
    # ===== FUNCTION: create_app.snapshot() =====
    # ID: F0033 · route · used
    # ORIGINAL FILE: backend/app/main.py:279-290
    # ROLE: HTTP GET /api/v1/snapshot
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0471 ApiBackend.snapshot() (http_request)
    #   <- F0861 test_health_is_public_but_data_requires_key() (http_request)
    #   <- F2179 snapshot_id() (http_request)
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0393 TenantRegistry.get() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0407 SapRepository.section() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/snapshot")
    def snapshot(who: Principal = Depends(reader)) -> dict:
        del who
        ctx = tenants.get()
        return {
            **sap.snapshot,
            "tenant": {"id": ctx.id, "industry": ctx.industry, "industry_label": ctx.industry_label, "customer": ctx.customer},
            "plants": sap.section("plants"),
            "materials": sap.section("materials"),
            "suppliers": [s["name"] for s in sap.section("suppliers")],
            "warehouse_demand_daily": sap.section("warehouse_demand_daily"),
        }

    # ===== FUNCTION: create_app.tenant_catalogue() =====
    # ID: F0034 · route · used
    # ORIGINAL FILE: backend/app/main.py:292-295
    # ROLE: HTTP GET /api/v1/tenants — Industries and customers for the top-bar selector (send the id back as the X-Tenant header).
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0963 test_catalogue_lists_industries_and_customers() (http_request)
    # CALLS:
    #   -> F0394 TenantRegistry.catalogue() (calls)
    #   -> F0397 TenantRegistry.current_id() (calls)
    #   -> F0391 TenantRegistry (references)
    @app.get("/api/v1/tenants")
    def tenant_catalogue() -> dict:
        """Industries and customers for the top-bar selector (send the id back as the X-Tenant header)."""
        return {**tenants.catalogue(), "active": TenantRegistry.current_id()}

    # ===== FUNCTION: create_app.network_map() =====
    # ID: F0035 · route · used
    # ORIGINAL FILE: backend/app/main.py:297-300
    # ROLE: HTTP GET /api/v1/network/map
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0224 SupplyChainEngine.network_map() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/network/map")
    def network_map(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.network_map()

    # ===== FUNCTION: create_app.sap_metadata() =====
    # ID: F0036 · route · used
    # ORIGINAL FILE: backend/app/main.py:302-305
    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F2099 router.odata() (http_request)
    #   <- F0862 test_sap_odata_reads_and_blocks_writes() (http_request)
    #   <- F0818 test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0415 SapRepository.metadata() (calls)
    #   -> F2099 router.odata() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata")
    def sap_metadata(who: Principal = Depends(reader)) -> dict:
        del who
        return sap.metadata()

    # ===== FUNCTION: create_app.sap_sandbox_documents() =====
    # ID: F0037 · route · used
    # ORIGINAL FILE: backend/app/main.py:307-311
    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F2099 router.odata() (http_request)
    #   <- F0818 test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0376 Store.sap_documents() (calls)
    #   -> F2099 router.odata() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument")
    def sap_sandbox_documents(who: Principal = Depends(reader)) -> dict:
        del who
        docs = store.sap_documents()
        return {"@odata.context": "$metadata#A_SandboxDocument", "@odata.count": len(docs), "value": docs, "__sandbox": True}

    # ===== FUNCTION: create_app.sap_odata() =====
    # ID: F0038 · route · used
    # ORIGINAL FILE: backend/app/main.py:313-326
    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity}
    # INPUTS:
    #   entity, top, plant, material, supplier, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F2047 validate_integrations.flowise() (http_request)
    #   <- F2099 router.odata() (http_request)
    #   <- F0888 Smoke.security() (http_request)
    #   <- F0862 test_sap_odata_reads_and_blocks_writes() (http_request)
    #   <- F2181 test_b_live_connection_sync_activate_and_rollback() (http_request)
    #   <- F2185 test_d_security() (http_request)
    #   <- F0818 test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0875 test_sap_read_endpoints_are_read_only() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0414 SapRepository.odata() (calls)
    #   -> F2099 router.odata() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity}")
    def sap_odata(
        entity: str,
        top: int = Query(default=200, alias="$top", ge=1, le=1000),
        plant: str | None = None,
        material: str | None = None,
        supplier: str | None = None,
        who: Principal = Depends(reader),
    ) -> dict:
        del who
        try:
            return sap.odata(entity, top=top, plant=plant, material=material, supplier=supplier)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown SAP entity {entity}") from exc

    # ===== FUNCTION: create_app.block_sap_write() =====
    # ID: F0039 · route · used
    # ORIGINAL FILE: backend/app/main.py:328-332
    # ROLE: HTTP POST/PUT/PATCH/DELETE /sap/opu/odata/sap/{path:path}
    # INPUTS:
    #   path, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Response
    # CALLED BY:
    #   <- F2047 validate_integrations.flowise() (http_request)
    #   <- F2084 SapODataConnector.test_connection() (http_request)
    #   <- F2098 router() (http_request)
    #   <- F2099 router.odata() (http_request)
    #   <- F0888 Smoke.security() (http_request)
    #   <- F0862 test_sap_odata_reads_and_blocks_writes() (http_request)
    #   <- F2181 test_b_live_connection_sync_activate_and_rollback() (http_request)
    #   <- F2185 test_d_security() (http_request)
    #   <- F0818 test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0875 test_sap_read_endpoints_are_read_only() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F2099 router.odata() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.api_route("/sap/opu/odata/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"])
    def block_sap_write(path: str, request: Request, who: Principal = Depends(reader)) -> Response:
        DENIALS.labels("sap_write").inc()
        store.audit(who.identity, who.role, "sap.write_blocked", {"path": path, "method": request.method}, request.state.correlation_id)
        raise HTTPException(status_code=405, detail="SAP adapter is read-only; write operations are disabled")


    # ------------------------------------------------- deterministic analyses
    # ===== FUNCTION: create_app.factory_readiness() =====
    # ID: F0040 · route · used
    # ORIGINAL FILE: backend/app/main.py:336-339
    # ROLE: HTTP POST /api/v1/analysis/factory-readiness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0472 ApiBackend.factory_readiness() (http_request)
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0863 test_analysis_validation_errors() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0866 test_agent_handoff_selects_analysis_server_side() (http_request)
    #   <- F0867 test_recommendation_requires_actions() (http_request)
    #   <- F2181 test_b_live_connection_sync_activate_and_rollback() (http_request)
    # CALLS:
    #   -> F0148 FactoryReadinessRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0197 SupplyChainEngine.factory_readiness() (calls)
    #   -> F0023 create_app.save() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0148 FactoryReadinessRequest (validates_input)
    @app.post("/api/v1/analysis/factory-readiness")
    def factory_readiness(body: FactoryReadinessRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.factory_readiness(body.plant, body.material, body.quantity, body.need_by)
        return save("factory_readiness", body.model_dump(mode="json"), result, who, request)

    # ===== FUNCTION: create_app.stock_balance() =====
    # ID: F0041 · route · used
    # ORIGINAL FILE: backend/app/main.py:341-343
    # ROLE: HTTP POST /api/v1/analysis/stock-balance
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0473 ApiBackend.stock_balance() (http_request)
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0863 test_analysis_validation_errors() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0149 StockBalanceRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0198 SupplyChainEngine.stock_balance() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0149 StockBalanceRequest (validates_input)
    @app.post("/api/v1/analysis/stock-balance")
    def stock_balance(body: StockBalanceRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stock_balance", body.model_dump(), engine.stock_balance(body.material, body.horizon_days, body.service_level), who, request)

    # ===== FUNCTION: create_app.demand_forecast() =====
    # ID: F0042 · route · used
    # ORIGINAL FILE: backend/app/main.py:345-347
    # ROLE: HTTP POST /api/v1/analysis/forecast
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0474 ApiBackend.demand_forecast() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0150 ForecastRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0199 SupplyChainEngine.demand_forecast() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0150 ForecastRequest (validates_input)
    @app.post("/api/v1/analysis/forecast")
    def demand_forecast(body: ForecastRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("forecast", body.model_dump(), engine.demand_forecast(body.material, body.warehouse, body.horizon_days), who, request)

    # ===== FUNCTION: create_app.what_if() =====
    # ID: F0043 · route · used
    # ORIGINAL FILE: backend/app/main.py:349-352
    # ROLE: HTTP POST /api/v1/analysis/what-if
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0151 WhatIfRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0200 SupplyChainEngine.what_if() (calls)
    #   -> F0023 create_app.save() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0151 WhatIfRequest (validates_input)
    @app.post("/api/v1/analysis/what-if")
    def what_if(body: WhatIfRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.what_if(body.material, body.demand_change_pct, body.supplier_delay_days, body.horizon_days)
        return save("what_if", body.model_dump(), result, who, request)

    # ===== FUNCTION: create_app.supplier_risk() =====
    # ID: F0044 · route · used
    # ORIGINAL FILE: backend/app/main.py:354-356
    # ROLE: HTTP POST /api/v1/analysis/supplier-risk
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0475 ApiBackend.supplier_risk() (http_request)
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0152 SupplierRiskRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0201 SupplyChainEngine.supplier_risk() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0152 SupplierRiskRequest (validates_input)
    @app.post("/api/v1/analysis/supplier-risk")
    def supplier_risk(body: SupplierRiskRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("supplier_risk", body.model_dump(), engine.supplier_risk(body.supplier), who, request)

    # ===== FUNCTION: create_app.quality() =====
    # ID: F0045 · route · used
    # ORIGINAL FILE: backend/app/main.py:358-360
    # ROLE: HTTP POST /api/v1/analysis/quality
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0476 ApiBackend.quality_status() (http_request)
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    #   <- F0866 test_agent_handoff_selects_analysis_server_side() (http_request)
    # CALLS:
    #   -> F0153 QualityRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0203 SupplyChainEngine.quality_status() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0153 QualityRequest (validates_input)
    @app.post("/api/v1/analysis/quality")
    def quality(body: QualityRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("quality_status", body.model_dump(), engine.quality_status(body.plant, body.material), who, request)

    # ===== FUNCTION: create_app.logistics() =====
    # ID: F0046 · route · used
    # ORIGINAL FILE: backend/app/main.py:362-364
    # ROLE: HTTP POST /api/v1/analysis/logistics
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0477 ApiBackend.logistics_status() (http_request)
    #   <- F0889 Smoke.analytics() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0154 LogisticsRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0204 SupplyChainEngine.logistics_status() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0154 LogisticsRequest (validates_input)
    @app.post("/api/v1/analysis/logistics")
    def logistics(body: LogisticsRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("logistics_status", body.model_dump(), engine.logistics_status(body.warehouse, body.material), who, request)

    # ===== FUNCTION: create_app.sales_orders() =====
    # ID: F0047 · route · used
    # ORIGINAL FILE: backend/app/main.py:366-368
    # ROLE: HTTP POST /api/v1/analysis/sales-orders
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0479 ApiBackend.sales_orders() (http_request)
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0155 SalesOrderRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0155 SalesOrderRequest (validates_input)
    @app.post("/api/v1/analysis/sales-orders")
    def sales_orders(body: SalesOrderRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("sales_order_fulfilment", body.model_dump(), engine.sales_order_fulfilment(body.warehouse), who, request)

    # ===== FUNCTION: create_app.stocktake() =====
    # ID: F0048 · route · used
    # ORIGINAL FILE: backend/app/main.py:370-372
    # ROLE: HTTP POST /api/v1/analysis/stocktake
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0480 ApiBackend.stocktake() (http_request)
    #   <- F0900 Smoke.operations_workspace() (http_request)
    # CALLS:
    #   -> F0156 StocktakeRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0207 SupplyChainEngine.stocktake_reconciliation() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0156 StocktakeRequest (validates_input)
    @app.post("/api/v1/analysis/stocktake")
    def stocktake(body: StocktakeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stocktake_reconciliation", body.model_dump(), engine.stocktake_reconciliation(body.tolerance_pct), who, request)

    # ===== FUNCTION: create_app.forecast_vs_actuals() =====
    # ID: F0049 · route · used
    # ORIGINAL FILE: backend/app/main.py:374-377
    # ROLE: HTTP GET /api/v1/analysis/forecast-vs-actuals
    # INPUTS:
    #   material, warehouse, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0209 SupplyChainEngine.forecast_vs_actuals() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/analysis/forecast-vs-actuals")
    def forecast_vs_actuals(material: str, warehouse: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.forecast_vs_actuals(material, warehouse)

    # ===== FUNCTION: create_app.production_overview() =====
    # ID: F0050 · route · used
    # ORIGINAL FILE: backend/app/main.py:379-382
    # ROLE: HTTP GET /api/v1/production/overview
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0208 SupplyChainEngine.production_overview() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/production/overview")
    def production_overview(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.production_overview()

    # ===== FUNCTION: create_app.products() =====
    # ID: F0051 · route · used
    # ORIGINAL FILE: backend/app/main.py:384-387
    # ROLE: HTTP GET /api/v1/products
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   <- F0946 test_brief_and_outlook_endpoints_follow_tenant() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0211 SupplyChainEngine.products() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/products")
    def products(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return engine.products()

    # ===== FUNCTION: create_app.product() =====
    # ID: F0052 · route · used
    # ORIGINAL FILE: backend/app/main.py:389-392
    # ROLE: HTTP GET /api/v1/products/{material}
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    #   <- F0946 test_brief_and_outlook_endpoints_follow_tenant() (http_request)
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0212 SupplyChainEngine.product_360() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/products/{material}")
    def product(material: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.product_360(material.upper())

    # ------------------------------------------------ role-centred decision views
    # ===== FUNCTION: create_app.role_catalogue() =====
    # ID: F0053 · route · used
    # ORIGINAL FILE: backend/app/main.py:395-398
    # ROLE: HTTP GET /api/v1/roles
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   <- F0955 test_catalogue_puts_the_five_mvp_roles_first() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0271 RoleCenter.catalogue() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/roles")
    def role_catalogue(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return roles.catalogue()

    # ===== FUNCTION: create_app.role_view() =====
    # ID: F0054 · route · used
    # ORIGINAL FILE: backend/app/main.py:400-405
    # ROLE: HTTP GET /api/v1/roles/{role}
    # INPUTS:
    #   role, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0878 test_tenant_scoped_authorization() (http_request)
    #   <- F0956 test_every_role_answers_the_four_questions() (http_request)
    #   <- F0957 test_role_views_know_the_aurelia_situation() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0272 RoleCenter.build() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/roles/{role}")
    def role_view(role: str, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        if role not in ROLES:
            raise HTTPException(status_code=404, detail=f"Unknown role {role}. Options: {', '.join(ROLES)}")
        return roles.build(role, material.upper() if material else None)

    # ===== FUNCTION: create_app.north_star() =====
    # ID: F0055 · route · used
    # ORIGINAL FILE: backend/app/main.py:407-410
    # ROLE: HTTP GET /api/v1/northstar
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0958 test_north_star_platform_kpis_and_industry_kpis() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0269 RoleCenter.north_star() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/northstar")
    def north_star(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return roles.north_star(material.upper() if material else None)

    # ===== FUNCTION: create_app.learning() =====
    # ID: F0056 · route · used
    # ORIGINAL FILE: backend/app/main.py:412-415
    # ROLE: HTTP GET /api/v1/learning
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0290 RoleCenter.learning() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/learning")
    def learning(who: Principal = Depends(reader)) -> dict:
        del who
        return roles.learning()

    # ===== FUNCTION: create_app.moat_view() =====
    # ID: F0057 · route · used
    # ORIGINAL FILE: backend/app/main.py:417-421
    # ROLE: HTTP GET /api/v1/moat — Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strength metrics.
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    #   <- F0960 test_moat_view_flywheel_metrics_and_consent_gate() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0255 MoatEngine.view() (calls)
    #   -> F0397 TenantRegistry.current_id() (calls)
    #   -> F0391 TenantRegistry (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/moat")
    def moat_view(who: Principal = Depends(reader)) -> dict:
        """Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strength metrics."""
        del who
        return moat.view(TenantRegistry.current_id())

    # ===== FUNCTION: create_app.moat_consent() =====
    # ID: F0058 · route · used
    # ORIGINAL FILE: backend/app/main.py:423-429
    # ROLE: HTTP POST /api/v1/moat/consent — The customer decides whether its data may contribute to industry learning (manager only, audited).
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0960 test_moat_view_flywheel_metrics_and_consent_gate() (http_request)
    # CALLS:
    #   -> F0163 ConsentRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0397 TenantRegistry.current_id() (calls)
    #   -> F0391 TenantRegistry (references)
    #   -> F0385 Store.set_consent() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0252 MoatEngine.consent() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0163 ConsentRequest (validates_input)
    @app.post("/api/v1/moat/consent")
    def moat_consent(body: ConsentRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        """The customer decides whether its data may contribute to industry learning (manager only, audited)."""
        tid = TenantRegistry.current_id()
        store.set_consent(tid, body.industry_learning, who.identity)
        store.audit(who.identity, who.role, "moat.consent", {"tenant": tid, "industry_learning": body.industry_learning}, request.state.correlation_id)
        return moat.consent(tid)

    # ===== FUNCTION: create_app.record_outcome() =====
    # ID: F0059 · route · used
    # ORIGINAL FILE: backend/app/main.py:431-443
    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/outcome — Record the real result of an executed recommendation against an SAP document (decision outcome learning).
    # INPUTS:
    #   recommendation_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    # CALLS:
    #   -> F0165 OutcomeRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0366 Store.get_recommendation() (calls)
    #   -> F0380 Store.list_outcomes() (calls)
    #   -> F0378 Store.create_outcome() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0016 _expectation() (calls)
    #   -> F0381 Store.record_outcome() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0165 OutcomeRequest (validates_input)
    @app.post("/api/v1/recommendations/{recommendation_id}/outcome")
    def record_outcome(recommendation_id: int, body: OutcomeRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        """Record the real result of an executed recommendation against an SAP document (decision outcome learning)."""
        rec = store.get_recommendation(recommendation_id)
        if rec and rec["status"] == "executed" and not any(o["recommendation_id"] == recommendation_id for o in store.list_outcomes()):
            # executed before outcome tracking existed: open its outcome record now
            store.create_outcome(recommendation_id, sap.snapshot["id"], rec["kind"], {"actions": len(rec["actions"]), "summary": "; ".join(_expectation(a) for a in rec["actions"])[:600]}, None)
        result = store.record_outcome(recommendation_id, body.achieved, body.observed, body.realized_impact_eur, body.source_document, body.note, who.identity)
        if result is None:
            raise HTTPException(status_code=409, detail="No executed recommendation awaiting an outcome with this id")
        store.audit(who.identity, who.role, "outcome.recorded", {"recommendation_id": recommendation_id, "achieved": body.achieved,
                                                                  "source_document": body.source_document}, request.state.correlation_id)
        return result

    # ===== FUNCTION: create_app.sales_outlook() =====
    # ID: F0060 · route · used
    # ORIGINAL FILE: backend/app/main.py:445-448
    # ROLE: HTTP GET /api/v1/sales/outlook
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0946 test_brief_and_outlook_endpoints_follow_tenant() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0220 SupplyChainEngine.sales_outlook() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/sales/outlook")
    def sales_outlook(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.sales_outlook(material.upper() if material else None)

    # ===== FUNCTION: create_app.product_brief() =====
    # ID: F0061 · route · used
    # ORIGINAL FILE: backend/app/main.py:450-453
    # ROLE: HTTP GET /api/v1/products/{material}/brief
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0946 test_brief_and_outlook_endpoints_follow_tenant() (http_request)
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0213 SupplyChainEngine.product_brief() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/products/{material}/brief")
    def product_brief(material: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.product_brief(material.upper())

    # ===== FUNCTION: create_app.sites() =====
    # ID: F0062 · route · used
    # ORIGINAL FILE: backend/app/main.py:455-458
    # ROLE: HTTP GET /api/v1/sites
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0221 SupplyChainEngine.sites() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/sites")
    def sites(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return engine.sites()

    # ===== FUNCTION: create_app.site() =====
    # ID: F0063 · route · used
    # ORIGINAL FILE: backend/app/main.py:460-463
    # ROLE: HTTP GET /api/v1/sites/{code}
    # INPUTS:
    #   code, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0222 SupplyChainEngine.site_360() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/sites/{code}")
    def site(code: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.site_360(code.upper())

    # ===== FUNCTION: create_app.dashboards_list() =====
    # ID: F0064 · route · used
    # ORIGINAL FILE: backend/app/main.py:465-467
    # ROLE: HTTP GET /api/v1/dashboards
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    # CALLS:
    #   (none found)
    @app.get("/api/v1/dashboards")
    def dashboards_list() -> dict:
        return PERSONAS

    # ===== FUNCTION: create_app.dashboard() =====
    # ID: F0065 · route · used
    # ORIGINAL FILE: backend/app/main.py:469-472
    # ROLE: HTTP GET /api/v1/dashboards/{persona}
    # INPUTS:
    #   persona, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    #   <- F0941 test_dashboards_focus_on_one_product() (http_request)
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0232 Dashboards.build() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/dashboards/{persona}")
    def dashboard(persona: str, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return dashboards.build(persona, material.upper() if material else None)

    # ===== FUNCTION: create_app.get_insights() =====
    # ID: F0066 · route · used
    # ORIGINAL FILE: backend/app/main.py:474-479
    # ROLE: HTTP GET /api/v1/insights
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    #   <- F0964 test_every_view_works_for_each_customer() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0248 InsightEngine.insights() (calls)
    #   -> F0404 SapRepository.as_of() (references)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/insights")
    def get_insights(who: Principal = Depends(reader)) -> dict:
        del who
        items = insight_engine.insights()
        return {"as_of": sap.as_of.isoformat(), "snapshot": sap.snapshot["id"], "deterministic": True,
                "counts": {s: sum(i["severity"] == s for i in items) for s in ("critical", "warning", "info", "good")}, "insights": items}

    # ------------------------------------------------------------ watches
    # ===== FUNCTION: create_app.watch_kinds() =====
    # ID: F0067 · route · used
    # ORIGINAL FILE: backend/app/main.py:482-484
    # ROLE: HTTP GET /api/v1/watches/kinds
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    # CALLS:
    #   (none found)
    @app.get("/api/v1/watches/kinds")
    def watch_kinds() -> dict:
        return WATCH_KINDS

    # ===== FUNCTION: create_app.list_watches() =====
    # ID: F0068 · route · used
    # ORIGINAL FILE: backend/app/main.py:486-488
    # ROLE: HTTP GET /api/v1/watches
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0372 Store.list_watches() (calls)
    #   -> F0022 create_app.watch_owner() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/watches")
    def list_watches(who: Principal = Depends(reader)) -> list[dict]:
        return store.list_watches(watch_owner(who))

    # ===== FUNCTION: create_app.create_watch() =====
    # ID: F0069 · route · used
    # ORIGINAL FILE: backend/app/main.py:490-498
    # ROLE: HTTP POST /api/v1/watches
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0157 WatchRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0249 InsightEngine.evaluate() (calls)
    #   -> F0369 Store.create_watch() (calls)
    #   -> F0022 create_app.watch_owner() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0157 WatchRequest (validates_input)
    @app.post("/api/v1/watches", status_code=201)
    def create_watch(body: WatchRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        missing = [p for p in WATCH_KINDS[body.kind]["params"] if not body.params.get(p)]
        if missing:
            raise HTTPException(status_code=422, detail=f"{body.kind} needs {', '.join(missing)}")
        insight_engine.evaluate(body.kind, body.params, body.threshold)  # validates codes before saving
        watch = store.create_watch(watch_owner(who), body.name, body.kind, body.params, body.threshold)
        store.audit(who.identity, who.role, "watch.created", {"watch_id": watch["id"], "kind": body.kind}, request.state.correlation_id)
        return watch

    # ===== FUNCTION: create_app.delete_watch() =====
    # ID: F0070 · route · used
    # ORIGINAL FILE: backend/app/main.py:500-504
    # ROLE: HTTP DELETE /api/v1/watches/{watch_id}
    # INPUTS:
    #   watch_id, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0373 Store.delete_watch() (calls)
    #   -> F0022 create_app.watch_owner() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.delete("/api/v1/watches/{watch_id}")
    def delete_watch(watch_id: int, who: Principal = Depends(reader)) -> dict:
        if not store.delete_watch(watch_id, watch_owner(who)):
            raise HTTPException(status_code=404, detail="Unknown watch")
        return {"deleted": watch_id}

    # ===== FUNCTION: create_app.evaluate_watches() =====
    # ID: F0071 · route · used
    # ORIGINAL FILE: backend/app/main.py:506-514
    # ROLE: HTTP POST /api/v1/watches/evaluate
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0940 test_api_dashboards_products_insights_watches() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0372 Store.list_watches() (calls)
    #   -> F0022 create_app.watch_owner() (calls)
    #   -> F0249 InsightEngine.evaluate() (calls)
    #   -> F0374 Store.record_watch() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.post("/api/v1/watches/evaluate")
    def evaluate_watches(who: Principal = Depends(reader)) -> dict:
        results = []
        for watch in store.list_watches(watch_owner(who)):
            result = insight_engine.evaluate(watch["kind"], watch["params"], watch["threshold"])
            changed = watch["last_value"] is not None and watch["last_value"] != result["value"]
            store.record_watch(watch["id"], result["value"], result["triggered"])
            results.append({**watch, **result, "changed": changed, "previous_value": watch["last_value"]})
        return {"evaluated": len(results), "triggered": sum(r["triggered"] for r in results), "watches": results}

    # ===== FUNCTION: create_app.get_analysis() =====
    # ID: F0072 · route · used
    # ORIGINAL FILE: backend/app/main.py:516-522
    # ROLE: HTTP GET /api/v1/analyses/{analysis_id}
    # INPUTS:
    #   analysis_id, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0362 Store.get_analysis() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/analyses/{analysis_id}")
    def get_analysis(analysis_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        analysis = store.get_analysis(analysis_id)
        if analysis is None:
            raise HTTPException(status_code=404, detail="Unknown analysis_id")
        return analysis

    # ===== FUNCTION: create_app.inventory() =====
    # ID: F0073 · route · used
    # ORIGINAL FILE: backend/app/main.py:524-527
    # ROLE: HTTP GET /api/v1/inventory
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0478 ApiBackend.inventory() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    #   <- F2181 test_b_live_connection_sync_activate_and_rollback() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0205 SupplyChainEngine.inventory_overview() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/inventory")
    def inventory(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return {"snapshot": sap.snapshot, **engine.inventory_overview(material)}

    # ===== FUNCTION: create_app.supplier_scorecard() =====
    # ID: F0074 · route · used
    # ORIGINAL FILE: backend/app/main.py:529-532
    # ROLE: HTTP GET /api/v1/suppliers/scorecard
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0202 SupplyChainEngine.supplier_scorecard() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/suppliers/scorecard")
    def supplier_scorecard(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.supplier_scorecard()

    # ===== FUNCTION: create_app.kpis() =====
    # ID: F0075 · route · used
    # ORIGINAL FILE: backend/app/main.py:534-537
    # ROLE: HTTP GET /api/v1/kpis
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0888 Smoke.security() (http_request)
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    #   <- F0873 test_metrics_exposed() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0226 SupplyChainEngine.kpis() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/kpis")
    def kpis(who: Principal = Depends(reader)) -> dict:
        del who
        return {"snapshot": sap.snapshot, **engine.kpis()}

    # -------------------------------------------------------------- RAG
    # ===== FUNCTION: create_app.rag_search() =====
    # ID: F0076 · route · used
    # ORIGINAL FILE: backend/app/main.py:540-543
    # ROLE: HTTP POST /api/v1/rag/search
    # INPUTS:
    #   body, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0481 ApiBackend.search_knowledge() (http_request)
    #   <- F1993 create_router() (http_request)
    #   <- F2014 create_router.rag_search() (http_request)
    #   <- F0629 search_supply_chain_policy() (http_request)
    #   <- F0678 policy() (http_request)
    #   <- F0890 Smoke.rag() (http_request)
    #   <- F0844 test_rag_is_tenant_scoped_cited_and_flags_injection() (http_request)
    #   <- F1937 test_candidate_index_is_separate_and_active_search_is_unchanged() (http_request)
    #   <- F1939 test_unauthorized_tenant_never_sees_other_documents() (http_request)
    #   <- F1944 test_publish_needs_director_benchmark_and_confirm_then_rollback() (http_request)
    #   <- F0868 test_rag_search_and_manager_only_ingest() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    # CALLS:
    #   -> F0158 RagQuery (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0746 MemoryRag.search() (calls)
    #   -> F0755 PgVectorRag.search() (calls)
    #   -> F2014 create_router.rag_search() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0158 RagQuery (validates_input)
    @app.post("/api/v1/rag/search")
    def rag_search(body: RagQuery, who: Principal = Depends(reader)) -> dict:
        del who
        return {"query": body.query, "results": rag.search(body.query, body.top_k, body.category)}

    # ===== FUNCTION: create_app.rag_search_get() =====
    # ID: F0077 · route · used
    # ORIGINAL FILE: backend/app/main.py:545-551
    # ROLE: HTTP GET /api/v1/rag/search — Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escaping of the question).
    # INPUTS:
    #   q, top_k, category, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0481 ApiBackend.search_knowledge() (http_request)
    #   <- F1993 create_router() (http_request)
    #   <- F2014 create_router.rag_search() (http_request)
    #   <- F0629 search_supply_chain_policy() (http_request)
    #   <- F0678 policy() (http_request)
    #   <- F0890 Smoke.rag() (http_request)
    #   <- F0844 test_rag_is_tenant_scoped_cited_and_flags_injection() (http_request)
    #   <- F1937 test_candidate_index_is_separate_and_active_search_is_unchanged() (http_request)
    #   <- F1939 test_unauthorized_tenant_never_sees_other_documents() (http_request)
    #   <- F1944 test_publish_needs_director_benchmark_and_confirm_then_rollback() (http_request)
    #   <- F0868 test_rag_search_and_manager_only_ingest() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0746 MemoryRag.search() (calls)
    #   -> F0755 PgVectorRag.search() (calls)
    #   -> F2014 create_router.rag_search() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/rag/search")
    def rag_search_get(q: str = Query(min_length=2, max_length=2000), top_k: int = Query(default=3, ge=1, le=12),
                       category: str | None = None, who: Principal = Depends(reader)) -> dict:
        """Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escaping of the question)."""
        del who
        hits = rag.search(q, top_k, category)
        return {"query": q, "results": [{k: h[k] for k in ("title", "category", "score", "text") if k in h} for h in hits]}

    # ===== FUNCTION: create_app.embeddings() =====
    # ID: F0078 · route · used
    # ORIGINAL FILE: backend/app/main.py:553-568
    # ROLE: HTTP POST /v1/embeddings — Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding model of the backend RAG,
    # INPUTS:
    #   body, request, authorization, x_api_key
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0168 EmbeddingsRequest (references)
    #   -> F0019 create_app.principal() (calls)
    #   -> F0079 create_app.embeddings.encode() (calls)
    #   -> F0168 EmbeddingsRequest (validates_input)
    @app.post("/v1/embeddings", tags=["RAG"], summary="OpenAI-compatible embeddings (same bge-small model as the governed RAG)")
    def embeddings(body: EmbeddingsRequest, request: Request, authorization: str | None = Header(default=None),
                   x_api_key: str | None = Header(default=None)) -> dict:
        """Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding model of the backend RAG,
        so one model serves both RAG paths. Auth: `Authorization: Bearer <key>` (OpenAI clients) or `X-API-Key`."""
        bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
        principal(request, x_api_key or bearer)
        texts = [body.input] if isinstance(body.input, str) else list(body.input)
        vectors = rag.embedder.embed(texts)
        # ===== FUNCTION: create_app.embeddings.encode() =====
        # ID: F0079 · nested · used
        # ORIGINAL FILE: backend/app/main.py:562-565
        # ROLE: Encode an embedding as a float list or base64 little-endian float32 (OpenAI clients).
        # INPUTS:
        #   vector
        # OUTPUT:
        #   see code
        # CALLED BY:
        #   <- F0078 create_app.embeddings() (calls)
        # CALLS:
        #   (none found)
        def encode(vector: list[float]):
            if body.encoding_format == "base64":  # openai-node asks for base64 by default and decodes it client-side
                return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode()
            return vector
        tokens = sum(len(t.split()) for t in texts)
        return {"object": "list", "model": rag.embedder.name, "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
                "data": [{"object": "embedding", "index": i, "embedding": encode(v)} for i, v in enumerate(vectors)]}

    # ===== FUNCTION: create_app.rag_stats() =====
    # ID: F0080 · route · used
    # ORIGINAL FILE: backend/app/main.py:570-573
    # ROLE: HTTP GET /api/v1/rag/stats
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0864 test_all_analysis_endpoints() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0747 MemoryRag.stats() (calls)
    #   -> F0753 PgVectorRag.stats() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/rag/stats")
    def rag_stats(who: Principal = Depends(reader)) -> dict:
        del who
        return rag.stats()

    # ===== FUNCTION: create_app.rag_add() =====
    # ID: F0081 · route · used
    # ORIGINAL FILE: backend/app/main.py:575-579
    # ROLE: HTTP POST /api/v1/rag/documents
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1993 create_router() (http_request)
    #   <- F2015 create_router.rag_documents() (http_request)
    #   <- F0868 test_rag_search_and_manager_only_ingest() (http_request)
    # CALLS:
    #   -> F0159 RagDocument (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0745 MemoryRag.add() (calls)
    #   -> F0752 PgVectorRag.add() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F2015 create_router.rag_documents() (http_request)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0159 RagDocument (validates_input)
    @app.post("/api/v1/rag/documents", status_code=201)
    def rag_add(body: RagDocument, request: Request, who: Principal = Depends(manager)) -> dict:
        chunks = rag.add(body.title, body.category, body.source, body.text)
        store.audit(who.identity, who.role, "rag.document_added", {"title": body.title, "chunks": chunks}, request.state.correlation_id)
        return {"chunks_added": chunks, "added_by": who.identity}

    # -------------------------------------------------- RAG Tuning page -> SCInsight API (every role; keys held server-side)
    # managers -> SCI_TUNING_KEY (director: may publish / roll back); planners -> SCI_TUNING_READER_KEY (mlops: everything else)
    # ===== FUNCTION: create_app.rag_tuning_proxy() =====
    # ID: F1801 · route · used
    # ORIGINAL FILE: backend/app/main.py:583-599
    # ROLE: HTTP GET/POST/PUT /api/v1/rag-tuning/{path:path}
    # INPUTS:
    #   path, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Response
    # CALLED BY:
    #   <- F1819 register() (http_request)
    #   <- F1824 register.get_config() (http_request)
    #   <- F1825 register.save_draft() (http_request)
    #   <- F1826 register.history() (http_request)
    #   <- F1827 register.config_diff() (http_request)
    #   <- F1828 register.list_documents() (http_request)
    #   <- F1829 register.validate_metadata() (http_request)
    #   <- F1830 register.document_source() (http_request)
    #   <- F1831 register.chunk_preview() (http_request)
    #   <- F1832 register.embedding_models() (http_request)
    #   <- F1833 register.test_model() (http_request)
    #   <- F1834 register.build_candidate() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F1824 register.get_config() (http_request)
    #   -> F1825 register.save_draft() (http_request)
    #   -> F1826 register.history() (http_request)
    #   -> F1827 register.config_diff() (http_request)
    #   -> F1828 register.list_documents() (http_request)
    #   -> F1829 register.validate_metadata() (http_request)
    #   -> F1830 register.document_source() (http_request)
    #   -> F1831 register.chunk_preview() (http_request)
    #   -> F1832 register.embedding_models() (http_request)
    @app.api_route("/api/v1/rag-tuning/{path:path}", methods=["GET", "POST", "PUT"], include_in_schema=False)
    async def rag_tuning_proxy(path: str, request: Request, who: Principal = Depends(reader)) -> Response:
        if path.strip("/") in ("publish", "rollback") and who.role != "manager":
            raise HTTPException(status_code=403, detail="Publishing or rolling back the RAG configuration needs the manager role")
        key = settings.sci_tuning_key if who.role == "manager" else settings.sci_tuning_reader_key
        if not key:
            raise HTTPException(status_code=503, detail="RAG tuning is not configured on the gateway (SCI_TUNING_KEY / SCI_TUNING_READER_KEY)")
        store.audit(who.identity, who.role, "rag_tuning.proxy", {"method": request.method, "path": path[:120]}, request.state.correlation_id)
        # in-process call to this same app's /scinsight routes (no network hop); SCI_API_URL only when SCInsight runs elsewhere
        local = app.state.scinsight is not None
        transport = httpx.ASGITransport(app=app) if local else None
        base = "http://local/scinsight" if local else settings.sci_api_url.rstrip("/")
        async with httpx.AsyncClient(timeout=120, transport=transport) as client:
            upstream = await client.request(request.method, f"{base}/api/v1/rag-tuning/{path}",
                                            params=dict(request.query_params), content=await request.body(),
                                            headers={"X-API-Key": key, "Content-Type": "application/json"})
        return Response(content=upstream.content, status_code=upstream.status_code, media_type="application/json")

    # -------------------------------------------------- backend code section (read: any key; save: manager + dev flag)
    code = CodeEditor(ROOT, settings.code_editor_enabled, settings.app_env)

    # ===== FUNCTION: create_app.code_files() =====
    # ID: F1950 · route · used
    # ORIGINAL FILE: backend/app/main.py:604-608
    # ROLE: HTTP GET /api/v1/code/files
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1991 test_backend_code_page_serves_each_apps_templates_and_nothing_else() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F1952 CodeEditor.files() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/code/files")
    def code_files(who: Principal = Depends(reader)) -> dict:
        del who
        # vscode_base: link prefix to open a file in VS Code on the machine that holds the repository (CODE_VSCODE_BASE)
        return {**code.files(), "vscode_base": settings.code_vscode_base}

    # ===== FUNCTION: create_app.code_file() =====
    # ID: F1951 · route · used
    # ORIGINAL FILE: backend/app/main.py:610-616
    # ROLE: HTTP GET /api/v1/code/file
    # INPUTS:
    #   path, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F1953 CodeEditor.file() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/code/file")
    def code_file(path: str = Query(min_length=5, max_length=300), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.file(path)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="file not found") from exc

    # ===== FUNCTION: create_app.code_template() =====
    # ID: F1955 · route · used
    # ORIGINAL FILE: backend/app/main.py:618-624
    # ROLE: HTTP GET /api/v1/code/template
    # INPUTS:
    #   name, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1991 test_backend_code_page_serves_each_apps_templates_and_nothing_else() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F1956 CodeEditor.template() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/code/template")
    def code_template(name: str = Query(pattern=r"^[a-z_]+\.py$"), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.template(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="template not found") from exc

    # ===== FUNCTION: create_app.code_functions() =====
    # ID: F0985 · route · used
    # ORIGINAL FILE: backend/app/main.py:626-629
    # ROLE: HTTP GET /api/v1/code/functions
    # INPUTS:
    #   q, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1796 test_api_lists_and_shows_backend_functions_read_only_by_default() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/code/functions")
    def code_functions(q: str = Query(default="", max_length=200), who: Principal = Depends(reader)) -> dict:
        del who
        return code.list(q)

    # ===== FUNCTION: create_app.code_function() =====
    # ID: F0986 · route · used
    # ORIGINAL FILE: backend/app/main.py:631-637
    # ROLE: HTTP GET /api/v1/code/function
    # INPUTS:
    #   key, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1796 test_api_lists_and_shows_backend_functions_read_only_by_default() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/code/function")
    def code_function(key: str = Query(min_length=5, max_length=400), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.get(key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown backend function") from exc

    # ===== FUNCTION: create_app.code_update() =====
    # ID: F0987 · route · used
    # ORIGINAL FILE: backend/app/main.py:639-649
    # ROLE: HTTP PUT /api/v1/code/function
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1796 test_api_lists_and_shows_backend_functions_read_only_by_default() (http_request)
    # CALLS:
    #   -> F0988 CodeUpdateRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0988 CodeUpdateRequest (validates_input)
    @app.put("/api/v1/code/function")
    def code_update(body: CodeUpdateRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        try:
            result = code.update(body.key, body.source, body.expected_sha256)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown backend function") from exc
        store.audit(who.identity, who.role, "code.function_updated",
                    {k: result.get(k) for k in ("key", "file", "changed", "backup", "sha256_before", "sha256_after")}, request.state.correlation_id)
        return result

    # -------------------------------------------------- LangGraph / agents
    # ===== FUNCTION: create_app._graph_call() =====
    # ID: F0082 · nested · used
    # ORIGINAL FILE: backend/app/main.py:652-658
    # ROLE: Run a graph call; non-HTTP errors become 502 Agent runtime error.
    # INPUTS:
    #   fn
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0083 create_app.chat() (calls)
    #   <- F0085 create_app.langgraph_agentflow() (calls)
    #   <- F0086 create_app.langgraph_agentflow_resume() (calls)
    #   <- F0087 create_app.business_start() (calls)
    #   <- F0088 create_app.business_resume() (calls)
    #   <- F0092 create_app.supplier_research() (calls)
    # CALLS:
    #   (none found)
    def _graph_call(fn, *args) -> dict:
        try:
            return fn(*args)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Agent runtime error: {str(exc)[:500]}") from exc

    # ===== FUNCTION: create_app.chat() =====
    # ID: F0083 · route · used
    # ORIGINAL FILE: backend/app/main.py:660-685
    # ROLE: HTTP POST /api/v1/chat
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0891 Smoke.langgraph_chat() (http_request)
    #   <- F0869 test_chat_and_business_workflow_through_api() (http_request)
    #   <- F0962 test_chat_accepts_only_known_roles() (http_request)
    # CALLS:
    #   -> F0164 ChatRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0626 GraphRunner.run() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0164 ChatRequest (validates_input)
    @app.post("/api/v1/chat")
    def chat(body: ChatRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        payload: dict = {"messages": [{"role": "user", "content": body.message}]}
        if body.role:  # specialised role agent: role mission, scoped tools and industry rules
            payload["role"] = body.role
        result = _graph_call(runner.run, "supply_chain_chat", payload, body.thread_id)
        messages = result["values"].get("messages", [])
        turn: list[dict] = []
        for message in reversed(messages):
            if message["type"] == "human":
                break
            turn.insert(0, message)
        answer = next((m["content"] for m in reversed(turn) if m["type"] == "ai" and m["content"]), "")
        tools_used = [call["name"] for m in turn for call in m.get("tool_calls", [])]
        store.audit(who.identity, who.role, "agent.chat", {"thread_id": result["thread_id"], "tools": tools_used}, request.state.correlation_id)
        return {
            "graph": "supply_chain_chat",
            "runtime": result["runtime"],
            "thread_id": result["thread_id"],
            "answer": answer,
            "answered_by": next((m["name"] for m in reversed(turn) if m["type"] == "ai"), None) or "qwen",
            "tools_used": tools_used,
            "tool_results": [m["content"][:4000] for m in turn if m["type"] == "tool"],
            "elapsed_seconds": result.get("elapsed_seconds"),
            "actor": who.identity,
        }

    # ===== FUNCTION: create_app._agentflow_view() =====
    # ID: F0084 · nested · used
    # ORIGINAL FILE: backend/app/main.py:687-709
    # ROLE: Shape the LangGraph agentflow result for the UI (route, workflow, answer, tools, interrupts).
    # INPUTS:
    #   result
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0085 create_app.langgraph_agentflow() (calls)
    #   <- F0086 create_app.langgraph_agentflow_resume() (calls)
    # CALLS:
    #   (none found)
    def _agentflow_view(result: dict) -> dict:
        values = result["values"]
        messages = values.get("messages", [])
        turn: list[dict] = []
        for message in reversed(messages):
            if message["type"] == "human":
                break
            turn.insert(0, message)
        return {
            "graph": "supply_chain_agentflow",
            "runtime": result["runtime"],
            "thread_id": result["thread_id"],
            "route": values.get("route"),
            "route_reason": values.get("route_reason"),
            "workflow": {"sap": values.get("sap_context"), "knowledge": [{k: d.get(k) for k in ("title", "category", "score")} for d in values.get("knowledge") or []]},
            "answer": "\n\n".join(m["content"] for m in turn if m["type"] == "ai" and m["content"]),
            "tools_used": [call["name"] for m in turn for call in m.get("tool_calls", [])],
            "analysis_id": (values.get("analysis") or {}).get("analysis_id"),
            "status": values.get("status"),
            "interrupts": result["interrupts"],
            "next": result["next"],
            "elapsed_seconds": result.get("elapsed_seconds"),
        }

    # ===== FUNCTION: create_app.langgraph_agentflow() =====
    # ID: F0085 · route · used
    # ORIGINAL FILE: backend/app/main.py:711-716
    # ROLE: HTTP POST /api/v1/langgraph/agentflow
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0892 Smoke.langgraph_agentflow() (http_request)
    #   <- F0870 test_langgraph_agentflow_through_api() (http_request)
    # CALLS:
    #   -> F0164 ChatRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0626 GraphRunner.run() (references)
    #   -> F0084 create_app._agentflow_view() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0164 ChatRequest (validates_input)
    @app.post("/api/v1/langgraph/agentflow")
    def langgraph_agentflow(body: ChatRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = _graph_call(runner.run, "supply_chain_agentflow", {"messages": [{"role": "user", "content": body.message}]}, body.thread_id)
        view = _agentflow_view(result)
        store.audit(who.identity, who.role, "agent.langgraph_agentflow", {"thread_id": view["thread_id"], "route": view["route"], "interrupted": bool(view["interrupts"])}, request.state.correlation_id)
        return view

    # ===== FUNCTION: create_app.langgraph_agentflow_resume() =====
    # ID: F0086 · route · used
    # ORIGINAL FILE: backend/app/main.py:718-722
    # ROLE: HTTP POST /api/v1/langgraph/agentflow/{thread_id}/resume
    # INPUTS:
    #   thread_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0892 Smoke.langgraph_agentflow() (http_request)
    #   <- F0870 test_langgraph_agentflow_through_api() (http_request)
    # CALLS:
    #   -> F0167 ResumeRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0084 create_app._agentflow_view() (calls)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0627 GraphRunner.resume() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0167 ResumeRequest (validates_input)
    @app.post("/api/v1/langgraph/agentflow/{thread_id}/resume")
    def langgraph_agentflow_resume(thread_id: str, body: ResumeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        view = _agentflow_view(_graph_call(runner.resume, "supply_chain_agentflow", thread_id, body.model_dump()))
        store.audit(who.identity, who.role, f"agent.langgraph_agentflow.{body.decision}", {"thread_id": thread_id, "status": view["status"]}, request.state.correlation_id)
        return view

    # ===== FUNCTION: create_app.business_start() =====
    # ID: F0087 · route · used
    # ORIGINAL FILE: backend/app/main.py:724-729
    # ROLE: HTTP POST /api/v1/workflows/business
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0893 Smoke.langgraph_business() (http_request)
    #   <- F0869 test_chat_and_business_workflow_through_api() (http_request)
    # CALLS:
    #   -> F0166 BusinessWorkflowRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0626 GraphRunner.run() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0166 BusinessWorkflowRequest (validates_input)
    @app.post("/api/v1/workflows/business")
    def business_start(body: BusinessWorkflowRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        payload = {k: v for k, v in body.model_dump(mode="json").items() if v is not None and k != "thread_id"}
        result = _graph_call(runner.run, "supply_chain_business", payload, body.thread_id)
        store.audit(who.identity, who.role, "agent.business_workflow.started", {"thread_id": result["thread_id"], "interrupted": bool(result["interrupts"])}, request.state.correlation_id)
        return {"graph": "supply_chain_business", **result}

    # ===== FUNCTION: create_app.business_resume() =====
    # ID: F0088 · route · used
    # ORIGINAL FILE: backend/app/main.py:731-735
    # ROLE: HTTP POST /api/v1/workflows/business/{thread_id}/resume
    # INPUTS:
    #   thread_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0893 Smoke.langgraph_business() (http_request)
    #   <- F0869 test_chat_and_business_workflow_through_api() (http_request)
    # CALLS:
    #   -> F0167 ResumeRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0627 GraphRunner.resume() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0167 ResumeRequest (validates_input)
    @app.post("/api/v1/workflows/business/{thread_id}/resume")
    def business_resume(thread_id: str, body: ResumeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = _graph_call(runner.resume, "supply_chain_business", thread_id, body.model_dump())
        store.audit(who.identity, who.role, f"agent.business_workflow.{body.decision}", {"thread_id": thread_id, "status": result["values"].get("status")}, request.state.correlation_id)
        return {"graph": "supply_chain_business", **result}

    # ------------------------------------------------ Deep Agent harness settings (governed, audited)
    HARNESS_KEY = "deep_agent_harness"
    # allowed range of every numeric harness setting, read from the schema so the UI never drifts from the validation
    HARNESS_RANGES = {name: [next(m.ge for m in f.metadata if hasattr(m, "ge")), next(m.le for m in f.metadata if hasattr(m, "le"))]
                      for name, f in DeepAgentHarness.model_fields.items()
                      if any(hasattr(m, "ge") for m in f.metadata) and any(hasattr(m, "le") for m in f.metadata)}

    # ===== FUNCTION: create_app.current_harness() =====
    # ID: F0089 · nested · used
    # ORIGINAL FILE: backend/app/main.py:744-746
    # ROLE: Current Deep Agent harness (stored setting validated over defaults).
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0017 create_app() (references)
    #   <- F0090 create_app.deep_harness() (calls)
    #   <- F0092 create_app.supplier_research() (calls)
    # CALLS:
    #   -> F0386 Store.get_setting() (calls)
    #   -> F0172 DeepAgentHarness (calls)
    def current_harness() -> dict:
        row = store.get_setting(HARNESS_KEY)
        return DeepAgentHarness(**(row["value"] if row else {})).model_dump()

    # ===== FUNCTION: create_app.deep_harness() =====
    # ID: F0090 · route · used
    # ORIGINAL FILE: backend/app/main.py:748-755
    # ROLE: HTTP GET /api/v1/deep-agents/harness
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0874 test_deep_agent_harness_settings_are_governed() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0386 Store.get_setting() (calls)
    #   -> F0089 create_app.current_harness() (calls)
    #   -> F0172 DeepAgentHarness (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/deep-agents/harness")
    def deep_harness(who: Principal = Depends(reader)) -> dict:
        del who
        row = store.get_setting(HARNESS_KEY)
        return {"harness": current_harness(), "defaults": DeepAgentHarness().model_dump(), "updated_by": row["updated_by"] if row else None,
                "updated_at": row["updated_at"] if row else None,
                "options": {"subagents": list(DEEP_SUBAGENTS), "tools": list(DEEP_TOOLS), "report_style": ["full", "executive"],
                            "ranges": HARNESS_RANGES}}

    # ===== FUNCTION: create_app.set_deep_harness() =====
    # ID: F0091 · route · used
    # ORIGINAL FILE: backend/app/main.py:757-761
    # ROLE: HTTP PUT /api/v1/deep-agents/harness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0874 test_deep_agent_harness_settings_are_governed() (http_request)
    # CALLS:
    #   -> F0172 DeepAgentHarness (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0387 Store.set_setting() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0172 DeepAgentHarness (validates_input)
    @app.put("/api/v1/deep-agents/harness")
    def set_deep_harness(body: DeepAgentHarness, request: Request, who: Principal = Depends(manager)) -> dict:
        saved = store.set_setting(HARNESS_KEY, body.model_dump(), who.identity)
        store.audit(who.identity, who.role, "agent.deep_research.harness_updated", body.model_dump(), request.state.correlation_id)
        return {"harness": saved["value"], "updated_by": saved["updated_by"], "updated_at": saved["updated_at"]}

    # ------------------------------------------------ ERP / SAP Setup (connections, mapping, sync, activation, checks)
    # Activation swaps the customer's snapshot in the TenantRegistry: every endpoint above (and so every Flowise / LangGraph tool)
    # computes on it from the next call. Restored from the database at startup.
    erp = ErpService(store, tenants, environment=settings.app_env, allowed_hosts=settings.erp_allowed_hosts)
    erp.restore()
    app.state.erp = erp
    erp_ctx = SimpleNamespace(tenants=tenants, store=store, rag=rag, runner=runner, settings=settings, erp=erp, harness=current_harness)

    # ===== FUNCTION: create_app.erp_audit() =====
    # ID: F2038 · nested · used
    # ORIGINAL FILE: backend/app/main.py:771-772
    # ROLE: Helper.
    # INPUTS:
    #   who, action, details, request
    # OUTPUT:
    #   None
    # CALLED BY:
    #   <- F0017 create_app() (references)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0358 Store.audit() (calls)
    def erp_audit(who: Principal, action: str, details: dict, request: Request) -> None:
        store.audit(who.identity, who.role, action, details, request.state.correlation_id)

    register_erp(app, erp=erp, ctx=erp_ctx, reader=reader, manager=manager, audit=erp_audit)
    if settings.app_env in ("development", "test"):  # SAP OData emulator for the "second ERP endpoint" demo and tests; never in staging/production
        app.include_router(erp_emulator(settings.data_file, settings.erp_emulator_password), prefix="/erp-emulator")
    if settings.erp_scheduler_enabled:
        erp.start_scheduler()  # daemon thread; scheduled syncs only stage snapshots

    # ===== FUNCTION: create_app.supplier_research() =====
    # ID: F0092 · route · used
    # ORIGINAL FILE: backend/app/main.py:780-801
    # ROLE: HTTP POST /api/v1/deep-agents/supplier-research
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0894 Smoke.deep_agent() (http_request)
    # CALLS:
    #   -> F0174 SupplierResearchRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0089 create_app.current_harness() (calls)
    #   -> F0082 create_app._graph_call() (calls)
    #   -> F0626 GraphRunner.run() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0174 SupplierResearchRequest (validates_input)
    @app.post("/api/v1/deep-agents/supplier-research")
    def supplier_research(body: SupplierResearchRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        prompt = f"Supplier: {body.supplier}." + (f" Material: {body.material}." if body.material else "") + f" Task: {body.question}"
        harness = current_harness()
        result = _graph_call(runner.run, "supplier_deep_agent", {"messages": [{"role": "user", "content": prompt}], "harness": harness}, body.thread_id)
        messages = result["values"].get("messages", [])
        report = next((m["content"] for m in reversed(messages) if m["type"] == "ai" and m["content"]), "")
        tools_used = [call["name"] for m in messages for call in m.get("tool_calls", [])]
        store.audit(who.identity, who.role, "agent.deep_research", {"thread_id": result["thread_id"], "tool_calls": len(tools_used)}, request.state.correlation_id)
        return {
            "agent": "supplier_deep_agent",
            "runtime": result["runtime"],
            "thread_id": result["thread_id"],
            "report": report,
            "todos": result["values"].get("todos", []),
            "tools_used": tools_used,
            "subagents_used": [call["args"].get("subagent_type") for m in messages for call in m.get("tool_calls", []) if call["name"] == "task"],
            "files": list((result["values"].get("files") or {}).keys()),
            "harness": result["values"].get("harness_used") or harness,
            "elapsed_seconds": result.get("elapsed_seconds"),
            "actor": who.identity,
        }

    # ------------------------------------------------------------ Flowise
    # ===== FUNCTION: create_app._flow_id() =====
    # ID: F0093 · nested · used
    # ORIGINAL FILE: backend/app/main.py:804-816
    # ROLE: Resolve a Flowise flow id: configured id, else look it up by name through the Flowise API.
    # INPUTS:
    #   flow
    # OUTPUT:
    #   str
    # CALLED BY:
    #   <- F0094 create_app.flowise_predict() (calls)
    # CALLS:
    #   (none found)
    async def _flow_id(flow: str) -> str:
        if flow_ids.get(flow):
            return flow_ids[flow]
        if not settings.flowise_url or not settings.flowise_api_key:
            raise HTTPException(status_code=503, detail="Flowise is not configured")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.flowise_url.rstrip('/')}/api/v1/chatflows", headers={"Authorization": f"Bearer {settings.flowise_api_key}"})
        response.raise_for_status()
        match = next((row["id"] for row in response.json() if row.get("name") == FLOW_NAMES[flow]), None)
        if not match:
            raise HTTPException(status_code=503, detail=f"Flowise flow '{FLOW_NAMES[flow]}' is not imported")
        flow_ids[flow] = match
        return match

    # ===== FUNCTION: create_app.flowise_predict() =====
    # ID: F0094 · route · used
    # ORIGINAL FILE: backend/app/main.py:818-853
    # ROLE: HTTP POST /api/v1/flowise/{flow}/predict
    # INPUTS:
    #   flow, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0895 Smoke.flowise_chatflow() (http_request)
    #   <- F0896 Smoke.flowise_agentflow() (http_request)
    # CALLS:
    #   -> F0175 FlowisePredictRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0093 create_app._flow_id() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0175 FlowisePredictRequest (validates_input)
    @app.post("/api/v1/flowise/{flow}/predict")
    async def flowise_predict(flow: str, body: FlowisePredictRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        if flow not in FLOW_NAMES:
            raise HTTPException(status_code=404, detail="flow must be chatflow or agentflow")
        flow_id = await _flow_id(flow)
        session_id = body.session_id or str(uuid.uuid4())
        # chatId + sessionId keep Flowise memory per conversation and let a paused AgentFlow Human Input resume.
        payload: dict = {"question": body.question, "chatId": session_id, "streaming": False, "overrideConfig": {"sessionId": session_id}}
        if body.form:
            payload["form"] = body.form
        if body.human_input:
            payload["humanInput"] = body.human_input
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds + 60) as client:
            response = await client.post(
                f"{settings.flowise_url.rstrip('/')}/api/v1/prediction/{flow_id}",
                headers={"Authorization": f"Bearer {settings.flowise_api_key}", "X-Correlation-ID": request.state.correlation_id},
                json=payload,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Flowise {response.status_code}: {response.text[:400]}")
        data = response.json()
        store.audit(who.identity, who.role, f"agent.flowise.{flow}", {"flow_id": flow_id, "session_id": session_id}, request.state.correlation_id)
        return {
            "flow": flow,
            "flow_id": flow_id,
            "session_id": session_id,
            "text": data.get("text", ""),
            "used_tools": [t.get("tool") for t in data.get("usedTools", []) or []],
            "agent_flow_executed": [
                {"node": n.get("nodeLabel"), "status": n.get("status")} for n in (data.get("agentFlowExecutedData") or [])
            ],
            "action": data.get("action"),
            "execution_id": data.get("executionId"),
            "elapsed_seconds": round(time.perf_counter() - started, 2),
        }

    # ------------------------------------------------- recommendations
    # ===== FUNCTION: create_app.submit_recommendation() =====
    # ID: F0095 · route · used
    # ORIGINAL FILE: backend/app/main.py:856-863
    # ROLE: HTTP POST /api/v1/recommendations
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0482 ApiBackend.submit_recommendation() (http_request)
    #   <- F0108 create_app.poc_decisions() (calls)
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0867 test_recommendation_requires_actions() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0160 RecommendationRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0364 Store.submit() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0160 RecommendationRequest (validates_input)
    @app.post("/api/v1/recommendations", status_code=201)
    def submit_recommendation(body: RecommendationRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        try:
            recommendation = store.submit(body.analysis_id, body.explanation, who.identity, source=body.source)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown analysis_id") from exc
        store.audit(who.identity, who.role, "recommendation.submitted", {"recommendation_id": recommendation["id"], "source": body.source}, request.state.correlation_id)
        return recommendation

    # ===== FUNCTION: create_app.submit_from_agent() =====
    # ID: F0096 · route · used
    # ORIGINAL FILE: backend/app/main.py:865-878
    # ROLE: HTTP POST /api/v1/recommendations/from-agent
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0866 test_agent_handoff_selects_analysis_server_side() (http_request)
    #   <- F0819 test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    # CALLS:
    #   -> F0161 RecommendationFromTextRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0363 Store.latest_actionable() (calls)
    #   -> F0364 Store.submit() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0161 RecommendationFromTextRequest (validates_input)
    @app.post("/api/v1/recommendations/from-agent", status_code=201)
    def submit_from_agent(body: RecommendationFromTextRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        ids = re.findall(r"AN-[0-9a-f]{12}", body.text)
        analysis = store.latest_actionable(ids, body.expected_kind)
        if analysis is None:
            raise HTTPException(status_code=422, detail=f"No {body.expected_kind} analysis with proposed actions referenced by the agent ({len(ids)} id(s) found)")
        explanation = body.text[:8000] + (f"\n\nPlanner comment: {body.comment}" if body.comment else "")
        recommendation = store.submit(analysis["id"], explanation, who.identity, source=body.source)
        store.audit(
            who.identity, who.role, "recommendation.submitted",
            {"recommendation_id": recommendation["id"], "source": body.source, "selected": analysis["id"], "candidates": ids},
            request.state.correlation_id,
        )
        return recommendation

    # ===== FUNCTION: create_app.recommendations() =====
    # ID: F0097 · route · used
    # ORIGINAL FILE: backend/app/main.py:880-883
    # ROLE: HTTP GET /api/v1/recommendations
    # INPUTS:
    #   status, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   <- F0482 ApiBackend.submit_recommendation() (http_request)
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0867 test_recommendation_requires_actions() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    #   <- F0965 test_customers_are_isolated() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0367 Store.list_recommendations() (calls)
    #   -> F0031 create_app.status() (references)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/recommendations")
    def recommendations(status: str | None = None, who: Principal = Depends(reader)) -> list[dict]:
        del who
        return store.list_recommendations(status, sap.snapshot["id"])

    # ===== FUNCTION: create_app.decide() =====
    # ID: F0098 · route · used
    # ORIGINAL FILE: backend/app/main.py:885-892
    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/decision
    # INPUTS:
    #   recommendation_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0109 create_app.poc_human_review() (calls)
    #   <- F0888 Smoke.security() (http_request)
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    # CALLS:
    #   -> F0162 DecisionRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0368 Store.decide() (calls)
    #   -> F0382 Store.record_feedback() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0162 DecisionRequest (validates_input)
    @app.post("/api/v1/recommendations/{recommendation_id}/decision")
    def decide(recommendation_id: int, body: DecisionRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        result = store.decide(recommendation_id, body.decision, who.identity, body.comment)
        if result is None:
            raise HTTPException(status_code=409, detail="Recommendation does not exist or was already decided")
        store.record_feedback(recommendation_id, body.decision, body.reason_code, body.modified and body.decision == "accepted", body.comment, who.identity)
        store.audit(who.identity, who.role, f"recommendation.{body.decision}", {"recommendation_id": recommendation_id}, request.state.correlation_id)
        return {**result, "sap_written": False, "next_step": "Authorized planner executes an accepted action manually in SAP."}

    DOC_TYPES = {
        "stock_transfer": "STO", "source_material": "PR", "expedite_purchase_order": "POCHG", "post_inventory_adjustment": "INVADJ",
        "post_pending_movements": "INVADJ", "recount": "RECOUNT", "propose_partial_delivery": "DLV",
    }

    # ===== FUNCTION: create_app.execute() =====
    # ID: F0099 · route · used
    # ORIGINAL FILE: backend/app/main.py:899-924
    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/execute — 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager only; agents cannot call this).
    # INPUTS:
    #   recommendation_id, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0900 Smoke.operations_workspace() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0942 test_one_click_execution_only_after_acceptance_and_only_for_manager() (http_request)
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0959 test_approval_is_not_proof_until_the_outcome_is_recorded() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0366 Store.get_recommendation() (calls)
    #   -> F0377 Store.next_doc_number() (calls)
    #   -> F0375 Store.execute_recommendation() (calls)
    #   -> F0404 SapRepository.as_of() (references)
    #   -> F0016 _expectation() (calls)
    #   -> F0378 Store.create_outcome() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0358 Store.audit() (calls)
    #   -> F0376 Store.sap_documents() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    @app.post("/api/v1/recommendations/{recommendation_id}/execute")
    def execute(recommendation_id: int, request: Request, who: Principal = Depends(manager)) -> dict:
        """1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager only; agents cannot call this)."""
        if settings.sap_execution_mode != "sandbox":
            raise HTTPException(status_code=403, detail="SAP execution is disabled; a planner executes accepted actions manually in SAP")
        rec = store.get_recommendation(recommendation_id)
        if rec is None or rec["status"] != "accepted":
            raise HTTPException(status_code=409, detail="Only an accepted recommendation can be executed (once)")
        documents = []
        for action in rec["actions"]:
            doc_type = DOC_TYPES.get(action.get("action"), "TASK")
            documents.append({"doc_type": doc_type, "doc_number": store.next_doc_number(doc_type) if not documents or doc_type not in {d["doc_type"] for d in documents}
                              else str(int(max(d["doc_number"] for d in documents if d["doc_type"] == doc_type)) + 1), "payload": action})
        result = store.execute_recommendation(recommendation_id, documents, who.identity)
        if result is None:
            raise HTTPException(status_code=409, detail="Recommendation was executed concurrently")
        # Decision outcome learning: what this decision is expected to achieve, to be checked against real SAP results later.
        dates = [a[k] for a in rec["actions"] for k in ("arrives", "new_delivery_date", "need_by") if isinstance(a.get(k), str)]
        due = max(dates) if dates else (sap.as_of + timedelta(days=14)).isoformat()
        expected = {"actions": len(rec["actions"]), "summary": "; ".join(_expectation(a) for a in rec["actions"])[:600],
                    "documents": [d["doc_number"] for d in documents]}
        store.create_outcome(recommendation_id, sap.snapshot["id"], rec["kind"], expected, due)
        store.audit(who.identity, who.role, "recommendation.executed_sandbox",
                    {"recommendation_id": recommendation_id, "documents": [d["doc_number"] for d in documents]}, request.state.correlation_id)
        return {**result, "sap_written": "sandbox", "documents": store.sap_documents(recommendation_id),
                "note": "Documents were created in the SAP mock sandbox outbox, not in a production SAP system."}

    # ===== FUNCTION: create_app.sap_documents() =====
    # ID: F0100 · route · used
    # ORIGINAL FILE: backend/app/main.py:926-929
    # ROLE: HTTP GET /api/v1/sap/documents
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0376 Store.sap_documents() (calls)
    #   -> F2006 create_router.sap_write_blocked() (http_request)
    #   -> F1967 create_app.sap_read_only() (http_request)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/api/v1/sap/documents")
    def sap_documents(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return store.sap_documents()

    # ===== FUNCTION: create_app.audit() =====
    # ID: F0101 · route · used
    # ORIGINAL FILE: backend/app/main.py:931-934
    # ROLE: HTTP GET /api/v1/audit
    # INPUTS:
    #   limit, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F1993 create_router() (http_request)
    #   <- F2027 create_router.audit() (http_request)
    #   <- F0901 Smoke.manager_decision() (http_request)
    #   <- F1960 create_app() (http_request)
    #   <- F1968 create_app.read_audit() (http_request)
    #   <- F1944 test_publish_needs_director_benchmark_and_confirm_then_rollback() (http_request)
    #   <- F0848 test_forged_tenant_is_rejected_and_audited() (http_request)
    #   <- F0862 test_sap_odata_reads_and_blocks_writes() (http_request)
    #   <- F0865 test_recommendation_lifecycle_and_roles() (http_request)
    #   <- F0874 test_deep_agent_harness_settings_are_governed() (http_request)
    #   <- F0878 test_tenant_scoped_authorization() (http_request)
    #   <- F1988 test_fastapi_template_auth_roles_validation_and_read_only_sap() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0359 Store.verify_chain() (calls)
    #   -> F0360 Store.audit_events() (calls)
    #   -> F2027 create_router.audit() (http_request)
    #   -> F1968 create_app.read_audit() (http_request)
    #   -> F0020 create_app.manager() (depends_on)
    @app.get("/api/v1/audit")
    def audit(limit: int = Query(default=100, ge=1, le=1000), who: Principal = Depends(manager)) -> dict:
        del who
        return {"chain_valid": store.verify_chain(), "events": store.audit_events(limit)}

    # ------------------------------------------------ POC contract: short REST paths for Flowise / LangGraph HTTP nodes
    # Thin, documented wrappers over the same engine, ledger and governance as /api/v1 — same auth, tenant scope and audit.
    poc = ["POC contract (Flowise / LangGraph REST)"]

    # ===== FUNCTION: create_app.poc_sap_inventory() =====
    # ID: F0102 · route · used
    # ORIGINAL FILE: backend/app/main.py:940-944
    # ROLE: HTTP GET /sap/inventory
    # INPUTS:
    #   plant, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0875 test_sap_read_endpoints_are_read_only() (http_request)
    #   <- F0878 test_tenant_scoped_authorization() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0414 SapRepository.odata() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/sap/inventory", tags=poc, summary="SAP material stock (read-only)")
    def poc_sap_inventory(plant: str | None = None, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        data = sap.odata("A_MaterialStock", top=1000, plant=plant, material=material)
        return {"source": "SAP S/4HANA OData A_MaterialStock (read-only)", "snapshot": sap.snapshot["id"], "count": len(data["value"]), "items": data["value"]}

    # ===== FUNCTION: create_app.poc_sap_production_orders() =====
    # ID: F0103 · route · used
    # ORIGINAL FILE: backend/app/main.py:946-950
    # ROLE: HTTP GET /sap/production-orders
    # INPUTS:
    #   plant, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F2181 test_b_live_connection_sync_activate_and_rollback() (http_request)
    #   <- F0875 test_sap_read_endpoints_are_read_only() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0414 SapRepository.odata() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/sap/production-orders", tags=poc, summary="SAP production orders (read-only)")
    def poc_sap_production_orders(plant: str | None = None, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        data = sap.odata("A_ProductionOrder", top=1000, plant=plant, material=material)
        return {"source": "SAP S/4HANA OData A_ProductionOrder (read-only)", "snapshot": sap.snapshot["id"], "count": len(data["value"]), "items": data["value"]}

    # ===== FUNCTION: create_app.poc_forecast_demand() =====
    # ID: F0104 · route · used
    # ORIGINAL FILE: backend/app/main.py:952-954
    # ROLE: HTTP POST /forecast/demand
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0876 test_forecasts_and_optimizers() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0150 ForecastRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0199 SupplyChainEngine.demand_forecast() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0150 ForecastRequest (validates_input)
    @app.post("/forecast/demand", tags=poc, summary="XGBoost demand forecast")
    def poc_forecast_demand(body: ForecastRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("forecast", body.model_dump(), engine.demand_forecast(body.material, body.warehouse, body.horizon_days), who, request)

    # ===== FUNCTION: create_app.poc_forecast_lead_time() =====
    # ID: F0105 · route · used
    # ORIGINAL FILE: backend/app/main.py:956-958
    # ROLE: HTTP POST /forecast/supplier-lead-time
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0876 test_forecasts_and_optimizers() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0170 SupplierLeadTimeRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0219 SupplyChainEngine.supplier_lead_time() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0170 SupplierLeadTimeRequest (validates_input)
    @app.post("/forecast/supplier-lead-time", tags=poc, summary="Empirical supplier lead-time forecast from SAP receipts")
    def poc_forecast_lead_time(body: SupplierLeadTimeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("supplier_lead_time", body.model_dump(), engine.supplier_lead_time(body.supplier, body.material), who, request)

    # ===== FUNCTION: create_app.poc_material_readiness() =====
    # ID: F0106 · route · used
    # ORIGINAL FILE: backend/app/main.py:960-963
    # ROLE: HTTP POST /optimizer/material-readiness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0876 test_forecasts_and_optimizers() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0148 FactoryReadinessRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0197 SupplyChainEngine.factory_readiness() (calls)
    #   -> F0023 create_app.save() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0148 FactoryReadinessRequest (validates_input)
    @app.post("/optimizer/material-readiness", tags=poc, summary="BOM material readiness (deterministic netting)")
    def poc_material_readiness(body: FactoryReadinessRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.factory_readiness(body.plant, body.material, body.quantity, body.need_by)
        return save("factory_readiness", body.model_dump(mode="json"), result, who, request)

    # ===== FUNCTION: create_app.poc_warehouse_transfer() =====
    # ID: F0107 · route · used
    # ORIGINAL FILE: backend/app/main.py:965-967
    # ROLE: HTTP POST /optimizer/warehouse-transfer
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0876 test_forecasts_and_optimizers() (http_request)
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0149 StockBalanceRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0023 create_app.save() (calls)
    #   -> F0198 SupplyChainEngine.stock_balance() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0149 StockBalanceRequest (validates_input)
    @app.post("/optimizer/warehouse-transfer", tags=poc, summary="Warehouse transfer optimisation (XGBoost + OR-Tools)")
    def poc_warehouse_transfer(body: StockBalanceRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stock_balance", body.model_dump(), engine.stock_balance(body.material, body.horizon_days, body.service_level), who, request)

    # ===== FUNCTION: create_app.poc_decisions() =====
    # ID: F0108 · route · used
    # ORIGINAL FILE: backend/app/main.py:969-971
    # ROLE: HTTP POST /decisions
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0160 RecommendationRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0095 create_app.submit_recommendation() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    #   -> F0160 RecommendationRequest (validates_input)
    @app.post("/decisions", tags=poc, status_code=201, summary="Submit a decision (recommendation) for human review")
    def poc_decisions(body: RecommendationRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return submit_recommendation(body, request, who)

    # ===== FUNCTION: create_app.poc_human_review() =====
    # ID: F0109 · route · used
    # ORIGINAL FILE: backend/app/main.py:973-975
    # ROLE: HTTP POST /decisions/{decision_id}/human-review
    # INPUTS:
    #   decision_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0162 DecisionRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0098 create_app.decide() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    #   -> F0162 DecisionRequest (validates_input)
    @app.post("/decisions/{decision_id}/human-review", tags=poc, summary="Manager accepts / modifies / rejects a decision")
    def poc_human_review(decision_id: int, body: DecisionRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        return decide(decision_id, body, request, who)

    # ===== FUNCTION: create_app.poc_reconcile() =====
    # ID: F0110 · route · used
    # ORIGINAL FILE: backend/app/main.py:977-1001
    # ROLE: HTTP POST /outcomes/reconcile
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0171 ReconcileRequest (references)
    #   -> F0767 Principal (references)
    #   -> F0020 create_app.manager() (references)
    #   -> F0366 Store.get_recommendation() (calls)
    #   -> F0404 SapRepository.as_of() (references)
    #   -> F0380 Store.list_outcomes() (calls)
    #   -> F0378 Store.create_outcome() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0016 _expectation() (calls)
    #   -> F0381 Store.record_outcome() (calls)
    #   -> F0358 Store.audit() (calls)
    #   -> F0020 create_app.manager() (depends_on)
    @app.post("/outcomes/reconcile", tags=poc, summary="Reconcile an executed decision with what SAP shows happened")
    def poc_reconcile(body: ReconcileRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        rec = store.get_recommendation(body.decision_id)
        if rec is None or rec["status"] != "executed":
            raise HTTPException(status_code=409, detail="Only an executed decision can be reconciled")
        expected_qty = sum(float(a.get("quantity") or 0) for a in rec["actions"] if isinstance(a.get("quantity"), (int, float))) or None
        dates = [a[k] for a in rec["actions"] for k in ("arrives", "new_delivery_date", "need_by") if isinstance(a.get(k), str)]
        # transfers carry a lane lead time instead of a date: expected arrival = SAP business date + lead days
        dates += [(sap.as_of + timedelta(days=int(a["lead_days"]))).isoformat() for a in rec["actions"] if isinstance(a.get("lead_days"), (int, float))]
        expected_date = max(dates) if dates else None
        qty_ok = body.actual_quantity is None or expected_qty is None or body.actual_quantity >= 0.95 * expected_qty
        date_ok = body.actual_date is None or expected_date is None or body.actual_date.isoformat() <= expected_date
        observed = {"sap_document": body.sap_document, "expected_quantity": expected_qty, "actual_quantity": body.actual_quantity,
                    "quantity_variance": None if body.actual_quantity is None or expected_qty is None else round(body.actual_quantity - expected_qty, 3),
                    "expected_by": expected_date, "actual_date": body.actual_date.isoformat() if body.actual_date else None,
                    "days_late": None if not (body.actual_date and expected_date) else (body.actual_date - date.fromisoformat(expected_date)).days,
                    "checks": {"quantity_in_full": qty_ok, "on_time": date_ok}}
        if not any(o["recommendation_id"] == body.decision_id for o in store.list_outcomes()):
            store.create_outcome(body.decision_id, sap.snapshot["id"], rec["kind"], {"actions": len(rec["actions"]), "summary": "; ".join(_expectation(a) for a in rec["actions"])[:600]}, expected_date)
        result = store.record_outcome(body.decision_id, qty_ok and date_ok, observed, body.realized_impact_eur, body.sap_document, body.note, who.identity)
        if result is None:
            raise HTTPException(status_code=409, detail="This decision's outcome was already reconciled")
        store.audit(who.identity, who.role, "outcome.reconciled", {"decision_id": body.decision_id, "achieved": result["achieved"], "sap_document": body.sap_document},
                    request.state.correlation_id)
        return {"decision_id": body.decision_id, "achieved": result["achieved"], "status": result["status"], "reconciliation": observed, "outcome": result}

    # ===== FUNCTION: create_app.poc_model_performance() =====
    # ID: F0111 · route · used
    # ORIGINAL FILE: backend/app/main.py:1003-1007
    # ROLE: HTTP GET /learning/model-performance
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    # CALLED BY:
    #   <- F0877 test_decision_lifecycle_human_review_and_reconciliation() (http_request)
    #   <- F0879 test_contract_is_documented_in_openapi() (http_request)
    # CALLS:
    #   -> F0767 Principal (references)
    #   -> F0021 create_app.reader() (references)
    #   -> F0290 RoleCenter.learning() (calls)
    #   -> F0021 create_app.reader() (depends_on)
    @app.get("/learning/model-performance", tags=poc, summary="Model accuracy, drift and verified decision outcomes")
    def poc_model_performance(who: Principal = Depends(reader)) -> dict:
        del who
        view = roles.learning()
        return {"as_of": view["as_of"], "models": view["models"], "summary": view["summary"], "note": view["note"]}

    # SCInsight API routes in this same app (before the static frontend, which catches every other path): /scinsight/api/v1/...
    app.state.scinsight = scinsight_router.state if scinsight_router is not None else None
    if scinsight_router is not None:
        app.include_router(scinsight_router, prefix="/scinsight", tags=["SCInsight API"])
    frontend = Path(ROOT / "frontend")
    if frontend.exists():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = create_app()
