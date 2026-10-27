"""ERP connections per customer: configuration (versioned), secrets (server-side only), mappings, staged synchronization,
validated activation and rollback.

Activation is the only thing that changes what SPARC computes on: it swaps the customer's snapshot in the TenantRegistry, so every
FastAPI business service — and therefore every Flowise and LangGraph tool, which call those services — uses it on the next call.
A sync never activates; a failed sync or test never touches the active snapshot.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from backend.app.engine import SupplyChainEngine
from backend.app.erp.connectors import (
    MODES,
    PROVIDERS,
    ErpConnector,
    ErpError,
    MockSapConnector,
    SapODataConnector,
    check_destination,
)
from backend.app.erp.mapping import REQUIRED_SECTIONS, SECTIONS, SectionMapping, default_mapping, validate_mapping
from backend.app.sap import SapRepository
from backend.app.store import Store
from backend.app.tenants import TenantRegistry

log = logging.getLogger(__name__)

SCHEMA = [
    """create table if not exists erp_connection (id text primary key, tenant text not null, name text not null, provider text not null,
       config text not null, version integer not null, status text not null, last_test text, last_test_at text, last_test_ok integer,
       mapping_valid integer, created_by text not null, created_at text not null, updated_by text not null, updated_at text not null)""",
    """create table if not exists erp_connection_version (id text primary key, connection_id text not null, version integer not null,
       config text not null, changed_by text not null, changed_at text not null)""",
    "create table if not exists erp_secret (connection_id text primary key, value text not null, updated_at text not null)",
    """create table if not exists erp_entity_mapping (connection_id text primary key, version integer not null, mapping text not null,
       updated_by text not null, updated_at text not null)""",
    """create table if not exists erp_sync_job (id text primary key, tenant text not null, connection_id text not null, connection_version integer not null,
       status text not null, snapshot_id text, snapshot text, counts text, errors text, warnings text, carried text, actor text not null,
       retry_of text, started_at text not null, finished_at text)""",
    """create table if not exists erp_activation_history (id text primary key, tenant text not null, connection_id text, sync_job_id text,
       snapshot_id text not null, action text not null, previous_snapshot_id text, actor text not null, at text not null)""",
    """create table if not exists erp_integration_check (id text primary key, tenant text not null, ok integer not null, result text not null,
       actor text not null, at text not null)""",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectionIn(BaseModel):
    """Connection settings. `secret` is write-only (only with secret_ref="stored"); it is never returned."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    provider: Literal["mock_sap", "sap_s4hana", "sap_ecc", "generic_rest"] = "mock_sap"
    environment: Literal["development", "staging", "production"] = "development"
    mode: Literal["mock", "read_only_live", "approved_write"] = "mock"
    protocol: Literal["snapshot", "odata_v2", "odata_v4", "rest"] = "snapshot"
    base_url: str = Field(default="", max_length=300)
    sap_client: str = Field(default="", pattern=r"^(\d{3})?$")
    auth: Literal["none", "basic", "oauth2_client_credentials", "api_key"] = "none"
    username: str = Field(default="", max_length=120)
    client_id: str = Field(default="", max_length=200)
    token_url: str = Field(default="", max_length=300)
    secret_ref: str = Field(default="", pattern=r"^(env:[A-Z][A-Z0-9_]{1,63}|stored)?$", description="env:NAME (secrets manager) or stored")
    secret: str | None = Field(default=None, max_length=4000)
    verify_tls: bool = True
    timeout_seconds: int = Field(default=15, ge=3, le=60)
    sync_mode: Literal["manual", "scheduled", "event"] = "manual"
    sync_interval_minutes: int = Field(default=1440, ge=15, le=10080)


class MappingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mapping: dict[str, SectionMapping]


