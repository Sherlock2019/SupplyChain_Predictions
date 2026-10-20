"""One governed backend for every agent runtime (LangGraph, Deep Agents, MCP).

Deployments set COPILOT_API_URL so agents call the FastAPI gateway over HTTP: the same API keys, audit chain,
metrics and stored analysis IDs apply to agent calls as to the dashboard. Unit tests use the in-process engine.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Any, Protocol

import httpx

from backend.app.config import Settings, get_settings
from backend.app.engine import SupplyChainEngine
from backend.app.rag import MemoryRag, create_rag
from backend.app.sap import SapRepository
from backend.app.store import Store


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


class LocalBackend:
    """In-process engine with its own ledger. Used by unit tests and when no gateway URL is configured."""

    def __init__(self, sap: SapRepository, rag: Any, store: Store | None = None, actor: str = "langgraph"):
        self.sap = sap
        self.engine = SupplyChainEngine(sap)
        self.rag = rag
        self.store = store or Store.memory()
        self.actor = actor

    def _save(self, kind: str, request: dict, result: dict) -> dict:
        analysis_id = self.store.save_analysis(kind, request, result, self.sap.snapshot["id"], self.actor)
        return {"analysis_id": analysis_id, "snapshot": self.sap.snapshot, "read_only": True, **result}

    def snapshot(self) -> dict:
        return {
            **self.sap.snapshot,
            "plants": self.sap.section("plants"),
            "materials": self.sap.section("materials"),
            "suppliers": [s["name"] for s in self.sap.section("suppliers")],
        }

    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: str) -> dict:
        request = {"plant": plant, "material": material, "quantity": quantity, "need_by": need_by}
        return self._save("factory_readiness", request, self.engine.factory_readiness(plant, material, float(quantity), date.fromisoformat(need_by)))

    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict:
        request = {"material": material, "horizon_days": horizon_days, "service_level": service_level}
        return self._save("stock_balance", request, self.engine.stock_balance(material, int(horizon_days), float(service_level)))

    def demand_forecast(self, material: str, warehouse: str | None = None, horizon_days: int = 14) -> dict:
        request = {"material": material, "warehouse": warehouse, "horizon_days": horizon_days}
        return self._save("forecast", request, self.engine.demand_forecast(material, warehouse, int(horizon_days)))

    def supplier_risk(self, supplier: str) -> dict:
        return self._save("supplier_risk", {"supplier": supplier}, self.engine.supplier_risk(supplier))

    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict:
        return self._save("quality_status", {"plant": plant, "material": material}, self.engine.quality_status(plant, material))

    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict:
        return self._save("logistics_status", {"warehouse": warehouse, "material": material}, self.engine.logistics_status(warehouse, material))

    def inventory(self, material: str | None = None) -> dict:
        return {"snapshot": self.sap.snapshot, **self.engine.inventory_overview(material)}

    def sales_orders(self, warehouse: str | None = None) -> dict:
        return self._save("sales_order_fulfilment", {"warehouse": warehouse}, self.engine.sales_order_fulfilment(warehouse))

    def stocktake(self, tolerance_pct: float = 1.0) -> dict:
        return self._save("stocktake_reconciliation", {"tolerance_pct": tolerance_pct}, self.engine.stocktake_reconciliation(tolerance_pct))

    def search_knowledge(self, query: str, top_k: int = 4, category: str | None = None) -> dict:
        return {"query": query, "results": self.rag.search(query, top_k, category)}

    def submit_recommendation(self, analysis_id: str, explanation: str) -> dict:
        return self.store.submit(analysis_id, explanation, self.actor, source="langgraph")


class ApiError(RuntimeError):
    pass


class ApiBackend:
    """HTTP client for the FastAPI gateway; every call is authenticated and audited by the gateway."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 60):
        self._client = httpx.Client(base_url=base_url.rstrip("/"), headers={"X-API-Key": api_key}, timeout=timeout)

    def _call(self, method: str, path: str, **kwargs) -> dict:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise ApiError(f"{method} {path} -> {response.status_code}: {detail}")
        return response.json()

    @staticmethod
    def _clean(payload: dict) -> dict:
        return {key: value for key, value in payload.items() if value not in (None, "")}

    def snapshot(self) -> dict:
        return self._call("GET", "/api/v1/snapshot")

    def factory_readiness(self, plant: str, material: str, quantity: float, need_by: str) -> dict:
        return self._call("POST", "/api/v1/analysis/factory-readiness", json={"plant": plant, "material": material, "quantity": quantity, "need_by": need_by})

    def stock_balance(self, material: str, horizon_days: int = 14, service_level: float = 0.95) -> dict:
        return self._call("POST", "/api/v1/analysis/stock-balance", json={"material": material, "horizon_days": horizon_days, "service_level": service_level})

    def demand_forecast(self, material: str, warehouse: str | None = None, horizon_days: int = 14) -> dict:
        return self._call("POST", "/api/v1/analysis/forecast", json=self._clean({"material": material, "warehouse": warehouse, "horizon_days": horizon_days}))

    def supplier_risk(self, supplier: str) -> dict:
        return self._call("POST", "/api/v1/analysis/supplier-risk", json={"supplier": supplier})

    def quality_status(self, plant: str | None = None, material: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/quality", json=self._clean({"plant": plant, "material": material}))

    def logistics_status(self, warehouse: str | None = None, material: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/logistics", json=self._clean({"warehouse": warehouse, "material": material}))

    def inventory(self, material: str | None = None) -> dict:
        return self._call("GET", "/api/v1/inventory", params=self._clean({"material": material}))

    def sales_orders(self, warehouse: str | None = None) -> dict:
        return self._call("POST", "/api/v1/analysis/sales-orders", json=self._clean({"warehouse": warehouse}))

    def stocktake(self, tolerance_pct: float = 1.0) -> dict:
        return self._call("POST", "/api/v1/analysis/stocktake", json={"tolerance_pct": tolerance_pct})

    def search_knowledge(self, query: str, top_k: int = 4, category: str | None = None) -> dict:
        return self._call("POST", "/api/v1/rag/search", json=self._clean({"query": query, "top_k": top_k, "category": category}))

    def submit_recommendation(self, analysis_id: str, explanation: str) -> dict:
        return self._call("POST", "/api/v1/recommendations", json={"analysis_id": analysis_id, "explanation": explanation, "source": "langgraph"})


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


@lru_cache
def get_backend() -> CopilotBackend:
    return build_backend(get_settings())
