"""TEMPLATE — a restricted MCP server (Streamable HTTP), the pattern of backend/app/mcp_server.py.

Run it:  TPL_MCP_KEYS=dev-mcp-key python -m templates.backend.mcp_server     (endpoint http://localhost:8202/mcp)

Rules kept from the real server: read-only tools only, typed parameters (the MCP client sees the schema), an API key on
every request, JSON results, and no tool that writes to SAP or approves anything.
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

mcp = FastMCP("template-tools", stateless_http=True)
STOCK = {"SKU-001": 120.0, "SKU-002": 8.0}  # stands in for an API / repository call


@mcp.tool()
def stock_level(sku: str) -> str:
    """Current on-hand quantity of one SKU (read-only)."""
    if sku not in STOCK:
        return json.dumps({"error": "unknown_sku", "sku": sku})
    return json.dumps({"sku": sku, "on_hand": STOCK[sku]})


@mcp.tool()
def low_stock(threshold: float = 10.0) -> str:
    """SKUs whose on-hand quantity is below the threshold (read-only)."""
    return json.dumps(sorted(s for s, q in STOCK.items() if q < threshold))


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Bearer or X-API-Key check on /mcp; keys come from TPL_MCP_KEYS (comma separated)."""

    def __init__(self, app, keys: list[str]):
        super().__init__(app)
        self.keys = [k for k in keys if k]

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            auth = request.headers.get("authorization", "")
            given = request.headers.get("x-api-key") or (auth[7:] if auth.lower().startswith("bearer ") else "")
            if not any(hmac.compare_digest(given.encode(), k.encode()) for k in self.keys):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def create_mcp_app():
    app = mcp.streamable_http_app()
    app.add_middleware(ApiKeyMiddleware, keys=os.environ.get("TPL_MCP_KEYS", "").split(","))
    return app


if __name__ == "__main__":
    uvicorn.run(create_mcp_app(), host="0.0.0.0", port=int(os.environ.get("TPL_MCP_PORT", "8202")))
