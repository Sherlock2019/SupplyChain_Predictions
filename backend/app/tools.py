"""Read-only LangChain tools shared by the LangGraph Chat Graph, Business Graph and Deep Agent."""
from __future__ import annotations

import json

from langchain_core.tools import tool

from backend.app.copilot import get_backend

MAX_TOOL_CHARS = 9000


def _dump(payload: dict) -> str:
    text = json.dumps(payload, default=str)
    return text if len(text) <= MAX_TOOL_CHARS else text[:MAX_TOOL_CHARS] + '..."TRUNCATED"'


def _safe(fn, *args, **kwargs) -> str:
    try:
        return _dump(fn(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - tool errors go back to the model so it can correct its arguments
        return json.dumps({"error": str(exc)[:600]})


@tool
def sap_snapshot() -> str:
    """Return SAP snapshot provenance plus valid plant, material and supplier codes. Call this before using any code."""
    return _safe(get_backend().snapshot)


@tool
def factory_material_readiness(plant: str, material: str, quantity: float, need_by: str) -> str:
    """Check BOM material readiness for a production run.

    Args:
        plant: factory code FR10, FR20 or TPM1
        material: finished-good code such as FG-SERUM-50
        quantity: units to produce
        need_by: production need date YYYY-MM-DD
    """
    return _safe(get_backend().factory_readiness, plant.upper(), material.upper(), quantity, need_by)


@tool
def warehouse_stock_balance(material: str, horizon_days: int = 14, service_level: float = 0.95) -> str:
    """Forecast demand (XGBoost) and optimise stock transfers between DC01, DC21 and DC22 (OR-Tools)."""
    return _safe(get_backend().stock_balance, material.upper(), horizon_days, service_level)


@tool
def demand_forecast(material: str, warehouse: str = "", horizon_days: int = 14) -> str:
    """XGBoost daily demand forecast for a finished good, optionally for one warehouse (DC01, DC21, DC22)."""
    return _safe(get_backend().demand_forecast, material.upper(), warehouse.upper() or None, horizon_days)


@tool
def supplier_risk(supplier: str) -> str:
    """Supplier scorecard: OTIF, delays, quality rejects, open PO exposure, single-source risk. Accepts supplier name or vendor code."""
    return _safe(get_backend().supplier_risk, supplier)


@tool
def quality_status(plant: str = "", material: str = "") -> str:
    """Quality inspection lots (QM): inspection/blocked/expired batches and which production orders they affect."""
    return _safe(get_backend().quality_status, plant.upper() or None, material.upper() or None)


@tool
def logistics_status(warehouse: str = "", material: str = "") -> str:
    """In-transit shipments, delays, revised ETAs and escalations for a warehouse and/or material."""
    return _safe(get_backend().logistics_status, warehouse.upper() or None, material.upper() or None)


@tool
def inventory_overview(material: str = "") -> str:
    """Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse."""
    return _safe(get_backend().inventory, material.upper() or None)


@tool
def sales_order_fulfilment(warehouse: str = "") -> str:
    """Open sales orders: can each ship on time from DC stock + inbound? Shortfalls get the cheapest on-time transfer or a partial delivery."""
    return _safe(get_backend().sales_orders, warehouse.upper() or None)


@tool
def stocktake_reconciliation(tolerance_pct: float = 1.0) -> str:
    """Explain stock count differences (unposted goods movements, scrap not posted) and recommend posting or a recount."""
    return _safe(get_backend().stocktake, tolerance_pct)


@tool
def search_governed_knowledge(query: str, category: str = "") -> str:
    """Search approved supplier contracts, SOPs, quality policies, product specs and logistics policies (RAG).

    Args:
        query: natural-language question
        category: optional filter: contract, sop, quality, product_spec, logistics
    """
    return _safe(get_backend().search_knowledge, query, 5, category or None)


READ_ONLY_TOOLS = [
    sap_snapshot,
    factory_material_readiness,
    warehouse_stock_balance,
    demand_forecast,
    supplier_risk,
    quality_status,
    logistics_status,
    inventory_overview,
    sales_order_fulfilment,
    stocktake_reconciliation,
    search_governed_knowledge,
]
