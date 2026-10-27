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


# ROLE: Plain-language expected result of one executed action (what the outcome check will look for in SAP).
# INPUTS:
#   action
# OUTPUT:
#   str
def _expectation(action: dict) -> str:
    """Plain-language expected result of one executed action (what the outcome check will look for in SAP)."""
    kind = action.get("action", "action")
    if kind == "stock_transfer":
        return f"{action.get('quantity', 0):,.0f} {action.get('material', '')} from {action.get('from')} to {action.get('to')} by {action.get('arrives', 'the planned date')}"
    if kind == "expedite_purchase_order":
        return f"PO {action.get('po', '')} delivered by {action.get('new_delivery_date') or action.get('need_by', 'the need date')}"
    return kind.replace("_", " ") + (f" for {action['material']}" if action.get("material") else "")


# ROLE: Application factory of the SPARC / Aurelia gateway: builds the store, tenant registry + proxies, moat, RAG, auth and graph runner, then registers middleware, dependencies and ~95 routes as closures.
# INPUTS:
#   settings, store, runner, scinsight_router
# OUTPUT:
#   FastAPI
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

    # ROLE: HTTP middleware: correlation id, active tenant (X-Tenant or ?tenant=), Prometheus request count + latency.
    # INPUTS:
    #   request, call_next
    # OUTPUT:
    #   see code
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
        if response.headers.get("content-type", "").startswith(("text/html", "text/javascript", "application/javascript", "text/css")):
            response.headers["Cache-Control"] = "no-cache"  # dashboard files: revalidate (ETag) so a new release shows at once
        REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
        return response

    # ROLE: Dependency: authenticate X-API-Key (401) and enforce tenant scope (403); every denial is counted and audited.
    # INPUTS:
    #   request, x_api_key
    # OUTPUT:
    #   Principal
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

    # ROLE: Dependency: authenticated caller with the manager role (403 otherwise, audited).
    # INPUTS:
    #   request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Principal
    def manager(request: Request, who: Principal = Depends(principal)) -> Principal:
        try:
            return auth.require(who, "manager")
        except HTTPException:
            DENIALS.labels("role").inc()
            store.audit(who.identity, who.role, "auth.forbidden", {"path": request.url.path}, request.state.correlation_id)
            raise

    # ROLE: Dependency: authenticated caller with the assistant or manager role.
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Principal
    def reader(who: Principal = Depends(principal)) -> Principal:
        return auth.require(who, "assistant", "manager")

    # ROLE: Owner key of a watch: identity@tenant.
    # INPUTS:
    #   who
    # OUTPUT:
    #   str
    def watch_owner(who: Principal) -> str:
        return f"{who.identity}@{TenantRegistry.current_id()}"  # watches belong to a user within one customer

    # ROLE: Store an analysis (AN-...), audit it, count it, and return it with snapshot provenance and read_only=True.
    # INPUTS:
    #   kind, payload, result, who, request
    # OUTPUT:
    #   dict
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

    # ROLE: Exception handler: any ValueError from the engine becomes HTTP 422 with a VALIDATION_ERROR body.
    # INPUTS:
    #   request, exc
    # OUTPUT:
    #   see code
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": str(exc), "correlation_id": request.state.correlation_id}})

    # ------------------------------------------------------------- platform
    # ROLE: HTTP GET /health
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "supply-chain-copilot", "snapshot": sap.snapshot["id"], "cloud": settings.cloud_provider}

    # ROLE: HTTP GET /ready
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/ready")
    def ready() -> dict:
        return {"ready": True, "sap_snapshot_valid": sap.snapshot["validated"], "store": store.dialect, "rag": rag.stats()}

    # ROLE: HTTP GET /metrics
    # INPUTS:
    #   none
    # OUTPUT:
    #   Response
    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # ROLE: HTTP GET /api/v1/config/public — Non-secret links for the dashboard header.
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /api/v1/demo/session — Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the UI needs no login.
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/api/v1/demo/session", include_in_schema=False)
    def demo_session() -> dict:
        """Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the UI needs no login."""
        if not settings.demo_auto_login:
            raise HTTPException(status_code=404, detail="Not found")
        planner = next((k for k, who in settings.assistants.items() if who == "planner"), next(iter(settings.assistants), ""))
        manager = next(iter(settings.managers), "")
        return {"planner": planner, "manager": manager}

    # ROLE: Public URL of a companion service from PUBLIC_<SERVICE>_URL.
    # INPUTS:
    #   service
    # OUTPUT:
    #   str
    def _public(service: str) -> str:
        return os.environ.get(f"PUBLIC_{service.upper()}_URL", "")

    # ROLE: HTTP GET /api/v1/status
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/status")
    async def status(who: Principal = Depends(reader)) -> dict:
        del who

        # ROLE: Probe one service URL asynchronously (up / error / down / not_configured).
        # INPUTS:
        #   name, url, headers
        # OUTPUT:
        #   tuple[str, dict]
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
    # ROLE: HTTP GET /api/v1/snapshot
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /api/v1/tenants — Industries and customers for the top-bar selector (send the id back as the X-Tenant header).
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/api/v1/tenants")
    def tenant_catalogue() -> dict:
        """Industries and customers for the top-bar selector (send the id back as the X-Tenant header)."""
        return {**tenants.catalogue(), "active": TenantRegistry.current_id()}

    # ROLE: HTTP GET /api/v1/network/map
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/network/map")
    def network_map(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.network_map()

    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata")
    def sap_metadata(who: Principal = Depends(reader)) -> dict:
        del who
        return sap.metadata()

    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument")
    def sap_sandbox_documents(who: Principal = Depends(reader)) -> dict:
        del who
        docs = store.sap_documents()
        return {"@odata.context": "$metadata#A_SandboxDocument", "@odata.count": len(docs), "value": docs, "__sandbox": True}

    # ROLE: HTTP GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity}
    # INPUTS:
    #   entity, top, plant, material, supplier, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP POST/PUT/PATCH/DELETE /sap/opu/odata/sap/{path:path}
    # INPUTS:
    #   path, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Response
    @app.api_route("/sap/opu/odata/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"])
    def block_sap_write(path: str, request: Request, who: Principal = Depends(reader)) -> Response:
        DENIALS.labels("sap_write").inc()
        store.audit(who.identity, who.role, "sap.write_blocked", {"path": path, "method": request.method}, request.state.correlation_id)
        raise HTTPException(status_code=405, detail="SAP adapter is read-only; write operations are disabled")


    # ------------------------------------------------- deterministic analyses
    # ROLE: HTTP POST /api/v1/analysis/factory-readiness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/factory-readiness")
    def factory_readiness(body: FactoryReadinessRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.factory_readiness(body.plant, body.material, body.quantity, body.need_by)
        return save("factory_readiness", body.model_dump(mode="json"), result, who, request)

    # ROLE: HTTP POST /api/v1/analysis/stock-balance
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/stock-balance")
    def stock_balance(body: StockBalanceRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stock_balance", body.model_dump(), engine.stock_balance(body.material, body.horizon_days, body.service_level), who, request)

    # ROLE: HTTP POST /api/v1/analysis/forecast
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/forecast")
    def demand_forecast(body: ForecastRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("forecast", body.model_dump(), engine.demand_forecast(body.material, body.warehouse, body.horizon_days), who, request)

    # ROLE: HTTP POST /api/v1/analysis/what-if
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/what-if")
    def what_if(body: WhatIfRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.what_if(body.material, body.demand_change_pct, body.supplier_delay_days, body.horizon_days)
        return save("what_if", body.model_dump(), result, who, request)

    # ROLE: HTTP POST /api/v1/analysis/supplier-risk
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/supplier-risk")
    def supplier_risk(body: SupplierRiskRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("supplier_risk", body.model_dump(), engine.supplier_risk(body.supplier), who, request)

    # ROLE: HTTP POST /api/v1/analysis/quality
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/quality")
    def quality(body: QualityRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("quality_status", body.model_dump(), engine.quality_status(body.plant, body.material), who, request)

    # ROLE: HTTP POST /api/v1/analysis/logistics
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/logistics")
    def logistics(body: LogisticsRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("logistics_status", body.model_dump(), engine.logistics_status(body.warehouse, body.material), who, request)

    # ROLE: HTTP POST /api/v1/analysis/sales-orders
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/sales-orders")
    def sales_orders(body: SalesOrderRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("sales_order_fulfilment", body.model_dump(), engine.sales_order_fulfilment(body.warehouse), who, request)

    # ROLE: HTTP POST /api/v1/analysis/stocktake
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/analysis/stocktake")
    def stocktake(body: StocktakeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stocktake_reconciliation", body.model_dump(), engine.stocktake_reconciliation(body.tolerance_pct), who, request)

    # ROLE: HTTP GET /api/v1/analysis/forecast-vs-actuals
    # INPUTS:
    #   material, warehouse, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/analysis/forecast-vs-actuals")
    def forecast_vs_actuals(material: str, warehouse: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.forecast_vs_actuals(material, warehouse)

    # ROLE: HTTP GET /api/v1/production/overview
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/production/overview")
    def production_overview(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.production_overview()

    # ROLE: HTTP GET /api/v1/products
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/products")
    def products(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return engine.products()

    # ROLE: HTTP GET /api/v1/products/{material}
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/products/{material}")
    def product(material: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.product_360(material.upper())

    # ------------------------------------------------ role-centred decision views
    # ROLE: HTTP GET /api/v1/roles
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/roles")
    def role_catalogue(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return roles.catalogue()

    # ROLE: HTTP GET /api/v1/roles/{role}
    # INPUTS:
    #   role, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/roles/{role}")
    def role_view(role: str, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        if role not in ROLES:
            raise HTTPException(status_code=404, detail=f"Unknown role {role}. Options: {', '.join(ROLES)}")
        return roles.build(role, material.upper() if material else None)

    # ROLE: HTTP GET /api/v1/northstar
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/northstar")
    def north_star(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return roles.north_star(material.upper() if material else None)

    # ROLE: HTTP GET /api/v1/learning
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/learning")
    def learning(who: Principal = Depends(reader)) -> dict:
        del who
        return roles.learning()

    # ROLE: HTTP GET /api/v1/moat — Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strength metrics.
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/moat")
    def moat_view(who: Principal = Depends(reader)) -> dict:
        """Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strength metrics."""
        del who
        return moat.view(TenantRegistry.current_id())

    # ROLE: HTTP POST /api/v1/moat/consent — The customer decides whether its data may contribute to industry learning (manager only, audited).
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/moat/consent")
    def moat_consent(body: ConsentRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        """The customer decides whether its data may contribute to industry learning (manager only, audited)."""
        tid = TenantRegistry.current_id()
        store.set_consent(tid, body.industry_learning, who.identity)
        store.audit(who.identity, who.role, "moat.consent", {"tenant": tid, "industry_learning": body.industry_learning}, request.state.correlation_id)
        return moat.consent(tid)

    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/outcome — Record the real result of an executed recommendation against an SAP document (decision outcome learning).
    # INPUTS:
    #   recommendation_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /api/v1/sales/outlook
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/sales/outlook")
    def sales_outlook(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.sales_outlook(material.upper() if material else None)

    # ROLE: HTTP GET /api/v1/products/{material}/brief
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/products/{material}/brief")
    def product_brief(material: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.product_brief(material.upper())

    # ROLE: HTTP GET /api/v1/sites
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/sites")
    def sites(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return engine.sites()

    # ROLE: HTTP GET /api/v1/sites/{code}
    # INPUTS:
    #   code, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/sites/{code}")
    def site(code: str, who: Principal = Depends(reader)) -> dict:
        del who
        return engine.site_360(code.upper())

    # ROLE: HTTP GET /api/v1/dashboards
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/api/v1/dashboards")
    def dashboards_list() -> dict:
        return PERSONAS

    # ROLE: HTTP GET /api/v1/dashboards/{persona}
    # INPUTS:
    #   persona, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/dashboards/{persona}")
    def dashboard(persona: str, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return dashboards.build(persona, material.upper() if material else None)

    # ROLE: HTTP GET /api/v1/insights
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/insights")
    def get_insights(who: Principal = Depends(reader)) -> dict:
        del who
        items = insight_engine.insights()
        return {"as_of": sap.as_of.isoformat(), "snapshot": sap.snapshot["id"], "deterministic": True,
                "counts": {s: sum(i["severity"] == s for i in items) for s in ("critical", "warning", "info", "good")}, "insights": items}

    # ------------------------------------------------------------ watches
    # ROLE: HTTP GET /api/v1/watches/kinds
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    @app.get("/api/v1/watches/kinds")
    def watch_kinds() -> dict:
        return WATCH_KINDS

    # ROLE: HTTP GET /api/v1/watches
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/watches")
    def list_watches(who: Principal = Depends(reader)) -> list[dict]:
        return store.list_watches(watch_owner(who))

    # ROLE: HTTP POST /api/v1/watches
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/watches", status_code=201)
    def create_watch(body: WatchRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        missing = [p for p in WATCH_KINDS[body.kind]["params"] if not body.params.get(p)]
        if missing:
            raise HTTPException(status_code=422, detail=f"{body.kind} needs {', '.join(missing)}")
        insight_engine.evaluate(body.kind, body.params, body.threshold)  # validates codes before saving
        watch = store.create_watch(watch_owner(who), body.name, body.kind, body.params, body.threshold)
        store.audit(who.identity, who.role, "watch.created", {"watch_id": watch["id"], "kind": body.kind}, request.state.correlation_id)
        return watch

    # ROLE: HTTP DELETE /api/v1/watches/{watch_id}
    # INPUTS:
    #   watch_id, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.delete("/api/v1/watches/{watch_id}")
    def delete_watch(watch_id: int, who: Principal = Depends(reader)) -> dict:
        if not store.delete_watch(watch_id, watch_owner(who)):
            raise HTTPException(status_code=404, detail="Unknown watch")
        return {"deleted": watch_id}

    # ROLE: HTTP POST /api/v1/watches/evaluate
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/watches/evaluate")
    def evaluate_watches(who: Principal = Depends(reader)) -> dict:
        results = []
        for watch in store.list_watches(watch_owner(who)):
            result = insight_engine.evaluate(watch["kind"], watch["params"], watch["threshold"])
            changed = watch["last_value"] is not None and watch["last_value"] != result["value"]
            store.record_watch(watch["id"], result["value"], result["triggered"])
            results.append({**watch, **result, "changed": changed, "previous_value": watch["last_value"]})
        return {"evaluated": len(results), "triggered": sum(r["triggered"] for r in results), "watches": results}

    # ROLE: HTTP GET /api/v1/analyses/{analysis_id}
    # INPUTS:
    #   analysis_id, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/analyses/{analysis_id}")
    def get_analysis(analysis_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        analysis = store.get_analysis(analysis_id)
        if analysis is None:
            raise HTTPException(status_code=404, detail="Unknown analysis_id")
        return analysis

    # ROLE: HTTP GET /api/v1/inventory
    # INPUTS:
    #   material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/inventory")
    def inventory(material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        return {"snapshot": sap.snapshot, **engine.inventory_overview(material)}

    # ROLE: HTTP GET /api/v1/suppliers/scorecard
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/suppliers/scorecard")
    def supplier_scorecard(who: Principal = Depends(reader)) -> dict:
        del who
        return engine.supplier_scorecard()

    # ROLE: HTTP GET /api/v1/kpis
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/kpis")
    def kpis(who: Principal = Depends(reader)) -> dict:
        del who
        return {"snapshot": sap.snapshot, **engine.kpis()}

    # -------------------------------------------------------------- RAG
    # ROLE: HTTP POST /api/v1/rag/search
    # INPUTS:
    #   body, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/rag/search")
    def rag_search(body: RagQuery, who: Principal = Depends(reader)) -> dict:
        del who
        return {"query": body.query, "results": rag.search(body.query, body.top_k, body.category)}

    # ROLE: HTTP GET /api/v1/rag/search — Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escaping of the question).
    # INPUTS:
    #   q, top_k, category, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/rag/search")
    def rag_search_get(q: str = Query(min_length=2, max_length=2000), top_k: int = Query(default=3, ge=1, le=12),
                       category: str | None = None, who: Principal = Depends(reader)) -> dict:
        """Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escaping of the question)."""
        del who
        hits = rag.search(q, top_k, category)
        return {"query": q, "results": [{k: h[k] for k in ("title", "category", "score", "text") if k in h} for h in hits]}

    # ROLE: HTTP POST /v1/embeddings — Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding model of the backend RAG,
    # INPUTS:
    #   body, request, authorization, x_api_key
    # OUTPUT:
    #   dict
    @app.post("/v1/embeddings", tags=["RAG"], summary="OpenAI-compatible embeddings (same bge-small model as the governed RAG)")
    def embeddings(body: EmbeddingsRequest, request: Request, authorization: str | None = Header(default=None),
                   x_api_key: str | None = Header(default=None)) -> dict:
        """Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding model of the backend RAG,
        so one model serves both RAG paths. Auth: `Authorization: Bearer <key>` (OpenAI clients) or `X-API-Key`."""
        bearer = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None
        principal(request, x_api_key or bearer)
        texts = [body.input] if isinstance(body.input, str) else list(body.input)
        vectors = rag.embedder.embed(texts)
        # ROLE: Encode an embedding as a float list or base64 little-endian float32 (OpenAI clients).
        # INPUTS:
        #   vector
        # OUTPUT:
        #   see code
        def encode(vector: list[float]):
            if body.encoding_format == "base64":  # openai-node asks for base64 by default and decodes it client-side
                return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode()
            return vector
        tokens = sum(len(t.split()) for t in texts)
        return {"object": "list", "model": rag.embedder.name, "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
                "data": [{"object": "embedding", "index": i, "embedding": encode(v)} for i, v in enumerate(vectors)]}

    # ROLE: HTTP GET /api/v1/rag/stats
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/rag/stats")
    def rag_stats(who: Principal = Depends(reader)) -> dict:
        del who
        return rag.stats()

    # ROLE: HTTP POST /api/v1/rag/documents
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/rag/documents", status_code=201)
    def rag_add(body: RagDocument, request: Request, who: Principal = Depends(manager)) -> dict:
        chunks = rag.add(body.title, body.category, body.source, body.text)
        store.audit(who.identity, who.role, "rag.document_added", {"title": body.title, "chunks": chunks}, request.state.correlation_id)
        return {"chunks_added": chunks, "added_by": who.identity}

    # -------------------------------------------------- RAG Tuning page -> SCInsight API (every role; keys held server-side)
    # managers -> SCI_TUNING_KEY (director: may publish / roll back); planners -> SCI_TUNING_READER_KEY (mlops: everything else)
    # ROLE: HTTP GET/POST/PUT /api/v1/rag-tuning/{path:path}
    # INPUTS:
    #   path, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   Response
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

    # ROLE: HTTP GET /api/v1/code/files
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/code/files")
    def code_files(who: Principal = Depends(reader)) -> dict:
        del who
        # vscode_base: link prefix to open a file in VS Code on the machine that holds the repository (CODE_VSCODE_BASE)
        return {**code.files(), "vscode_base": settings.code_vscode_base}

    # ROLE: HTTP GET /api/v1/code/file
    # INPUTS:
    #   path, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/code/file")
    def code_file(path: str = Query(min_length=5, max_length=300), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.file(path)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="file not found") from exc

    # ROLE: HTTP GET /api/v1/code/template
    # INPUTS:
    #   name, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/code/template")
    def code_template(name: str = Query(pattern=r"^[a-z_]+\.py$"), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.template(name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="template not found") from exc

    # ROLE: HTTP GET /api/v1/code/functions
    # INPUTS:
    #   q, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/code/functions")
    def code_functions(q: str = Query(default="", max_length=200), who: Principal = Depends(reader)) -> dict:
        del who
        return code.list(q)

    # ROLE: HTTP GET /api/v1/code/function
    # INPUTS:
    #   key, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/code/function")
    def code_function(key: str = Query(min_length=5, max_length=400), who: Principal = Depends(reader)) -> dict:
        del who
        try:
            return code.get(key)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown backend function") from exc

    # ROLE: HTTP PUT /api/v1/code/function
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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
    # ROLE: Run a graph call; non-HTTP errors become 502 Agent runtime error.
    # INPUTS:
    #   fn
    # OUTPUT:
    #   dict
    def _graph_call(fn, *args) -> dict:
        try:
            return fn(*args)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Agent runtime error: {str(exc)[:500]}") from exc

    # ROLE: HTTP POST /api/v1/chat
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: Shape the LangGraph agentflow result for the UI (route, workflow, answer, tools, interrupts).
    # INPUTS:
    #   result
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP POST /api/v1/langgraph/agentflow
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/langgraph/agentflow")
    def langgraph_agentflow(body: ChatRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = _graph_call(runner.run, "supply_chain_agentflow", {"messages": [{"role": "user", "content": body.message}]}, body.thread_id)
        view = _agentflow_view(result)
        store.audit(who.identity, who.role, "agent.langgraph_agentflow", {"thread_id": view["thread_id"], "route": view["route"], "interrupted": bool(view["interrupts"])}, request.state.correlation_id)
        return view

    # ROLE: HTTP POST /api/v1/langgraph/agentflow/{thread_id}/resume
    # INPUTS:
    #   thread_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/langgraph/agentflow/{thread_id}/resume")
    def langgraph_agentflow_resume(thread_id: str, body: ResumeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        view = _agentflow_view(_graph_call(runner.resume, "supply_chain_agentflow", thread_id, body.model_dump()))
        store.audit(who.identity, who.role, f"agent.langgraph_agentflow.{body.decision}", {"thread_id": thread_id, "status": view["status"]}, request.state.correlation_id)
        return view

    # ROLE: HTTP POST /api/v1/workflows/business
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/workflows/business")
    def business_start(body: BusinessWorkflowRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        payload = {k: v for k, v in body.model_dump(mode="json").items() if v is not None and k != "thread_id"}
        result = _graph_call(runner.run, "supply_chain_business", payload, body.thread_id)
        store.audit(who.identity, who.role, "agent.business_workflow.started", {"thread_id": result["thread_id"], "interrupted": bool(result["interrupts"])}, request.state.correlation_id)
        return {"graph": "supply_chain_business", **result}

    # ROLE: HTTP POST /api/v1/workflows/business/{thread_id}/resume
    # INPUTS:
    #   thread_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: Current Deep Agent harness (stored setting validated over defaults).
    # INPUTS:
    #   none
    # OUTPUT:
    #   dict
    def current_harness() -> dict:
        row = store.get_setting(HARNESS_KEY)
        return DeepAgentHarness(**(row["value"] if row else {})).model_dump()

    # ROLE: HTTP GET /api/v1/deep-agents/harness
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/deep-agents/harness")
    def deep_harness(who: Principal = Depends(reader)) -> dict:
        del who
        row = store.get_setting(HARNESS_KEY)
        return {"harness": current_harness(), "defaults": DeepAgentHarness().model_dump(), "updated_by": row["updated_by"] if row else None,
                "updated_at": row["updated_at"] if row else None,
                "options": {"subagents": list(DEEP_SUBAGENTS), "tools": list(DEEP_TOOLS), "report_style": ["full", "executive"],
                            "ranges": HARNESS_RANGES}}

    # ROLE: HTTP PUT /api/v1/deep-agents/harness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: Helper.
    # INPUTS:
    #   who, action, details, request
    # OUTPUT:
    #   None
    def erp_audit(who: Principal, action: str, details: dict, request: Request) -> None:
        store.audit(who.identity, who.role, action, details, request.state.correlation_id)

    register_erp(app, erp=erp, ctx=erp_ctx, reader=reader, manager=manager, audit=erp_audit)
    if settings.app_env in ("development", "test"):  # SAP OData emulator for the "second ERP endpoint" demo and tests; never in staging/production
        app.include_router(erp_emulator(settings.data_file, settings.erp_emulator_password), prefix="/erp-emulator")
    if settings.erp_scheduler_enabled:
        erp.start_scheduler()  # daemon thread; scheduled syncs only stage snapshots

    # ROLE: HTTP POST /api/v1/deep-agents/supplier-research
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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
    # ROLE: Resolve a Flowise flow id: configured id, else look it up by name through the Flowise API.
    # INPUTS:
    #   flow
    # OUTPUT:
    #   str
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

    # ROLE: HTTP POST /api/v1/flowise/{flow}/predict
    # INPUTS:
    #   flow, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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
    # ROLE: HTTP POST /api/v1/recommendations
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/api/v1/recommendations", status_code=201)
    def submit_recommendation(body: RecommendationRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        try:
            recommendation = store.submit(body.analysis_id, body.explanation, who.identity, source=body.source)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown analysis_id") from exc
        store.audit(who.identity, who.role, "recommendation.submitted", {"recommendation_id": recommendation["id"], "source": body.source}, request.state.correlation_id)
        return recommendation

    # ROLE: HTTP POST /api/v1/recommendations/from-agent
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /api/v1/recommendations
    # INPUTS:
    #   status, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/recommendations")
    def recommendations(status: str | None = None, who: Principal = Depends(reader)) -> list[dict]:
        del who
        return store.list_recommendations(status, sap.snapshot["id"])

    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/decision
    # INPUTS:
    #   recommendation_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP POST /api/v1/recommendations/{recommendation_id}/execute — 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager only; agents cannot call this).
    # INPUTS:
    #   recommendation_id, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /api/v1/sap/documents
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   list[dict]
    @app.get("/api/v1/sap/documents")
    def sap_documents(who: Principal = Depends(reader)) -> list[dict]:
        del who
        return store.sap_documents()

    # ROLE: HTTP GET /api/v1/audit
    # INPUTS:
    #   limit, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/api/v1/audit")
    def audit(limit: int = Query(default=100, ge=1, le=1000), who: Principal = Depends(manager)) -> dict:
        del who
        return {"chain_valid": store.verify_chain(), "events": store.audit_events(limit)}

    # ------------------------------------------------ POC contract: short REST paths for Flowise / LangGraph HTTP nodes
    # Thin, documented wrappers over the same engine, ledger and governance as /api/v1 — same auth, tenant scope and audit.
    poc = ["POC contract (Flowise / LangGraph REST)"]

    # ROLE: HTTP GET /sap/inventory
    # INPUTS:
    #   plant, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/sap/inventory", tags=poc, summary="SAP material stock (read-only)")
    def poc_sap_inventory(plant: str | None = None, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        data = sap.odata("A_MaterialStock", top=1000, plant=plant, material=material)
        return {"source": "SAP S/4HANA OData A_MaterialStock (read-only)", "snapshot": sap.snapshot["id"], "count": len(data["value"]), "items": data["value"]}

    # ROLE: HTTP GET /sap/production-orders
    # INPUTS:
    #   plant, material, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.get("/sap/production-orders", tags=poc, summary="SAP production orders (read-only)")
    def poc_sap_production_orders(plant: str | None = None, material: str | None = None, who: Principal = Depends(reader)) -> dict:
        del who
        data = sap.odata("A_ProductionOrder", top=1000, plant=plant, material=material)
        return {"source": "SAP S/4HANA OData A_ProductionOrder (read-only)", "snapshot": sap.snapshot["id"], "count": len(data["value"]), "items": data["value"]}

    # ROLE: HTTP POST /forecast/demand
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/forecast/demand", tags=poc, summary="XGBoost demand forecast")
    def poc_forecast_demand(body: ForecastRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("forecast", body.model_dump(), engine.demand_forecast(body.material, body.warehouse, body.horizon_days), who, request)

    # ROLE: HTTP POST /forecast/supplier-lead-time
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/forecast/supplier-lead-time", tags=poc, summary="Empirical supplier lead-time forecast from SAP receipts")
    def poc_forecast_lead_time(body: SupplierLeadTimeRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("supplier_lead_time", body.model_dump(), engine.supplier_lead_time(body.supplier, body.material), who, request)

    # ROLE: HTTP POST /optimizer/material-readiness
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/optimizer/material-readiness", tags=poc, summary="BOM material readiness (deterministic netting)")
    def poc_material_readiness(body: FactoryReadinessRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        result = engine.factory_readiness(body.plant, body.material, body.quantity, body.need_by)
        return save("factory_readiness", body.model_dump(mode="json"), result, who, request)

    # ROLE: HTTP POST /optimizer/warehouse-transfer
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/optimizer/warehouse-transfer", tags=poc, summary="Warehouse transfer optimisation (XGBoost + OR-Tools)")
    def poc_warehouse_transfer(body: StockBalanceRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return save("stock_balance", body.model_dump(), engine.stock_balance(body.material, body.horizon_days, body.service_level), who, request)

    # ROLE: HTTP POST /decisions
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/decisions", tags=poc, status_code=201, summary="Submit a decision (recommendation) for human review")
    def poc_decisions(body: RecommendationRequest, request: Request, who: Principal = Depends(reader)) -> dict:
        return submit_recommendation(body, request, who)

    # ROLE: HTTP POST /decisions/{decision_id}/human-review
    # INPUTS:
    #   decision_id, body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
    @app.post("/decisions/{decision_id}/human-review", tags=poc, summary="Manager accepts / modifies / rejects a decision")
    def poc_human_review(decision_id: int, body: DecisionRequest, request: Request, who: Principal = Depends(manager)) -> dict:
        return decide(decision_id, body, request, who)

    # ROLE: HTTP POST /outcomes/reconcile
    # INPUTS:
    #   body, request, who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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

    # ROLE: HTTP GET /learning/model-performance
    # INPUTS:
    #   who
    #   (FastAPI Depends(...) parameters are injected: principal -> reader / manager run first)
    # OUTPUT:
    #   dict
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
