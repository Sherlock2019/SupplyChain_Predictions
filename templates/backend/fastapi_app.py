"""TEMPLATE — a governed FastAPI app, the pattern of backend/scinsight/app.py and backend/app/main.py.

Run it:  uvicorn templates.backend.fastapi_app:create_app --factory --port 8200   (Swagger: http://localhost:8200/docs)
Copy it to start a new backend service; replace the in-memory data with your repository / database.

What every route gets, as in the real apps:
  * an application factory (create_app) so tests build the app with their own settings
  * settings from environment variables (pydantic-settings), never hard-coded secrets
  * the caller identified from an API key; tenant and roles come from the key, never from the request body
  * one dependency per access level (reader / manager) and Pydantic models for every request body
  * read-only external data (writes answer 405) and an audit line for every state change
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TemplateSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TPL_", extra="ignore")

    # "key:identity:tenant:role,key2:..." — real apps keep hashed keys in a database (see backend/scinsight/security.py)
    api_keys: str = "dev-reader:alice:demo-tenant:reader,dev-manager:bob:demo-tenant:manager"


@dataclass(frozen=True)
class Principal:
    identity: str
    tenant: str
    role: str


class ItemRequest(BaseModel):
    """Request body: validated before the route runs (422 otherwise)."""
    sku: str = Field(pattern=r"^[A-Z0-9-]{3,20}$")
    quantity: float = Field(gt=0, le=1_000_000)


def create_app(settings: TemplateSettings | None = None) -> FastAPI:
    settings = settings or TemplateSettings()
    keys = {k: (ident, tenant, role) for k, ident, tenant, role in (row.split(":") for row in settings.api_keys.split(",") if row)}
    stock = {("demo-tenant", "SKU-001"): 120.0}  # stands in for a repository / database
    audit: list[dict] = []

    app = FastAPI(title="Template service", version="0.1.0")

    # ---- dependencies: authentication, then authorisation per access level
    def principal(x_api_key: str | None = Header(default=None)) -> Principal:
        for key, (ident, tenant, role) in keys.items():
            if x_api_key and hmac.compare_digest(x_api_key.encode(), key.encode()):  # constant-time comparison
                return Principal(ident, tenant, role)
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    def reader(p: Principal = Depends(principal)) -> Principal:
        return p

    def manager(p: Principal = Depends(principal)) -> Principal:
        if p.role != "manager":
            raise HTTPException(status_code=403, detail="Manager role required")
        return p

    # ---- routes
    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/v1/stock/{sku}")
    def get_stock(sku: str, p: Principal = Depends(reader)) -> dict:
        # tenant comes from the key: another tenant's rows are never read
        if (p.tenant, sku) not in stock:
            raise HTTPException(status_code=404, detail="unknown sku for your tenant")
        return {"tenant": p.tenant, "sku": sku, "on_hand": stock[(p.tenant, sku)]}

    @app.post("/api/v1/adjustments", status_code=201)
    def adjust(body: ItemRequest, p: Principal = Depends(manager)) -> dict:
        stock[(p.tenant, body.sku)] = stock.get((p.tenant, body.sku), 0.0) + body.quantity
        audit.append({"actor": p.identity, "action": "stock.adjusted", "sku": body.sku, "quantity": body.quantity})
        return {"sku": body.sku, "on_hand": stock[(p.tenant, body.sku)]}

    @app.api_route("/api/v1/sap/{path:path}", methods=["POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    def sap_read_only(path: str, p: Principal = Depends(principal)) -> dict:
        raise HTTPException(status_code=405, detail="SAP is read-only")

    @app.get("/api/v1/audit")
    def read_audit(p: Principal = Depends(manager)) -> list[dict]:
        return audit

    return app
