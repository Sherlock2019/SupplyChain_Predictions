"""/api/v1/erp: the ERP / SAP Setup page's API. Reads for every signed-in role; changes, tests, syncs, activation and rollback
for managers only. The customer is the request's tenant (X-Tenant, already authorized by the gateway); connections of another
customer answer 404. Responses never contain secrets."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.app.auth import Principal
from backend.app.erp.checks import last_check, save_check, validate_integrations
from backend.app.erp.connectors import ErpError
from backend.app.erp.service import ConnectionIn, ErpService, MappingIn, options
from backend.app.tenants import TenantRegistry


class ActivateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sync_job_id: str | None = Field(default=None, max_length=40)


class PreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    section: str
    top: int = Field(default=5, ge=1, le=50)


class SyncIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retry_of: str | None = Field(default=None, max_length=40)


class ValidateAllIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deep: bool = False


def register(app: FastAPI, *, erp: ErpService, ctx: SimpleNamespace, reader: Callable, manager: Callable, audit: Callable[..., None]) -> None:
    tags = ["ERP / SAP Setup"]

    def tenant() -> str:
        return TenantRegistry.current_id()

    def run(fn: Callable[[], Any]) -> Any:
        try:
            return fn()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Not found for this customer: {exc.args[0]}") from exc
        except ErpError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def log(request: Request, who: Principal, action: str, **details) -> None:
        audit(who, f"erp.{action}", {"tenant": tenant(), **details}, request)

    @app.get("/api/v1/erp/providers", tags=tags)
    def providers(who: Principal = Depends(reader)) -> dict:
        del who
        return options()

    @app.get("/api/v1/erp/connections", tags=tags)
    def connections(who: Principal = Depends(reader)) -> dict:
        del who
        active = erp.active(tenant())
        return {"tenant": tenant(), "connections": erp.list(tenant()), "active": active, "snapshot": ctx.tenants.get(tenant()).sap.snapshot["id"]}

    @app.post("/api/v1/erp/connections", tags=tags, status_code=201)
    def create(body: ConnectionIn, request: Request, who: Principal = Depends(manager)) -> dict:
        conn = run(lambda: erp.create(tenant(), body, who.identity))
        log(request, who, "connection_created", connection_id=conn["id"], provider=body.provider, environment=body.environment, mode=body.mode)
        return conn

    @app.get("/api/v1/erp/connections/{conn_id}", tags=tags)
    def get(conn_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        return run(lambda: erp.get(tenant(), conn_id))

    @app.patch("/api/v1/erp/connections/{conn_id}", tags=tags)
    def patch(conn_id: str, request: Request, changes: dict = Body(...), who: Principal = Depends(manager)) -> dict:
        try:
            conn = run(lambda: erp.patch(tenant(), conn_id, changes, who.identity))
        except ValueError as exc:  # pydantic validation of the merged settings
            raise HTTPException(status_code=422, detail=str(exc)[:600]) from exc
        log(request, who, "connection_modified", connection_id=conn_id, version=conn["version"], fields=sorted(k for k in changes if k != "secret"),
            secret_changed="secret" in changes)
        return conn

    @app.post("/api/v1/erp/connections/{conn_id}/test", tags=tags)
    def test(conn_id: str, request: Request, who: Principal = Depends(manager)) -> dict:
        result = run(lambda: erp.test(tenant(), conn_id))
        log(request, who, "connection_tested", connection_id=conn_id, ok=result["ok"], error=result.get("error"))
        return result

    @app.get("/api/v1/erp/connections/{conn_id}/health", tags=tags)
    def health(conn_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        return run(lambda: erp.health(tenant(), conn_id))

    @app.get("/api/v1/erp/connections/{conn_id}/entities", tags=tags)
    def entities(conn_id: str, request: Request, who: Principal = Depends(manager)) -> dict:
        result = run(lambda: erp.discover(tenant(), conn_id))
        log(request, who, "entities_discovered", connection_id=conn_id)
        return result

    @app.get("/api/v1/erp/connections/{conn_id}/mappings", tags=tags)
    def mappings(conn_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        return {"mapping": {k: v.model_dump() for k, v in run(lambda: erp.mapping(tenant(), conn_id)).items()}}

    @app.put("/api/v1/erp/connections/{conn_id}/mappings", tags=tags)
    def put_mappings(conn_id: str, body: MappingIn, request: Request, who: Principal = Depends(manager)) -> dict:
        result = run(lambda: erp.set_mapping(tenant(), conn_id, body, who.identity))
        log(request, who, "mapping_changed", connection_id=conn_id, enabled=sorted(k for k, m in body.mapping.items() if m.enabled))
        return result

    @app.post("/api/v1/erp/connections/{conn_id}/validate", tags=tags)
    def validate(conn_id: str, request: Request, who: Principal = Depends(manager)) -> dict:
        result = run(lambda: erp.validate(tenant(), conn_id))
        log(request, who, "mapping_validated", connection_id=conn_id, valid=result["valid"], problems=len(result["problems"]))
        return result

    @app.post("/api/v1/erp/connections/{conn_id}/preview", tags=tags)
    def preview(conn_id: str, body: PreviewIn, request: Request, who: Principal = Depends(manager)) -> dict:
        result = run(lambda: erp.preview(tenant(), conn_id, body.section, body.top))
        log(request, who, "data_previewed", connection_id=conn_id, section=body.section, rows=len(result["rows"]))
        return result

    @app.post("/api/v1/erp/connections/{conn_id}/sync", tags=tags)
    def sync(conn_id: str, request: Request, body: SyncIn | None = None, who: Principal = Depends(manager)) -> dict:
        log(request, who, "sync_started", connection_id=conn_id, retry_of=body.retry_of if body else None)
        job = run(lambda: erp.sync(tenant(), conn_id, who.identity, body.retry_of if body else None))
        log(request, who, "sync_completed" if job["status"] == "validated" else "sync_failed", connection_id=conn_id, job=job["id"],
            counts=job["counts"], errors=len(job["errors"]))
        return job

    @app.get("/api/v1/erp/connections/{conn_id}/sync-history", tags=tags)
    def sync_history(conn_id: str, who: Principal = Depends(reader)) -> dict:
        del who
        return {"jobs": run(lambda: erp.sync_history(tenant(), conn_id))}

    @app.post("/api/v1/erp/connections/{conn_id}/activate", tags=tags)
    def activate(conn_id: str, request: Request, body: ActivateIn | None = None, who: Principal = Depends(manager)) -> dict:
        try:
            result = run(lambda: erp.activate(tenant(), conn_id, body.sync_job_id if body else None, who.identity))
        except HTTPException as exc:
            log(request, who, "activation_refused", connection_id=conn_id, reason=str(exc.detail)[:200])
            raise
        log(request, who, "connection_activated", connection_id=conn_id, job=result["sync_job_id"], snapshot=result["snapshot_id"],
            previous_snapshot=result["previous_snapshot_id"])
        return result

    @app.post("/api/v1/erp/connections/{conn_id}/rollback", tags=tags)
    def rollback(conn_id: str, request: Request, who: Principal = Depends(manager)) -> dict:
        run(lambda: erp.get(tenant(), conn_id))
        result = run(lambda: erp.rollback(tenant(), who.identity))
        log(request, who, "connection_rolled_back", connection_id=conn_id, snapshot=result["snapshot_id"], previous_snapshot=result["previous_snapshot_id"])
        return result

    @app.get("/api/v1/erp/connections/{conn_id}/logs", tags=tags)
    def logs(conn_id: str, limit: int = Query(default=100, ge=1, le=500), who: Principal = Depends(reader)) -> dict:
        del who
        return {"events": run(lambda: erp.logs(tenant(), conn_id, limit))}

    @app.get("/api/v1/erp/activation-history", tags=tags)
    def activation_history(who: Principal = Depends(reader)) -> dict:
        del who
        return {"history": erp.activation_history(tenant())}

    @app.get("/api/v1/erp/integration-status", tags=tags)
    def integration_status(who: Principal = Depends(reader)) -> dict:
        del who
        return {"tenant": tenant(), "snapshot": ctx.tenants.get(tenant()).sap.snapshot["id"], "last_check": last_check(ctx.store, tenant())}

    @app.post("/api/v1/erp/validate-integrations", tags=tags)
    def validate_all(request: Request, body: ValidateAllIn | None = None, who: Principal = Depends(manager)) -> dict:
        result = validate_integrations(ctx, tenant(), deep=bool(body and body.deep))
        save_check(ctx.store, tenant(), result, who.identity)
        log(request, who, "integrations_validated", ok=result["ok"], deep=result["deep"],
            results={r["component"]: r["status"] for r in result["results"]})
        return result
