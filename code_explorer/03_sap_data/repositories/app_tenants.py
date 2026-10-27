# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/tenants.py
# What this module is: multi-tenancy of the SPARC gateway. Each industry / customer has its own SAP snapshot and engine stack
# (SapRepository -> SupplyChainEngine -> InsightEngine / Dashboards / RoleCenter), built lazily and cached. The active tenant of
# a request lives in a ContextVar set by the request middleware; TenantProxy forwards attribute access to that tenant's object.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Industry / customer tenants: one SAP snapshot and engine stack per customer, selected per request (X-Tenant header).

data/tenants/index.json lists industries and their customers (scripts/generate_tenants.py). The default tenant is the
original cosmetics demo (Settings.data_file). Engines are built lazily and cached; the active tenant for a request is held
in a ContextVar, so the existing endpoint code keeps using `sap`, `engine`, ... through thin proxies.
"""
from __future__ import annotations

import json
import threading
# ContextVar: a variable whose value is local to the current request / asyncio task (safe under concurrency).
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
# The active tenant id of the current request (default: the cosmetics demo).
_current: ContextVar[str] = ContextVar("tenant", default=DEFAULT_TENANT)


# ===== CLASS: TenantContext =====
# ID: F0390 · class · used
# ORIGINAL FILE: backend/app/tenants.py:27-37
# ROLE: Everything that belongs to one tenant: identity labels + its SAP repository and engines.
# FIELDS:
#   id, industry, industry_label, customer, sap, engine, insights, dashboards, roles.
# CALLED BY:
#   <- F0392 TenantRegistry.__init__() (references)
#   <- F0393 TenantRegistry.get() (calls)
#   <- F0393 TenantRegistry.get() (references)
# CALLS:
#   (none found)
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


# ===== CLASS: TenantRegistry =====
# ID: F0391 · class · used
# ORIGINAL FILE: backend/app/tenants.py:40-90
# ROLE: Registry of tenants (from data/tenants/index.json + the default file) with a lazily filled, thread-safe cache.
# FIELDS:
#   store, index, files {tenant_id: Path}, labels {tenant_id: (industry, label, customer)}, _cache, _lock.
# CALLED BY:
#   <- F0017 create_app() (calls)
#   <- F0018 create_app.request_context() (references)
#   <- F0019 create_app.principal() (references)
#   <- F0022 create_app.watch_owner() (references)
#   <- F0034 create_app.tenant_catalogue() (references)
#   <- F0057 create_app.moat_view() (references)
#   <- F0058 create_app.moat_consent() (references)
#   <- F0251 MoatEngine.__init__() (references)
#   <- F0399 TenantProxy.__init__() (references)
# CALLS:
#   (none found)
class TenantRegistry:
    # ===== FUNCTION: TenantRegistry.__init__() =====
    # ID: F0392 · method · used (framework)
    # ORIGINAL FILE: backend/app/tenants.py:41-57
    # ROLE: Read the tenant index and map every tenant id to its snapshot file and labels.
    # INPUTS:
    #   default_file: Path (Settings.data_file), store: Store, index_file: Path | None.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0354 Store (references)
    #   -> F0390 TenantContext (references)
    def __init__(self, default_file: Path, store: Store, index_file: Path | None = None):
        self.store = store
        # Fallback index when no tenants file exists (only the default cosmetics tenant).
        self.index = {"default": DEFAULT_TENANT, "industries": {"cosmetics": {"label": "Cosmetics & beauty", "customers": []}}}
        index_file = index_file or ROOT / "data" / "tenants" / "index.json"
        if index_file.exists():
            self.index = json.loads(index_file.read_text(encoding="utf-8"))
        self.files: dict[str, Path] = {}
        self.labels: dict[str, tuple[str, str, str]] = {}
        for industry, info in self.index["industries"].items():
            for customer in info["customers"]:
                # Tenant id = "industry/customer", e.g. "pharma/northwind".
                tid = f"{industry}/{customer['id']}"
                self.files[tid] = ROOT / customer["file"]
                self.labels[tid] = (industry, info["label"], customer["name"])
        self.files[DEFAULT_TENANT] = Path(default_file)  # the default always follows Settings.data_file (tests, deployments)
        self.labels.setdefault(DEFAULT_TENANT, ("cosmetics", "Cosmetics & beauty", "Aurelia Cosmetics"))
        self._cache: dict[str, TenantContext] = {}
        self._lock = threading.Lock()

    # ===== FUNCTION: TenantRegistry.get() =====
    # ID: F0393 · method · used
    # ORIGINAL FILE: backend/app/tenants.py:59-72
    # ROLE: The TenantContext of a tenant (default: the request's active tenant), building its engine stack on first use.
    # INPUTS:
    #   tenant_id: str | None.
    # OUTPUT:
    #   TenantContext (ValueError for an unknown tenant).
    # CALLED BY:
    #   <- F1791 CodeEditor.list() (calls)
    #   <- F0017 create_app() (calls)
    #   <- F0033 create_app.snapshot() (calls)
    #   <- F0253 MoatEngine._series() (calls)
    #   <- F0254 MoatEngine.model_comparison() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    #   <- F1822 register.cfg_of() (calls)
    #   <- F1892 build_candidate_index() (calls)
    #   <- F1895 validate_config() (calls)
    #   <- F1897 _activate() (calls)
    #   <- F1898 publish_rag_config() (calls)
    #   <- F1899 rollback_rag_config() (calls)
    # CALLS:
    #   -> F0401 SapRepository (calls)
    #   -> F0192 SupplyChainEngine (calls)
    #   -> F0244 InsightEngine (calls)
    #   -> F0229 Dashboards (calls)
    #   -> F0390 TenantContext (calls)
    #   -> F0259 RoleCenter (calls)
    #   -> F0390 TenantContext (references)
    def get(self, tenant_id: str | None = None) -> TenantContext:
        tid = tenant_id or _current.get()
        if tid not in self.files:
            raise ValueError(f"Unknown tenant {tid}. Options: {', '.join(sorted(self.files))}")
        # The lock prevents two concurrent requests from building the same tenant twice.
        with self._lock:
            if tid not in self._cache:
                # Dependency chain: SAP data -> engine -> insights / dashboards / role center.
                sap = SapRepository(self.files[tid])
                engine = SupplyChainEngine(sap)
                insights = InsightEngine(engine)
                industry, label, customer = self.labels[tid]
                dashboards = Dashboards(engine, insights, self.store)
                self._cache[tid] = TenantContext(tid, industry, label, customer, sap, engine, insights, dashboards,
                                                 RoleCenter(engine, insights, self.store, dashboards, industry))
            return self._cache[tid]

    # ===== FUNCTION: TenantRegistry.catalogue() =====
    # ID: F0394 · method · used
    # ORIGINAL FILE: backend/app/tenants.py:74-78
    # ROLE: Industries and customers for the UI tenant selector.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict -> {"default", "industries": [{id, label, customers: [{id, name, synthetic}]}]}.
    # CALLED BY:
    #   <- F0034 create_app.tenant_catalogue() (calls)
    # CALLS:
    #   (none found)
    def catalogue(self) -> dict:
        return {"default": DEFAULT_TENANT, "industries": [
            {"id": industry, "label": info["label"],
             "customers": [{"id": f"{industry}/{c['id']}", "name": c["name"], "synthetic": c.get("synthetic", True)} for c in info["customers"]]}
            for industry, info in self.index["industries"].items()]}

    # ===== FUNCTION: TenantRegistry.activate() =====
    # ID: F0395 · method · used
    # ORIGINAL FILE: backend/app/tenants.py:80-82
    # ROLE: Set the active tenant for the current request; returns a token to restore the previous value.
    # INPUTS:
    #   tenant_id: str | None.
    # OUTPUT:
    #   contextvars.Token.
    # CALLED BY:
    #   <- F0018 create_app.request_context() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def activate(tenant_id: str | None):
        return _current.set(tenant_id or DEFAULT_TENANT)

    # ===== FUNCTION: TenantRegistry.deactivate() =====
    # ID: F0396 · method · used
    # ORIGINAL FILE: backend/app/tenants.py:84-86
    # ROLE: Restore the previous tenant (end of the request).
    # INPUTS:
    #   token.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0018 create_app.request_context() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def deactivate(token) -> None:
        _current.reset(token)

    # ===== FUNCTION: TenantRegistry.current_id() =====
    # ID: F0397 · method · used
    # ORIGINAL FILE: backend/app/tenants.py:88-90
    # ROLE: Id of the active tenant.
    # INPUTS:
    #   none.
    # OUTPUT:
    #   str.
    # CALLED BY:
    #   <- F0019 create_app.principal() (calls)
    #   <- F0022 create_app.watch_owner() (calls)
    #   <- F0034 create_app.tenant_catalogue() (calls)
    #   <- F0057 create_app.moat_view() (calls)
    #   <- F0058 create_app.moat_consent() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def current_id() -> str:
        return _current.get()


# ===== CLASS: TenantProxy =====
# ID: F0398 · class · used
# ORIGINAL FILE: backend/app/tenants.py:93-101
# ROLE: Thin proxy: `engine.stock_balance(...)` in main.py becomes `registry.get().engine.stock_balance(...)` for the active tenant.
# FIELDS:
#   _registry: TenantRegistry, _attribute: str ("sap" | "engine" | "insights" | "dashboards" | "roles").
# CALLED BY:
#   <- F0017 create_app() (calls)
# CALLS:
#   (none found)
class TenantProxy:
    """Attribute access is forwarded to the active tenant's object (sap / engine / insights / dashboards / roles)."""

    # ===== FUNCTION: TenantProxy.__init__() =====
    # ID: F0399 · method · used (framework)
    # ORIGINAL FILE: backend/app/tenants.py:96-98
    # ROLE: Store registry and attribute name without triggering __getattr__.
    # INPUTS:
    #   registry: TenantRegistry, attribute: str.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0391 TenantRegistry (references)
    def __init__(self, registry: TenantRegistry, attribute: str):
        # object.__setattr__ bypasses any custom attribute logic of this class.
        object.__setattr__(self, "_registry", registry)
        object.__setattr__(self, "_attribute", attribute)

    # ===== FUNCTION: TenantProxy.__getattr__() =====
    # ID: F0400 · method · used (framework)
    # ORIGINAL FILE: backend/app/tenants.py:100-101
    # ROLE: Called only for attributes NOT found normally: forward to the active tenant's object.
    # INPUTS:
    #   name: str -> attribute requested (e.g. "factory_readiness").
    # OUTPUT:
    #   the attribute of the tenant's sap/engine/... object.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __getattr__(self, name):
        return getattr(getattr(self._registry.get(), self._attribute), name)
