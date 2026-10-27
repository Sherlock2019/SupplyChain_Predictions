# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/copilot.py
# What this module is: the single governed backend used by every agent runtime of the SPARC gateway (LangGraph graphs, Deep Agent,
# MCP tools). In deployments (COPILOT_API_URL set) agents call the FastAPI gateway over HTTP (ApiBackend), so the same API keys,
# audit chain, metrics and analysis ids apply; in unit tests they use the in-process engine (LocalBackend).
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""One governed backend for every agent runtime (LangGraph, Deep Agents, MCP).

Deployments set COPILOT_API_URL so agents call the FastAPI gateway over HTTP: the same API keys, audit chain,
metrics and stored analysis IDs apply to agent calls as to the dashboard. Unit tests use the in-process engine.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
# Protocol: structural interface (any class with these methods qualifies; no inheritance needed).
from typing import Any, Protocol

import httpx

from backend.app.config import Settings, get_settings
from backend.app.engine import SupplyChainEngine
from backend.app.rag import MemoryRag, create_rag
from backend.app.sap import SapRepository
from backend.app.store import Store


# ===== CLASS: CopilotBackend =====
# ID: F0438 · class · used
# ORIGINAL FILE: backend/app/copilot.py:21-33
# ROLE: The interface every agent tool relies on (implemented by LocalBackend and ApiBackend). "..." = no body (declaration only).
# FIELDS:
#   methods: snapshot, factory_readiness, stock_balance, demand_forecast, supplier_risk, quality_status, logistics_status,
#            inventory, sales_orders, stocktake, search_knowledge, submit_recommendation.
# CALLED BY:
#   <- F0483 build_backend() (references)
#   <- F0484 get_backend() (references)
# CALLS:
#   (none found)
class CopilotBackend(Protocol):
    def snapshot(self) -> dict: ...
    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: str) -> dict: ...
    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict: ...
    def demand_forecast(self, material: str, warehouse: str | None = None, horizon_days: int = 14) -> dict: ...
    def supplier_risk(self, supplier: str) -> dict: ...
    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict: ...
    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict: ...
    def inventory(self, material: str | None = None) -> dict: ...
    def sales_orders(self, warehouse: str | None = None) -> dict: ...
    def stocktake(self, tolerance_pct: float = 1.0) -> dict: ...
    def search_knowledge(self, query: str, top_k: int = 4, category: str | None = None) -> dict: ...
    def submit_recommendation(self, analysis_id: str, explanation: str) -> dict: ...


