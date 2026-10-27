# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/mcp_server.py
# What this module is: the restricted MCP server (Model Context Protocol, Streamable HTTP) of the SPARC platform: 10 read-only tools
# consumed by the Aurelia Flowise flows (Custom MCP node) and the LangGraph MCP client. Every tool calls the governed backend
# (the FastAPI gateway in deployments). /mcp is protected by an API-key middleware; /health is open.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Restricted MCP server (Streamable HTTP) exposing read-only SAP, analytics and RAG tools.

Consumed by the Flowise Chatflow / AgentFlow V2 (Custom MCP tool) and by the LangGraph MCP client.
Every tool calls the governed FastAPI gateway, so MCP calls are authenticated, audited and metered there.
"""
from __future__ import annotations

import hmac
import json
import os

import uvicorn
# FastMCP: high-level MCP server; @mcp.tool() registers a function as an MCP tool (schema from type hints + docstring).
from mcp.server.fastmcp import FastMCP
# Starlette pieces for the API-key middleware and the health route.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.copilot import get_backend

# The MCP server: stateless HTTP (no session affinity needed behind a load balancer), JSON responses.
mcp = FastMCP(
    "aurelia-supply-chain-readonly",
    instructions="Read-only SAP S/4HANA mock, deterministic analytics and governed RAG. No tool can write to SAP.",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
)


# ===== FUNCTION: _dump() =====
# ID: F0485 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:29-33
# ROLE: Call a backend method; JSON result capped at 12000 characters; errors returned as {"error": ...}.
# INPUTS:
#   fn: callable, *args.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0486 sap_snapshot() (calls)
#   <- F0487 factory_material_readiness() (calls)
#   <- F0488 warehouse_stock_balance() (calls)
#   <- F0489 supplier_risk() (calls)
#   <- F0490 quality_status() (calls)
#   <- F0491 logistics_status() (calls)
#   <- F0492 inventory_overview() (calls)
#   <- F0493 sales_order_fulfilment() (calls)
#   <- F0494 stocktake_reconciliation() (calls)
#   <- F0495 search_governed_knowledge() (calls)
# CALLS:
#   (none found)
def _dump(fn, *args) -> str:
    try:
        return json.dumps(fn(*args), default=str)[:12000]
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)[:600]})


# ===== FUNCTION: sap_snapshot() =====
# ID: F0486 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:36-39
# ROLE: MCP tool sap_snapshot.
# INPUTS:
#   none.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0454 LocalBackend.snapshot() (references)
#   -> F0471 ApiBackend.snapshot() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def sap_snapshot() -> str:
    """SAP snapshot provenance and valid plant, material and supplier codes. Call first."""
    return _dump(get_backend().snapshot)


# ===== FUNCTION: factory_material_readiness() =====
# ID: F0487 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:42-45
# ROLE: MCP tool factory_material_readiness.
# INPUTS:
#   plant, material: str; quantity: float; need_by: str.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0455 LocalBackend.factory_readiness() (references)
#   -> F0472 ApiBackend.factory_readiness() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def factory_material_readiness(plant: str, material: str, quantity: float, need_by: str) -> str:
    """BOM material readiness for a production run (plant FR10/FR20/TPM1, finished good code, units, need date YYYY-MM-DD)."""
    return _dump(get_backend().factory_readiness, plant.upper(), material.upper(), quantity, need_by)


# ===== FUNCTION: warehouse_stock_balance() =====
# ID: F0488 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:48-51
# ROLE: MCP tool warehouse_stock_balance.
# INPUTS:
#   material: str, horizon_days: int, service_level: float.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0456 LocalBackend.stock_balance() (references)
#   -> F0473 ApiBackend.stock_balance() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def warehouse_stock_balance(material: str, horizon_days: int = 14, service_level: float = 0.95) -> str:
    """XGBoost demand forecast and OR-Tools transfer proposals across DC01, DC21 and DC22 for one finished good."""
    return _dump(get_backend().stock_balance, material.upper(), horizon_days, service_level)


# ===== FUNCTION: supplier_risk() =====
# ID: F0489 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:54-57
# ROLE: MCP tool supplier_risk.
# INPUTS:
#   supplier: str.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0458 LocalBackend.supplier_risk() (references)
#   -> F0475 ApiBackend.supplier_risk() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def supplier_risk(supplier: str) -> str:
    """Supplier scorecard: OTIF, delays, quality rejects, open PO exposure and single-source risk."""
    return _dump(get_backend().supplier_risk, supplier)


# ===== FUNCTION: quality_status() =====
# ID: F0490 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:60-63
# ROLE: MCP tool quality_status.
# INPUTS:
#   plant, material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0459 LocalBackend.quality_status() (references)
#   -> F0476 ApiBackend.quality_status() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def quality_status(plant: str = "", material: str = "") -> str:
    """Open inspection lots, blocked/expired batches and affected production orders."""
    return _dump(get_backend().quality_status, plant.upper() or None, material.upper() or None)


# ===== FUNCTION: logistics_status() =====
# ID: F0491 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:66-69
# ROLE: MCP tool logistics_status.
# INPUTS:
#   warehouse, material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0460 LocalBackend.logistics_status() (references)
#   -> F0477 ApiBackend.logistics_status() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def logistics_status(warehouse: str = "", material: str = "") -> str:
    """In-transit shipments, delays, revised ETAs and escalations."""
    return _dump(get_backend().logistics_status, warehouse.upper() or None, material.upper() or None)


# ===== FUNCTION: inventory_overview() =====
# ID: F0492 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:72-75
# ROLE: MCP tool inventory_overview.
# INPUTS:
#   material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0461 LocalBackend.inventory() (references)
#   -> F0478 ApiBackend.inventory() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def inventory_overview(material: str = "") -> str:
    """Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse."""
    return _dump(get_backend().inventory, material.upper() or None)


# ===== FUNCTION: sales_order_fulfilment() =====
# ID: F0493 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:78-81
# ROLE: MCP tool sales_order_fulfilment.
# INPUTS:
#   warehouse: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0462 LocalBackend.sales_orders() (references)
#   -> F0479 ApiBackend.sales_orders() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def sales_order_fulfilment(warehouse: str = "") -> str:
    """Open sales orders: on-time status, shortfalls and the cheapest on-time transfer or partial-delivery proposal."""
    return _dump(get_backend().sales_orders, warehouse.upper() or None)


# ===== FUNCTION: stocktake_reconciliation() =====
# ID: F0494 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:84-87
# ROLE: MCP tool stocktake_reconciliation.
# INPUTS:
#   tolerance_pct: float.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0463 LocalBackend.stocktake() (references)
#   -> F0480 ApiBackend.stocktake() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def stocktake_reconciliation(tolerance_pct: float = 1.0) -> str:
    """Explain stock count differences with evidence and recommend posting, adjustment or recount."""
    return _dump(get_backend().stocktake, tolerance_pct)


# ===== FUNCTION: search_governed_knowledge() =====
# ID: F0495 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:90-93
# ROLE: MCP tool search_governed_knowledge (top 5).
# INPUTS:
#   query: str, category: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0485 _dump() (calls)
#   -> F0464 LocalBackend.search_knowledge() (references)
#   -> F0481 ApiBackend.search_knowledge() (references)
#   -> F0484 get_backend() (calls)
@mcp.tool()
def search_governed_knowledge(query: str, category: str = "") -> str:
    """Search approved contracts, SOPs, quality policies, product specs and logistics policies. Category is optional."""
    return _dump(get_backend().search_knowledge, query, 5, category or None)


# ===== FUNCTION: health() =====
# ID: F0496 · route · used
# ORIGINAL FILE: backend/app/mcp_server.py:96-98
# ROLE: Open health endpoint (GET /health) with the number of registered tools.
# INPUTS:
#   _: Request (unused).
# OUTPUT:
#   JSONResponse.
# async def: Starlette awaits it; `await mcp.list_tools()` is an asynchronous call.
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "mcp", "tools": len(await mcp.list_tools())})


# ===== CLASS: ApiKeyMiddleware =====
# ID: F0497 · class · used
# ORIGINAL FILE: backend/app/mcp_server.py:101-114
# ROLE: ASGI middleware: requests to /mcp need a valid key (X-API-Key or Authorization: Bearer) from MCP_API_KEYS; /health is exempt;
#       no configured keys = open (local development).
# FIELDS:
#   keys: list[bytes].
# CALLED BY:
#   <- F0500 create_mcp_app() (references)
# CALLS:
#   (none found)
class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Bearer or X-API-Key check for /mcp; keys come from MCP_API_KEYS (comma separated)."""

    # ===== FUNCTION: ApiKeyMiddleware.__init__() =====
    # ID: F0498 · method · used (framework)
    # ORIGINAL FILE: backend/app/mcp_server.py:104-106
    # ROLE: Store the allowed keys as bytes (empty strings dropped).
    # INPUTS:
    #   app: ASGI app, keys: list[str].
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, app, keys: list[str]):
        super().__init__(app)
        self.keys = [key.encode() for key in keys if key]

    # ===== FUNCTION: ApiKeyMiddleware.dispatch() =====
    # ID: F0499 · method · used (framework)
    # ORIGINAL FILE: backend/app/mcp_server.py:108-114
    # ROLE: Check the key, then pass the request on (await call_next) or answer 401.
    # INPUTS:
    #   request: Request, call_next: async callable.
    # OUTPUT:
    #   Response.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health" or not self.keys:
            return await call_next(request)
        supplied = request.headers.get("x-api-key") or request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if supplied and any(hmac.compare_digest(supplied.encode(), key) for key in self.keys):
            return await call_next(request)
        return JSONResponse({"error": "missing or invalid MCP API key"}, status_code=401)


# ===== FUNCTION: create_mcp_app() =====
# ID: F0500 · function · used
# ORIGINAL FILE: backend/app/mcp_server.py:117-120
# ROLE: Build the Streamable-HTTP ASGI app with the API-key middleware.
# INPUTS:
#   none (reads MCP_API_KEYS).
# OUTPUT:
#   Starlette app.
# CALLED BY:
#   <- F0951 test_mcp_server_tools_health_and_auth() (calls)
# CALLS:
#   -> F0497 ApiKeyMiddleware (references)
def create_mcp_app():
    app = mcp.streamable_http_app()
    app.add_middleware(ApiKeyMiddleware, keys=os.environ.get("MCP_API_KEYS", "").split(","))
    return app


# Script entry point: `python -m backend.app.mcp_server` serves on MCP_PORT (default 8000).
if __name__ == "__main__":
    uvicorn.run(create_mcp_app(), host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