class ErpService:
    def __init__(self, store: Store, tenants: TenantRegistry, *, environment: str, allowed_hosts: str = "",
                 transport: httpx.BaseTransport | None = None, snapshot_dir: Path | None = None):
        self.store, self.tenants, self.transport = store, tenants, transport
        self.allow_http = environment in ("development", "test")
        self.allowed_hosts = {h.strip().lower() for h in allowed_hosts.split(",") if h.strip()}
        self.snapshot_dir = Path(snapshot_dir or Path(tempfile.gettempdir()) / "sparc-erp")
        self._db = store._db
        for statement in SCHEMA:
            self._db.query(statement, fetch="none")
        self._lock = threading.Lock()

    # ------------------------------------------------------------ rows
    def _row(self, tenant: str, conn_id: str) -> dict:
        row = self._db.query("select * from erp_connection where id=? and tenant=?", (conn_id, tenant), fetch="one")
        if row is None:  # also what another customer's connection id gives: no existence leak across tenants
            raise KeyError(conn_id)
        return {**row, "config": json.loads(row["config"]), "last_test": json.loads(row["last_test"]) if row["last_test"] else None}

    def _secret(self, conn: dict) -> tuple[str, str]:
        """(secret, source). env:NAME reads the variable a secrets manager injects; stored reads the write-only table."""
        ref = conn["config"].get("secret_ref", "")
        if ref.startswith("env:"):
            return os.environ.get(ref[4:], ""), ref
        if ref == "stored":
            row = self._db.query("select value from erp_secret where connection_id=?", (conn["id"],), fetch="one")
            return (row["value"] if row else ""), "stored"
        return "", ""

    def public(self, conn: dict) -> dict:
        secret, source = self._secret(conn)
        return {"id": conn["id"], "tenant": conn["tenant"], "name": conn["name"], "provider": conn["provider"], "version": conn["version"],
                "status": conn["status"], "config": conn["config"], "secret_set": bool(secret), "secret_source": source,
                "last_test": conn["last_test"], "last_test_at": conn["last_test_at"], "mapping_valid": None if conn["mapping_valid"] is None else bool(conn["mapping_valid"]),
                "created_by": conn["created_by"], "created_at": conn["created_at"], "updated_by": conn["updated_by"], "updated_at": conn["updated_at"]}

    def list(self, tenant: str) -> list[dict]:
        rows = self._db.query("select id from erp_connection where tenant=? order by created_at", (tenant,))
        return [self.public(self._row(tenant, r["id"])) for r in rows]

    def get(self, tenant: str, conn_id: str) -> dict:
        return self.public(self._row(tenant, conn_id))

    # ------------------------------------------------------------ configuration
    def _rules(self, body: ConnectionIn) -> None:
        provider = PROVIDERS[body.provider]
        if not provider["available"]:
            raise ErpError(provider["reason"])
        if not MODES[body.mode]["available"]:
            raise ErpError(MODES[body.mode]["description"])
        if body.mode not in provider["modes"]:
            raise ErpError(f"{provider['label']} supports mode {', '.join(provider['modes'])}")
        if body.protocol not in provider["protocols"]:
            raise ErpError(f"{provider['label']} supports protocol {', '.join(provider['protocols'])}")
        if body.sync_mode == "event":
            raise ErpError("Event-driven sync needs an SAP Event Mesh subscription; not supported yet (use manual or scheduled)")
        if body.provider == "mock_sap":
            return
        if not body.base_url:
            raise ErpError("SAP base URL is required")
        for url in filter(None, (body.base_url, body.token_url)):
            check_destination(url, environment=body.environment, allowed_hosts=self.allowed_hosts, allow_http=self.allow_http)
        if body.auth == "none":
            raise ErpError("Live connections need authentication")
        if body.environment == "production":
            if not body.verify_tls:
                raise ErpError("TLS verification cannot be disabled for production")
            if not body.secret_ref.startswith("env:"):
                raise ErpError("Production secrets must come from a secrets manager (secret reference env:NAME)")
        if not body.secret_ref:
            raise ErpError("Choose a secret reference (env:NAME or stored)")

    def _save(self, tenant: str, conn_id: str | None, body: ConnectionIn, actor: str) -> dict:
        self._rules(body)
        config = body.model_dump(exclude={"secret", "name", "provider"})
        config["base_url"] = config["base_url"].rstrip("/")
        now = _now()
        with self._lock:
            if conn_id is None:
                conn_id = f"ERP-{uuid.uuid4().hex[:8].upper()}"
                version = 1
                self._db.query("insert into erp_connection(id,tenant,name,provider,config,version,status,created_by,created_at,updated_by,updated_at) values(?,?,?,?,?,?,?,?,?,?,?)",
                               (conn_id, tenant, body.name, body.provider, json.dumps(config), version, "draft", actor, now, actor, now), fetch="none")
                if body.provider != "mock_sap":
                    self._db.query("insert into erp_entity_mapping(connection_id,version,mapping,updated_by,updated_at) values(?,?,?,?,?)",
                                   (conn_id, 1, json.dumps({k: v.model_dump() for k, v in default_mapping().items()}), actor, now), fetch="none")
            else:
                current = self._row(tenant, conn_id)
                version = current["version"] + 1
                # a changed configuration must be tested again before it can be activated; the active snapshot stays as is
                status = current["status"] if current["status"] == "active" else "draft"
                self._db.query("update erp_connection set name=?, provider=?, config=?, version=?, status=?, last_test_ok=null, mapping_valid=null, updated_by=?, updated_at=? where id=? and tenant=?",
                               (body.name, body.provider, json.dumps(config), version, status, actor, now, conn_id, tenant), fetch="none")
            self._db.query("insert into erp_connection_version(id,connection_id,version,config,changed_by,changed_at) values(?,?,?,?,?,?)",
                           (uuid.uuid4().hex, conn_id, version, json.dumps({"name": body.name, "provider": body.provider, **config}), actor, now), fetch="none")
            if body.secret_ref == "stored" and body.secret is not None:
                self._db.run([("delete from erp_secret where connection_id=?", (conn_id,)),
                              ("insert into erp_secret(connection_id,value,updated_at) values(?,?,?)", (conn_id, body.secret, now))])
            elif body.secret_ref != "stored":
                self._db.query("delete from erp_secret where connection_id=?", (conn_id,), fetch="none")
        return self.get(tenant, conn_id)

    def create(self, tenant: str, body: ConnectionIn, actor: str) -> dict:
        return self._save(tenant, None, body, actor)

    def patch(self, tenant: str, conn_id: str, changes: dict, actor: str) -> dict:
        current = self._row(tenant, conn_id)
        merged = {"name": current["name"], "provider": current["provider"], **current["config"], **changes}
        return self._save(tenant, conn_id, ConnectionIn(**merged), actor)

    # ------------------------------------------------------------ connector
    def connector(self, tenant: str, conn: dict) -> ErpConnector:
        if conn["provider"] == "mock_sap":
            return MockSapConnector(self.tenants.builtin[tenant])
        cfg = conn["config"]
        check_destination(cfg["base_url"], environment=cfg["environment"], allowed_hosts=self.allowed_hosts, allow_http=self.allow_http)
        secret, _ = self._secret(conn)
        if not secret:
            raise ErpError("No secret available for this connection (set the env variable or store a secret)")
        return SapODataConnector(conn["provider"], cfg, secret, transport=self.transport)

    def mapping(self, tenant: str, conn_id: str) -> dict[str, SectionMapping]:
        self._row(tenant, conn_id)
        row = self._db.query("select mapping from erp_entity_mapping where connection_id=?", (conn_id,), fetch="one")
        return {k: SectionMapping(**v) for k, v in json.loads(row["mapping"]).items()} if row else {}

    def set_mapping(self, tenant: str, conn_id: str, body: MappingIn, actor: str) -> dict:
        conn = self._row(tenant, conn_id)
        if conn["provider"] == "mock_sap":
            raise ErpError("The Mock SAP snapshot is already in SPARC's shape; it has no mapping")
        unknown = set(body.mapping) - set(SECTIONS)
        if unknown:
            raise ErpError(f"Unknown SPARC sections: {sorted(unknown)}")
        now = _now()
        self._db.run([("delete from erp_entity_mapping where connection_id=?", (conn_id,)),
                      ("insert into erp_entity_mapping(connection_id,version,mapping,updated_by,updated_at) values(?,?,?,?,?)",
                       (conn_id, conn["version"], json.dumps({k: v.model_dump() for k, v in body.mapping.items()}), actor, now)),
                      ("update erp_connection set mapping_valid=null, updated_by=?, updated_at=? where id=?", (actor, now, conn_id))])
        return {"mapping": {k: v.model_dump() for k, v in self.mapping(tenant, conn_id).items()}, "problems": validate_mapping(self.mapping(tenant, conn_id))}

    # ------------------------------------------------------------ test / discover / validate / preview
    def test(self, tenant: str, conn_id: str) -> dict:
        conn = self._row(tenant, conn_id)
        try:
            connector = self.connector(tenant, conn)
            result = connector.test_connection(self.mapping(tenant, conn_id)) if isinstance(connector, SapODataConnector) else connector.test_connection()
        except ErpError as exc:
            result = {"ok": False, "error": str(exc), "checks": [], "auth": "unknown", "latency_ms": None}
        status = conn["status"] if conn["status"] == "active" else ("tested" if result["ok"] else "failed")
        self._db.query("update erp_connection set last_test=?, last_test_at=?, last_test_ok=?, status=? where id=?",
                       (json.dumps(result), _now(), int(result["ok"]), status, conn_id), fetch="none")
        return {**result, "activated": False, "note": "A successful test never activates the connection."}

    def discover(self, tenant: str, conn_id: str) -> dict:
        conn = self._row(tenant, conn_id)
        return {"provider": conn["provider"], "entities": self.connector(tenant, conn).discover_entities(self.mapping(tenant, conn_id))}

    def validate(self, tenant: str, conn_id: str) -> dict:
        conn = self._row(tenant, conn_id)
        problems = self.connector(tenant, conn).validate_mapping(self.mapping(tenant, conn_id))
        self._db.query("update erp_connection set mapping_valid=? where id=?", (int(not problems), conn_id), fetch="none")
        return {"valid": not problems, "problems": problems}

    def preview(self, tenant: str, conn_id: str, section: str, top: int) -> dict:
        if section not in SECTIONS:
            raise ErpError(f"Unknown SPARC section {section}")
        conn = self._row(tenant, conn_id)
        return self.connector(tenant, conn).read_entity(section, self.mapping(tenant, conn_id), top)

    # ------------------------------------------------------------ sync (staging + validation; never activates)
    def sync(self, tenant: str, conn_id: str, actor: str, retry_of: str | None = None) -> dict:
        conn = self._row(tenant, conn_id)
        job_id = f"SYNC-{uuid.uuid4().hex[:10].upper()}"
        started = _now()
        self._db.query("insert into erp_sync_job(id,tenant,connection_id,connection_version,status,actor,retry_of,started_at) values(?,?,?,?,?,?,?,?)",
                       (job_id, tenant, conn_id, conn["version"], "running", actor, retry_of, started), fetch="none")
        errors: list[str] = []
        try:
            base = json.loads(Path(self.tenants.files[tenant]).read_text(encoding="utf-8"))
            result = self.connector(tenant, conn).sync_data(base, self.mapping(tenant, conn_id))
            data, errors = result["snapshot"], list(result["errors"])
            if conn["provider"] != "mock_sap":
                data["snapshot"] = {**base["snapshot"], "id": f"ERP-{conn_id[4:]}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
                                    "source_system": f"{conn['provider']}:{conn['name']}", "extracted_at": _now(), "as_of_date": date.today().isoformat(),
                                    "read_only": True, "erp_connection": conn_id, "erp_sync_job": job_id, "carried_sections": result["carried"]}
            for section in REQUIRED_SECTIONS:
                if not data.get(section):
                    errors.append(f"{SECTIONS[section]['label']}: no rows — the engine cannot run without them")
            if not errors:
                errors += self._smoke(data, job_id)
        except (ErpError, httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            errors.append(str(exc)[:300])
            data, result = None, {"counts": {}, "warnings": [], "carried": []}
        status = "failed" if errors else "validated"
        self._db.query("update erp_sync_job set status=?, snapshot_id=?, snapshot=?, counts=?, errors=?, warnings=?, carried=?, finished_at=? where id=?",
                       (status, data["snapshot"]["id"] if data and not errors else None, json.dumps(data) if data and not errors else None,
                        json.dumps(result["counts"]), json.dumps(errors[:200]), json.dumps(result["warnings"]), json.dumps(result["carried"]), _now(), job_id), fetch="none")
        return self.job(tenant, job_id)

    def _smoke(self, data: dict, job_id: str) -> list[str]:
        """The candidate must load and the engine must compute on it before it can ever be activated."""
        path = self._write(data, f"staging-{job_id}")
        try:
            engine = SupplyChainEngine(SapRepository(path))
            engine.kpis()
            engine.production_overview()
            engine.position_health()
            engine.network_map()
            return []
        except Exception as exc:  # noqa: BLE001 - any failure blocks activation
            return [f"Validation: the business engine failed on this data: {type(exc).__name__}: {str(exc)[:200]}"]
        finally:
            path.unlink(missing_ok=True)

    def _write(self, data: dict, name: str) -> Path:
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.snapshot_dir / f"{name}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def job(self, tenant: str, job_id: str) -> dict:
        row = self._db.query("select * from erp_sync_job where id=? and tenant=?", (job_id, tenant), fetch="one")
        if row is None:
            raise KeyError(job_id)
        return {k: (json.loads(row[k]) if row[k] else ([] if k in ("errors", "warnings", "carried") else {})) if k in ("counts", "errors", "warnings", "carried") else row[k]
                for k in row if k != "snapshot"}

    def sync_history(self, tenant: str, conn_id: str) -> list[dict]:
        self._row(tenant, conn_id)
        rows = self._db.query("select id from erp_sync_job where connection_id=? and tenant=? order by started_at desc limit 50", (conn_id, tenant))
        return [self.job(tenant, r["id"]) for r in rows]

    # ------------------------------------------------------------ activation / rollback
    def active(self, tenant: str) -> dict | None:
        return self._db.query("select * from erp_activation_history where tenant=? order by at desc limit 1", (tenant,), fetch="one")

    def activate(self, tenant: str, conn_id: str, job_id: str | None, actor: str) -> dict:
        conn = self._row(tenant, conn_id)
        if not conn["last_test_ok"]:
            raise ErpError("Test the connection successfully (current configuration version) before activating it")
        if conn["provider"] == "mock_sap":
            ctx = self.tenants.use_snapshot(tenant, None)
            job = None
        else:
            if not conn["mapping_valid"]:
                raise ErpError("Validate the entity mapping before activating")
            row = (self._db.query("select * from erp_sync_job where id=? and tenant=? and connection_id=?", (job_id, tenant, conn_id), fetch="one") if job_id else
                   self._db.query("select * from erp_sync_job where tenant=? and connection_id=? and status in ('validated','activated') order by started_at desc limit 1",
                                  (tenant, conn_id), fetch="one"))
            if row is None or row["status"] not in ("validated", "activated") or not row["snapshot"]:
                raise ErpError("No validated synchronization to activate: run a sync first")
            if row["connection_version"] != conn["version"]:
                raise ErpError("That sync was made with an older configuration version: sync again")
            ctx = self._swap(tenant, row["id"], row["snapshot"])
            job = row["id"]
        return self._record(tenant, conn_id, job, ctx.sap.snapshot["id"], "activate", actor)

    def _swap(self, tenant: str, job_id: str, snapshot_json: str):
        path = self._write(json.loads(snapshot_json), f"{tenant.replace('/', '__')}-{job_id}")
        return self.tenants.use_snapshot(tenant, path)  # raises (and keeps the current snapshot) if it does not load

    def _record(self, tenant: str, conn_id: str | None, job_id: str | None, snapshot_id: str, action: str, actor: str) -> dict:
        previous = self.active(tenant)
        now = _now()
        self._db.run([("insert into erp_activation_history(id,tenant,connection_id,sync_job_id,snapshot_id,action,previous_snapshot_id,actor,at) values(?,?,?,?,?,?,?,?,?)",
                       (uuid.uuid4().hex, tenant, conn_id, job_id, snapshot_id, action, previous["snapshot_id"] if previous else None, actor, now)),
                      ("update erp_connection set status='inactive' where tenant=? and status='active'", (tenant,)),
                      *([("update erp_connection set status='active' where id=?", (conn_id,))] if conn_id else []),
                      *([("update erp_sync_job set status='activated' where id=?", (job_id,))] if job_id else [])])
        return {"tenant": tenant, "connection_id": conn_id, "sync_job_id": job_id, "snapshot_id": snapshot_id, "action": action,
                "previous_snapshot_id": previous["snapshot_id"] if previous else None, "at": now}

    def rollback(self, tenant: str, actor: str) -> dict:
        """Back to the snapshot that was active before the current one (or the customer's built-in snapshot)."""
        history = self._db.query("select * from erp_activation_history where tenant=? order by at desc limit 2", (tenant,))
        if not history:
            raise ErpError("Nothing to roll back: the built-in snapshot is active")
        target = history[1] if len(history) > 1 else None
        if target and target["sync_job_id"]:
            row = self._db.query("select snapshot from erp_sync_job where id=?", (target["sync_job_id"],), fetch="one")
            ctx = self._swap(tenant, target["sync_job_id"], row["snapshot"])
        else:
            ctx = self.tenants.use_snapshot(tenant, None)
        conn_id = target["connection_id"] if target else None
        return self._record(tenant, conn_id, target["sync_job_id"] if target else None, ctx.sap.snapshot["id"], "rollback", actor)

    def activation_history(self, tenant: str) -> list[dict]:
        return self._db.query("select * from erp_activation_history where tenant=? order by at desc limit 50", (tenant,))

    def restore(self) -> None:
        """At startup: put every customer back on its last activated snapshot (the database is the source of truth)."""
        for tenant in list(self.tenants.files):
            last = self.active(tenant)
            if not last or not last["sync_job_id"]:
                continue
            row = self._db.query("select snapshot from erp_sync_job where id=?", (last["sync_job_id"],), fetch="one")
            try:
                self._swap(tenant, last["sync_job_id"], row["snapshot"])
            except Exception as exc:  # noqa: BLE001 - keep the built-in snapshot rather than fail startup
                log.error("ERP snapshot %s for %s could not be restored: %s", last["snapshot_id"], tenant, exc)

    # ------------------------------------------------------------ health
    def health(self, tenant: str, conn_id: str) -> dict:
        conn = self._row(tenant, conn_id)
        test = conn["last_test"] or {}
        ok_job = self._db.query("select * from erp_sync_job where connection_id=? and status in ('validated','activated') order by started_at desc limit 1", (conn_id,), fetch="one")
        mapping = self.mapping(tenant, conn_id)
        active = self.active(tenant)
        snap = self.tenants.get(tenant).sap.snapshot
        status = "not_configured" if conn["last_test_ok"] is None and not test else "connected" if conn["last_test_ok"] else "error" if test.get("error") else "disconnected"
        last_ok = self._db.query("select at from erp_activation_history where connection_id=? order by at desc limit 1", (conn_id,), fetch="one")
        return {"connection_id": conn_id, "status": status, "provider": conn["provider"], "environment": conn["config"]["environment"], "mode": conn["config"]["mode"],
                "active": conn["status"] == "active", "system": test.get("system"), "last_test_at": conn["last_test_at"], "last_test_ok": conn["last_test_ok"],
                "auth": test.get("auth"), "latency_ms": test.get("latency_ms"), "last_error": test.get("error"),
                "last_sync_at": ok_job["finished_at"] if ok_job else None, "records_synced": sum(json.loads(ok_job["counts"]).values()) if ok_job and ok_job["counts"] else 0,
                "mapped_entities": sum(1 for m in mapping.values() if m.enabled) if mapping else len([s for s in SECTIONS]),
                "last_activated_at": last_ok["at"] if last_ok else None,
                "tenant_snapshot": {"id": snap["id"], "source_system": snap.get("source_system"), "extracted_at": snap.get("extracted_at"), "age_hours": snap.get("age_hours"),
                                    "activated_by_erp": bool(active)}}

    def logs(self, tenant: str, conn_id: str, limit: int = 100) -> list[dict]:
        self._row(tenant, conn_id)
        return [e for e in self.store.audit_events(1000) if e["action"].startswith("erp.") and e["details"].get("connection_id") == conn_id][:limit]

    # ------------------------------------------------------------ scheduled sync (staging only)
    def run_scheduled(self) -> int:
        ran = 0
        for row in self._db.query("select id, tenant, config from erp_connection"):
            cfg = json.loads(row["config"])
            if cfg.get("sync_mode") != "scheduled":
                continue
            last = self._db.query("select started_at from erp_sync_job where connection_id=? order by started_at desc limit 1", (row["id"],), fetch="one")
            due = not last or datetime.fromisoformat(last["started_at"]) + timedelta(minutes=cfg.get("sync_interval_minutes", 1440)) <= datetime.now(timezone.utc)
            if due:
                job = self.sync(row["tenant"], row["id"], "erp-scheduler")
                self.store.audit("erp-scheduler", "system", "erp.sync_completed" if job["status"] == "validated" else "erp.sync_failed",
                                 {"connection_id": row["id"], "tenant": row["tenant"], "job": job["id"], "scheduled": True})
                ran += 1
        return ran

    def start_scheduler(self, every_seconds: int = 60) -> None:
        def loop() -> None:
            while True:
                try:
                    self.run_scheduled()
                except Exception as exc:  # noqa: BLE001
                    log.warning("ERP scheduler: %s", exc)
                threading.Event().wait(every_seconds)
        threading.Thread(target=loop, name="erp-scheduler", daemon=True).start()


def options() -> dict[str, Any]:
    return {"providers": PROVIDERS, "modes": MODES, "sections": {k: {**v, "optional": list(v["optional"])} for k, v in SECTIONS.items()},
            "environments": ["development", "staging", "production"], "auth": ["none", "basic", "oauth2_client_credentials", "api_key"],
            "sync_modes": {"manual": True, "scheduled": True, "event": False}}