# ===== CLASS: LocalBackend =====
# ID: F0451 · class · used
# ORIGINAL FILE: backend/app/copilot.py:36-92
# ROLE: In-process backend: engine + RAG + its own ledger; every analysis is stored and returned with an analysis_id.
# FIELDS:
#   sap, engine, rag, store, actor.
# CALLED BY:
#   <- F0483 build_backend() (calls)
# CALLS:
#   (none found)
class LocalBackend:
    """In-process engine with its own ledger. Used by unit tests and when no gateway URL is configured."""

    # ===== FUNCTION: LocalBackend.__init__() =====
    # ID: F0452 · method · used (framework)
    # ORIGINAL FILE: backend/app/copilot.py:39-44
    # ROLE: Build the engine on the SAP repository; default ledger = in-memory store.
    # INPUTS:
    #   sap: SapRepository, rag, store: Store | None, actor: str.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0401 SapRepository (references)
    #   -> F0354 Store (references)
    #   -> F0192 SupplyChainEngine (calls)
    #   -> F0356 Store.memory() (calls)
    def __init__(self, sap: SapRepository, rag: Any, store: Store | None = None, actor: str = "langgraph"):
        self.sap = sap
        self.engine = SupplyChainEngine(sap)
        self.rag = rag
        self.store = store or Store.memory()
        self.actor = actor

    # ===== FUNCTION: LocalBackend._save() =====
    # ID: F0453 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:46-48
    # ROLE: Store an analysis and return it in the gateway's response shape (analysis_id + snapshot + read_only + result).
    # INPUTS:
    #   kind: str, request: dict, result: dict.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0455 LocalBackend.factory_readiness() (calls)
    #   <- F0456 LocalBackend.stock_balance() (calls)
    #   <- F0457 LocalBackend.demand_forecast() (calls)
    #   <- F0458 LocalBackend.supplier_risk() (calls)
    #   <- F0459 LocalBackend.quality_status() (calls)
    #   <- F0460 LocalBackend.logistics_status() (calls)
    #   <- F0462 LocalBackend.sales_orders() (calls)
    #   <- F0463 LocalBackend.stocktake() (calls)
    # CALLS:
    #   -> F0361 Store.save_analysis() (calls)
    #   -> F0405 SapRepository.snapshot() (references)
    def _save(self, kind: str, request: dict, result: dict) -> dict:
        analysis_id = self.store.save_analysis(kind, request, result, self.sap.snapshot["id"], self.actor)
        return {"analysis_id": analysis_id, "snapshot": self.sap.snapshot, "read_only": True, **result}

    # ===== FUNCTION: LocalBackend.snapshot() =====
    # ID: F0454 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:50-56
    # ROLE: Snapshot provenance + valid plants, materials and supplier names (agents call it first to learn valid codes).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0541 sap_read() (calls)
    #   <- F0590 validate() (calls)
    #   <- F0486 sap_snapshot() (references)
    #   <- F0503 sap_snapshot() (references)
    # CALLS:
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0407 SapRepository.section() (calls)
    def snapshot(self) -> dict:
        return {
            **self.sap.snapshot,
            "plants": self.sap.section("plants"),
            "materials": self.sap.section("materials"),
            "suppliers": [s["name"] for s in self.sap.section("suppliers")],
        }

    # ===== FUNCTION: LocalBackend.factory_readiness() =====
    # ID: F0455 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:58-60
    # ROLE: Engine factory readiness (need_by given as an ISO string by the agent), stored.
    # INPUTS:
    #   plant, material: str; quantity: float; need_by: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0592 run_factory() (calls)
    #   <- F0487 factory_material_readiness() (references)
    #   <- F0504 factory_material_readiness() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0197 SupplyChainEngine.factory_readiness() (calls)
    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: str) -> dict:
        request = {"plant": plant, "material": material, "quantity": quantity, "need_by": need_by}
        return self._save("factory_readiness", request, self.engine.factory_readiness(plant, material, float(quantity), date.fromisoformat(need_by)))

    # ===== FUNCTION: LocalBackend.stock_balance() =====
    # ID: F0456 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:62-64
    # ROLE: Engine stock balancing, stored.
    # INPUTS:
    #   material: str, horizon_days: int, service_level: float.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0593 run_balance() (calls)
    #   <- F0488 warehouse_stock_balance() (references)
    #   <- F0505 warehouse_stock_balance() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0198 SupplyChainEngine.stock_balance() (calls)
    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict:
        request = {"material": material, "horizon_days": horizon_days, "service_level": service_level}
        return self._save("stock_balance", request, self.engine.stock_balance(material, int(horizon_days), float(service_level)))

    # ===== FUNCTION: LocalBackend.demand_forecast() =====
    # ID: F0457 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:66-68
    # ROLE: Engine demand forecast, stored.
    # INPUTS:
    #   material: str, warehouse: str | None, horizon_days: int.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0506 demand_forecast() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0199 SupplyChainEngine.demand_forecast() (calls)
    def demand_forecast(self, material: str, warehouse: str | None = None, horizon_days: int = 14) -> dict:
        request = {"material": material, "warehouse": warehouse, "horizon_days": horizon_days}
        return self._save("forecast", request, self.engine.demand_forecast(material, warehouse, int(horizon_days)))

    # ===== FUNCTION: LocalBackend.supplier_risk() =====
    # ID: F0458 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:70-71
    # ROLE: Engine supplier risk, stored.
    # INPUTS:
    #   supplier: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0594 run_supplier() (calls)
    #   <- F0489 supplier_risk() (references)
    #   <- F0507 supplier_risk() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0201 SupplyChainEngine.supplier_risk() (calls)
    def supplier_risk(self, supplier: str) -> dict:
        return self._save("supplier_risk", {"supplier": supplier}, self.engine.supplier_risk(supplier))

    # ===== FUNCTION: LocalBackend.quality_status() =====
    # ID: F0459 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:73-74
    # ROLE: Engine quality status, stored.
    # INPUTS:
    #   plant, material: str | None.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0595 run_quality() (calls)
    #   <- F0490 quality_status() (references)
    #   <- F0508 quality_status() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0203 SupplyChainEngine.quality_status() (calls)
    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict:
        return self._save("quality_status", {"plant": plant, "material": material}, self.engine.quality_status(plant, material))

    # ===== FUNCTION: LocalBackend.logistics_status() =====
    # ID: F0460 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:76-77
    # ROLE: Engine logistics status, stored.
    # INPUTS:
    #   warehouse, material: str | None.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0596 run_logistics() (calls)
    #   <- F0491 logistics_status() (references)
    #   <- F0509 logistics_status() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0204 SupplyChainEngine.logistics_status() (calls)
    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict:
        return self._save("logistics_status", {"warehouse": warehouse, "material": material}, self.engine.logistics_status(warehouse, material))

    # ===== FUNCTION: LocalBackend.inventory() =====
    # ID: F0461 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:79-80
    # ROLE: Inventory overview (not stored: no proposed actions).
    # INPUTS:
    #   material: str | None.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0597 run_inventory() (calls)
    #   <- F0492 inventory_overview() (references)
    #   <- F0510 inventory_overview() (references)
    # CALLS:
    #   -> F0405 SapRepository.snapshot() (references)
    #   -> F0205 SupplyChainEngine.inventory_overview() (calls)
    def inventory(self, material: str | None = None) -> dict:
        return {"snapshot": self.sap.snapshot, **self.engine.inventory_overview(material)}

    # ===== FUNCTION: LocalBackend.sales_orders() =====
    # ID: F0462 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:82-83
    # ROLE: Sales-order fulfilment, stored.
    # INPUTS:
    #   warehouse: str | None.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0493 sales_order_fulfilment() (references)
    #   <- F0511 sales_order_fulfilment() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    def sales_orders(self, warehouse: str | None = None) -> dict:
        return self._save("sales_order_fulfilment", {"warehouse": warehouse}, self.engine.sales_order_fulfilment(warehouse))

    # ===== FUNCTION: LocalBackend.stocktake() =====
    # ID: F0463 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:85-86
    # ROLE: Stocktake reconciliation, stored.
    # INPUTS:
    #   tolerance_pct: float.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0494 stocktake_reconciliation() (references)
    #   <- F0512 stocktake_reconciliation() (references)
    # CALLS:
    #   -> F0453 LocalBackend._save() (calls)
    #   -> F0207 SupplyChainEngine.stocktake_reconciliation() (calls)
    def stocktake(self, tolerance_pct: float = 1.0) -> dict:
        return self._save("stocktake_reconciliation", {"tolerance_pct": tolerance_pct}, self.engine.stocktake_reconciliation(tolerance_pct))

    # ===== FUNCTION: LocalBackend.search_knowledge() =====
    # ID: F0464 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:88-89
    # ROLE: Governed RAG search.
    # INPUTS:
    #   query: str, top_k: int, category: str | None.
    # OUTPUT:
    #   dict -> {"query", "results"}.
    # CALLED BY:
    #   <- F0542 rag_retrieve() (calls)
    #   <- F0598 policy_context() (calls)
    #   <- F0495 search_governed_knowledge() (references)
    #   <- F0513 search_governed_knowledge() (references)
    # CALLS:
    #   -> F0746 MemoryRag.search() (calls)
    #   -> F0755 PgVectorRag.search() (calls)
    def search_knowledge(self, query: str, top_k: int = 4, category: str | None = None) -> dict:
        return {"query": query, "results": self.rag.search(query, top_k, category)}

    # ===== FUNCTION: LocalBackend.submit_recommendation() =====
    # ID: F0465 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:91-92
    # ROLE: Submit a stored analysis to the review queue (source "langgraph").
    # INPUTS:
    #   analysis_id: str, explanation: str.
    # OUTPUT:
    #   dict -> recommendation.
    # CALLED BY:
    #   <- F0552 approval_gate() (calls)
    #   <- F0603 submit() (calls)
    # CALLS:
    #   -> F0364 Store.submit() (calls)
    def submit_recommendation(self, analysis_id: str, explanation: str) -> dict:
        return self.store.submit(analysis_id, explanation, self.actor, source="langgraph")


