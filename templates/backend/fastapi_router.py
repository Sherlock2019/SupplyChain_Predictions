"""TEMPLATE — ONE FastAPI app built from routers, the pattern of backend/app/main.py including backend/scinsight/app.py
(create_router) at /scinsight.

Run it:  uvicorn templates.backend.fastapi_router:create_app --factory --port 8201
  http://localhost:8201/health              the app's own route
  http://localhost:8201/inner/api/v1/...    a module's routes, included under a prefix (one Swagger: /docs)

Each module builds an APIRouter with its own dependencies (keys, roles, database); the app includes it under a prefix, so
route names never clash (both may define /health) and everything runs as one app, one process, one port.
"""
from __future__ import annotations

from types import SimpleNamespace

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException


def create_inner_router() -> APIRouter:
    """A module's routes and its shared objects (router.state), like backend/scinsight/app.py:create_router."""
    stock = {"SKU-001": 120.0}
    router = APIRouter()
    router.state = SimpleNamespace(stock=stock)

    def caller(x_api_key: str | None = Header(default=None)) -> str:  # this module's own authentication
        if x_api_key != "dev-inner-key":
            raise HTTPException(status_code=401, detail="Missing or invalid API key")
        return "inner-user"

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "module": "inner"}

    @router.get("/api/v1/stock/{sku}")
    def get_stock(sku: str, who: str = Depends(caller)) -> dict:
        if sku not in stock:
            raise HTTPException(status_code=404, detail="unknown sku")
        return {"sku": sku, "on_hand": stock[sku], "caller": who}

    return router


def create_app(inner: APIRouter | None = None) -> FastAPI:
    inner = inner or create_inner_router()  # tests pass their own router, as backend/app/main.py:create_app(scinsight_router=...)
    app = FastAPI(title="Template app", version="0.1.0")
    app.state.inner = inner.state

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "app"}

    # include BEFORE any catch-all mount (e.g. a static frontend at "/")
    app.include_router(inner, prefix="/inner", tags=["Inner module"])
    return app
