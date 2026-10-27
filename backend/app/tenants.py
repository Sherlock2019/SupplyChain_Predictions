"""Industry / customer tenants: one SAP snapshot and engine stack per customer, selected per request (X-Tenant header).

data/tenants/index.json lists industries and their customers (scripts/generate_tenants.py). The default tenant is the
original cosmetics demo (Settings.data_file). Engines are built lazily and cached; the active tenant for a request is held
in a ContextVar, so the existing endpoint code keeps using `sap`, `engine`, ... through thin proxies.
"""
from __future__ import annotations

import json
import threading
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from backend.app.config import ROOT
from backend.app.dashboards import Dashboards
from backend.app.engine import SupplyChainEngine
from backend.app.insights import InsightEngine
from backend.app.roles import RoleCenter
from backend.app.sap import SapRepository
from backend.app.store import Store

DEFAULT_TENANT = "cosmetics/aurelia"
_current: ContextVar[str] = ContextVar("tenant", default=DEFAULT_TENANT)


@dataclass
class TenantContext:
    id: str
    industry: str
    industry_label: str
    customer: str
    sap: SapRepository
    engine: SupplyChainEngine
    insights: InsightEngine
    dashboards: Dashboards
    roles: RoleCenter


class TenantRegistry:
    def __init__(self, default_file: Path, store: Store, index_file: Path | None = None):
        self.store = store
        self.index = {"default": DEFAULT_TENANT, "industries": {"cosmetics": {"label": "Cosmetics & beauty", "customers": []}}}
        index_file = index_file or ROOT / "data" / "tenants" / "index.json"
        if index_file.exists():
            self.index = json.loads(index_file.read_text(encoding="utf-8"))
        self.files: dict[str, Path] = {}
        self.labels: dict[str, tuple[str, str, str]] = {}
        for industry, info in self.index["industries"].items():
            for customer in info["customers"]:
                tid = f"{industry}/{customer['id']}"
                self.files[tid] = ROOT / customer["file"]
                self.labels[tid] = (industry, info["label"], customer["name"])
        self.files[DEFAULT_TENANT] = Path(default_file)  # the default always follows Settings.data_file (tests, deployments)
        self.labels.setdefault(DEFAULT_TENANT, ("cosmetics", "Cosmetics & beauty", "Aurelia Cosmetics"))
        self.builtin: dict[str, Path] = dict(self.files)  # each customer's own snapshot file (the Mock SAP connection)
        self._cache: dict[str, TenantContext] = {}
        self._lock = threading.Lock()

    def _build(self, tid: str, path: Path) -> TenantContext:
        sap = SapRepository(path)
        engine = SupplyChainEngine(sap)
        insights = InsightEngine(engine)
        industry, label, customer = self.labels[tid]
        dashboards = Dashboards(engine, insights, self.store)
        return TenantContext(tid, industry, label, customer, sap, engine, insights, dashboards, RoleCenter(engine, insights, self.store, dashboards, industry))

    def get(self, tenant_id: str | None = None) -> TenantContext:
        tid = tenant_id or _current.get()
        if tid not in self.files:
            raise ValueError(f"Unknown tenant {tid}. Options: {', '.join(sorted(self.files))}")
        with self._lock:
            if tid not in self._cache:
                self._cache[tid] = self._build(tid, self.files[tid])
            return self._cache[tid]

    def use_snapshot(self, tenant_id: str, path: Path | None) -> TenantContext:
        """Switch one customer to another validated snapshot file (None = its built-in snapshot): ERP activation and rollback.
        The new engine stack is built before the swap, so a failure leaves the current one untouched, and no other customer
        is affected."""
        path = Path(path) if path else self.builtin[tenant_id]
        ctx = self._build(tenant_id, path)
        with self._lock:
            self.files[tenant_id] = path
            self._cache[tenant_id] = ctx
        return ctx

    def catalogue(self) -> dict:
        return {"default": DEFAULT_TENANT, "industries": [
            {"id": industry, "label": info["label"],
             "customers": [{"id": f"{industry}/{c['id']}", "name": c["name"], "synthetic": c.get("synthetic", True)} for c in info["customers"]]}
            for industry, info in self.index["industries"].items()]}

    @staticmethod
    def activate(tenant_id: str | None):
        return _current.set(tenant_id or DEFAULT_TENANT)

    @staticmethod
    def deactivate(token) -> None:
        _current.reset(token)

    @staticmethod
    def current_id() -> str:
        return _current.get()


class TenantProxy:
    """Attribute access is forwarded to the active tenant's object (sap / engine / insights / dashboards / roles)."""

    def __init__(self, registry: TenantRegistry, attribute: str):
        object.__setattr__(self, "_registry", registry)
        object.__setattr__(self, "_attribute", attribute)

    def __getattr__(self, name):
        return getattr(getattr(self._registry.get(), self._attribute), name)