# ===== CLASS: ApiError =====
# ID: F0466 · class · used
# ORIGINAL FILE: backend/app/copilot.py:95-96
# ROLE: Error raised by ApiBackend when the gateway answers >= 400 (the message carries method, path, status and detail).
# FIELDS:
#   (message only).
# CALLED BY:
#   <- F0469 ApiBackend._call() (calls)
# CALLS:
#   (none found)
class ApiError(RuntimeError):
    pass


# ===== CLASS: ApiBackend =====
# ID: F0467 · class · used
# ORIGINAL FILE: backend/app/copilot.py:99-153
# ROLE: HTTP backend: each method calls one gateway endpoint with the agent's API key (authenticated, audited, metered by the gateway).
# FIELDS:
#   _client: httpx.Client (base URL + X-API-Key header).
# CALLED BY:
#   <- F0483 build_backend() (calls)
# CALLS:
#   (none found)
class ApiBackend:
    """HTTP client for the FastAPI gateway; every call is authenticated and audited by the gateway."""

    # ===== FUNCTION: ApiBackend.__init__() =====
    # ID: F0468 · method · used (framework)
    # ORIGINAL FILE: backend/app/copilot.py:102-103
    # ROLE: Create the HTTP client.
    # INPUTS:
    #   base_url: str, api_key: str, timeout: float.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, base_url: str, api_key: str, timeout: float = 60):
        self._client = httpx.Client(base_url=base_url.rstrip("/"), headers={"X-API-Key": api_key}, timeout=timeout)

    # ===== FUNCTION: ApiBackend._call() =====
    # ID: F0469 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:105-113
    # ROLE: Send a request; >= 400 raises ApiError with the gateway's detail; else return the JSON body.
    # INPUTS:
    #   method: str, path: str, **kwargs (json=..., params=...).
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0471 ApiBackend.snapshot() (calls)
    #   <- F0472 ApiBackend.factory_readiness() (calls)
    #   <- F0473 ApiBackend.stock_balance() (calls)
    #   <- F0474 ApiBackend.demand_forecast() (calls)
    #   <- F0475 ApiBackend.supplier_risk() (calls)
    #   <- F0476 ApiBackend.quality_status() (calls)
    #   <- F0477 ApiBackend.logistics_status() (calls)
    #   <- F0478 ApiBackend.inventory() (calls)
    #   <- F0479 ApiBackend.sales_orders() (calls)
    #   <- F0480 ApiBackend.stocktake() (calls)
    #   <- F0481 ApiBackend.search_knowledge() (calls)
    #   <- F0482 ApiBackend.submit_recommendation() (calls)
    # CALLS:
    #   -> F0466 ApiError (calls)
    def _call(self, method: str, path: str, **kwargs) -> dict:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise ApiError(f"{method} {path} -> {response.status_code}: {detail}")
        return response.json()

    # ===== FUNCTION: ApiBackend._clean() =====
    # ID: F0470 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:115-117
    # ROLE: Drop None / empty values so the strict gateway schemas do not receive empty optional fields.
    # INPUTS:
    #   payload: dict.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0474 ApiBackend.demand_forecast() (calls)
    #   <- F0476 ApiBackend.quality_status() (calls)
    #   <- F0477 ApiBackend.logistics_status() (calls)
    #   <- F0478 ApiBackend.inventory() (calls)
    #   <- F0479 ApiBackend.sales_orders() (calls)
    #   <- F0481 ApiBackend.search_knowledge() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _clean(payload: dict) -> dict:
        return {key: value for key, value in payload.items() if value not in (None, "")}

    # ===== FUNCTION: ApiBackend.snapshot() =====
    # ID: F0471 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:119-120
    # ROLE: GET /api/v1/snapshot.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0541 sap_read() (calls)
    #   <- F0590 validate() (calls)
    #   <- F0486 sap_snapshot() (references)
    #   <- F0503 sap_snapshot() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0033 create_app.snapshot() (http_request)
    def snapshot(self) -> dict:
        return self._call("GET", "/api/v1/snapshot")

    # ===== FUNCTION: ApiBackend.factory_readiness() =====
    # ID: F0472 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:122-123
    # ROLE: POST /api/v1/analysis/factory-readiness.
    # INPUTS:
    #   plant, material, quantity, need_by.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0592 run_factory() (calls)
    #   <- F0487 factory_material_readiness() (references)
    #   <- F0504 factory_material_readiness() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0040 create_app.factory_readiness() (http_request)
    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: str) -> dict:
        return self._call("POST", "/api/v1/analysis/factory-readiness", json={"plant": plant, "material": material, "quantity": quantity, "need_by": need_by})

    # ===== FUNCTION: ApiBackend.stock_balance() =====
    # ID: F0473 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:125-126
    # ROLE: POST /api/v1/analysis/stock-balance.
    # INPUTS:
    #   material, horizon_days, service_level.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0593 run_balance() (calls)
    #   <- F0488 warehouse_stock_balance() (references)
    #   <- F0505 warehouse_stock_balance() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0041 create_app.stock_balance() (http_request)
    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict:
        return self._call("POST", "/api/v1/analysis/stock-balance", json={"material": material, "horizon_days": horizon_days, "service_level": service_level})

    # ===== FUNCTION: ApiBackend.demand_forecast() =====
    # ID: F0474 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:128-129
    # ROLE: POST /api/v1/analysis/forecast.
    # INPUTS:
    #   material, warehouse, horizon_days.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0506 demand_forecast() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0042 create_app.demand_forecast() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def demand_forecast(self, material: str, warehouse: str | None = None, horizon_days: int = 14) -> dict:
        return self._call("POST", "/api/v1/analysis/forecast", json=self._clean({"material": material, "warehouse": warehouse, "horizon_days": horizon_days}))

    # ===== FUNCTION: ApiBackend.supplier_risk() =====
    # ID: F0475 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:131-132
    # ROLE: POST /api/v1/analysis/supplier-risk.
    # INPUTS:
    #   supplier.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0594 run_supplier() (calls)
    #   <- F0489 supplier_risk() (references)
    #   <- F0507 supplier_risk() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0044 create_app.supplier_risk() (http_request)
    def supplier_risk(self, supplier: str) -> dict:
        return self._call("POST", "/api/v1/analysis/supplier-risk", json={"supplier": supplier})

    # ===== FUNCTION: ApiBackend.quality_status() =====
    # ID: F0476 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:134-135
    # ROLE: POST /api/v1/analysis/quality.
    # INPUTS:
    #   plant, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0595 run_quality() (calls)
    #   <- F0490 quality_status() (references)
    #   <- F0508 quality_status() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0045 create_app.quality() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/quality", json=self._clean({"plant": plant, "material": material}))

    # ===== FUNCTION: ApiBackend.logistics_status() =====
    # ID: F0477 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:137-138
    # ROLE: POST /api/v1/analysis/logistics.
    # INPUTS:
    #   warehouse, material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0596 run_logistics() (calls)
    #   <- F0491 logistics_status() (references)
    #   <- F0509 logistics_status() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0046 create_app.logistics() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/logistics", json=self._clean({"warehouse": warehouse, "material": material}))

    # ===== FUNCTION: ApiBackend.inventory() =====
    # ID: F0478 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:140-141
    # ROLE: GET /api/v1/inventory (query parameter material).
    # INPUTS:
    #   material.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0597 run_inventory() (calls)
    #   <- F0492 inventory_overview() (references)
    #   <- F0510 inventory_overview() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0073 create_app.inventory() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def inventory(self, material: str | None = None) -> dict:
        return self._call("GET", "/api/v1/inventory", params=self._clean({"material": material}))

    # ===== FUNCTION: ApiBackend.sales_orders() =====
    # ID: F0479 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:143-144
    # ROLE: POST /api/v1/analysis/sales-orders.
    # INPUTS:
    #   warehouse.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0493 sales_order_fulfilment() (references)
    #   <- F0511 sales_order_fulfilment() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0047 create_app.sales_orders() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def sales_orders(self, warehouse: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/sales-orders", json=self._clean({"warehouse": warehouse}))

    # ===== FUNCTION: ApiBackend.stocktake() =====
    # ID: F0480 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:146-147
    # ROLE: POST /api/v1/analysis/stocktake.
    # INPUTS:
    #   tolerance_pct.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0494 stocktake_reconciliation() (references)
    #   <- F0512 stocktake_reconciliation() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0048 create_app.stocktake() (http_request)
    def stocktake(self, tolerance_pct: float = 1.0) -> dict:
        return self._call("POST", "/api/v1/analysis/stocktake", json={"tolerance_pct": tolerance_pct})

    # ===== FUNCTION: ApiBackend.search_knowledge() =====
    # ID: F0481 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:149-150
    # ROLE: POST /api/v1/rag/search.
    # INPUTS:
    #   query, top_k, category.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0542 rag_retrieve() (calls)
    #   <- F0598 policy_context() (calls)
    #   <- F0495 search_governed_knowledge() (references)
    #   <- F0513 search_governed_knowledge() (references)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0076 create_app.rag_search() (http_request)
    #   -> F0077 create_app.rag_search_get() (http_request)
    #   -> F2014 create_router.rag_search() (http_request)
    #   -> F0470 ApiBackend._clean() (calls)
    def search_knowledge(self, query: str, top_k: int = 4, category: str | None = None) -> dict:
        return self._call("POST", "/api/v1/rag/search", json=self._clean({"query": query, "top_k": top_k, "category": category}))

    # ===== FUNCTION: ApiBackend.submit_recommendation() =====
    # ID: F0482 · method · used
    # ORIGINAL FILE: backend/app/copilot.py:152-153
    # ROLE: POST /api/v1/recommendations (source "langgraph").
    # INPUTS:
    #   analysis_id, explanation.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0552 approval_gate() (calls)
    #   <- F0603 submit() (calls)
    # CALLS:
    #   -> F0469 ApiBackend._call() (calls)
    #   -> F0095 create_app.submit_recommendation() (http_request)
    #   -> F0097 create_app.recommendations() (http_request)
    def submit_recommendation(self, analysis_id: str, explanation: str) -> dict:
        return self._call("POST", "/api/v1/recommendations", json={"analysis_id": analysis_id, "explanation": explanation, "source": "langgraph"})


