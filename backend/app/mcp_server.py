"""Restricted MCP server (Streamable HTTP) exposing read-only SAP, analytics and RAG tools.

Consumed by the Flowise Chatflow / AgentFlow V2 (Custom MCP tool) and by the LangGraph MCP client.
Every tool calls the governed FastAPI gateway, so MCP calls are authenticated, audited and metered there.
"""
from __future__ import annotations

import hmac
import json
import os

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.copilot import get_backend

mcp = FastMCP(
    "aurelia-supply-chain-readonly",
    instructions="Read-only SAP S/4HANA mock, deterministic analytics and governed RAG. No tool can write to SAP.",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
)


def _dump(fn, *args) -> str:
    try:
        return json.dumps(fn(*args), default=str)[:12000]
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)[:600]})


@mcp.tool()
def sap_snapshot() -> str:
    """SAP snapshot provenance and valid plant, material and supplier codes. Call first."""
    return _dump(get_backend().snapshot)


@mcp.tool()
def factory_material_readiness(plant: str, material: str, quantity: float, need_by: str) -> str:
    """BOM material readiness for a production run (plant FR10/FR20/TPM1, finished good code, units, need date YYYY-MM-DD)."""
    return _dump(get_backend().factory_readiness, plant.upper(), material.upper(), quantity, need_by)


@mcp.tool()
def warehouse_stock_balance(material: str, horizon_days: int = 14, service_level: float = 0.95) -> str:
    """XGBoost demand forecast and OR-Tools transfer proposals across DC01, DC21 and DC22 for one finished good."""
    return _dump(get_backend().stock_balance, material.upper(), horizon_days, service_level)


@mcp.tool()
def supplier_risk(supplier: str) -> str:
    """Supplier scorecard: OTIF, delays, quality rejects, open PO exposure and single-source risk."""
    return _dump(get_backend().supplier_risk, supplier)


@mcp.tool()
def quality_status(plant: str = "", material: str = "") -> str:
    """Open inspection lots, blocked/expired batches and affected production orders."""
    return _dump(get_backend().quality_status, plant.upper() or None, material.upper() or None)


@mcp.tool()
def logistics_status(warehouse: str = "", material: str = "") -> str:
    """In-transit shipments, delays, revised ETAs and escalations."""
    return _dump(get_backend().logistics_status, warehouse.upper() or None, material.upper() or None)


@mcp.tool()
def inventory_overview(material: str = "") -> str:
    """Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse."""
    return _dump(get_backend().inventory, material.upper() or None)


@mcp.tool()
def sales_order_fulfilment(warehouse: str = "") -> str:
    """Open sales orders: on-time status, shortfalls and the cheapest on-time transfer or partial-delivery proposal."""
    return _dump(get_backend().sales_orders, warehouse.upper() or None)


@mcp.tool()
def stocktake_reconciliation(tolerance_pct: float = 1.0) -> str:
    """Explain stock count differences with evidence and recommend posting, adjustment or recount."""
    return _dump(get_backend().stocktake, tolerance_pct)


@mcp.tool()
def search_governed_knowledge(query: str, category: str = "") -> str:
    """Search approved contracts, SOPs, quality policies, product specs and logistics policies. Category is optional."""
    return _dump(get_backend().search_knowledge, query, 5, category or None)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "mcp", "tools": len(await mcp.list_tools())})


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Bearer or X-API-Key check for /mcp; keys come from MCP_API_KEYS (comma separated)."""

    def __init__(self, app, keys: list[str]):
        super().__init__(app)
        self.keys = [key.encode() for key in keys if key]

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health" or not self.keys:
            return await call_next(request)
        supplied = request.headers.get("x-api-key") or request.headers.get("authorization", "").removeprefix("Bearer ").strip()
        if supplied and any(hmac.compare_digest(supplied.encode(), key) for key in self.keys):
            return await call_next(request)
        return JSONResponse({"error": "missing or invalid MCP API key"}, status_code=401)


def create_mcp_app():
    app = mcp.streamable_http_app()
    app.add_middleware(ApiKeyMiddleware, keys=os.environ.get("MCP_API_KEYS", "").split(","))
    return app


if __name__ == "__main__":
    uvicorn.run(create_mcp_app(), host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