# ===== FUNCTION: build_backend() =====
# ID: F0483 · function · used
# ORIGINAL FILE: backend/app/copilot.py:156-165
# ROLE: Choose the backend: ApiBackend when COPILOT_API_URL is set; else LocalBackend (RAG falls back to in-memory if pgvector fails,
#       so graphs stay loadable in Studio without PostgreSQL).
# INPUTS:
#   settings: Settings, actor: str.
# OUTPUT:
#   CopilotBackend.
# CALLED BY:
#   <- F0484 get_backend() (calls)
# CALLS:
#   -> F0001 Settings (references)
#   -> F0467 ApiBackend (calls)
#   -> F0401 SapRepository (calls)
#   -> F0756 create_rag() (calls)
#   -> F0743 MemoryRag (calls)
#   -> F0748 MemoryRag.load_directory() (calls)
#   -> F0754 PgVectorRag.load_directory() (calls)
#   -> F0451 LocalBackend (calls)
#   -> F0438 CopilotBackend (references)
def build_backend(settings: Settings, actor: str = "langgraph") -> CopilotBackend:
    if settings.copilot_api_url:
        return ApiBackend(settings.copilot_api_url, settings.copilot_api_key)
    sap = SapRepository(settings.data_file)
    try:
        rag = create_rag(settings.rag_backend, settings.postgres_url, settings.knowledge_dir, settings.embedding_backend, settings.embedding_model)
    except Exception:  # noqa: BLE001 - offline fallback keeps graphs loadable for Studio without Postgres
        rag = MemoryRag()
        rag.load_directory(settings.knowledge_dir)
    return LocalBackend(sap, rag, actor=actor)


# ===== FUNCTION: get_backend() =====
# ID: F0484 · function · used
# ORIGINAL FILE: backend/app/copilot.py:168-170
# ROLE: Process-wide cached backend used by tools.py, mcp_server.py, graphs and the deep agent.
# INPUTS:
#   none.
# OUTPUT:
#   CopilotBackend.
# CALLED BY:
#   <- F0541 sap_read() (calls)
#   <- F0542 rag_retrieve() (calls)
#   <- F0548 _deterministic() (calls)
#   <- F0552 approval_gate() (calls)
#   <- F0583 fallback_answer() (calls)
#   <- F0590 validate() (calls)
#   <- F0592 run_factory() (calls)
#   <- F0593 run_balance() (calls)
#   <- F0594 run_supplier() (calls)
#   <- F0595 run_quality() (calls)
#   <- F0596 run_logistics() (calls)
#   <- F0597 run_inventory() (calls)
# CALLS:
#   -> F0483 build_backend() (calls)
#   -> F0008 get_settings() (calls)
#   -> F0438 CopilotBackend (references)
@lru_cache
def get_backend() -> CopilotBackend:
    return build_backend(get_settings())
