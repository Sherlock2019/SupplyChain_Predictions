# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/tools.py
# What this module is: the read-only LangChain tools of the SPARC agents (LangGraph chat graph, business graph, Deep Agent).
# Each @tool wraps one CopilotBackend method; the docstring is the tool description the LLM reads; errors are returned to the model
# as JSON so it can correct its arguments; outputs are capped at 9000 characters.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Read-only LangChain tools shared by the LangGraph Chat Graph, Business Graph and Deep Agent."""
from __future__ import annotations

import json

# @tool: turns a typed function + docstring into a tool schema the model can call.
from langchain_core.tools import tool

from backend.app.copilot import get_backend

# Keeps tool results inside the model's context window.
MAX_TOOL_CHARS = 9000


# ===== FUNCTION: _dump() =====
# ID: F0501 · function · used
# ORIGINAL FILE: backend/app/tools.py:13-15
# ROLE: Serialise a payload to JSON, truncated to MAX_TOOL_CHARS with a visible marker.
# INPUTS:
#   payload: dict.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0502 _safe() (calls)
# CALLS:
#   (none found)
def _dump(payload: dict) -> str:
    text = json.dumps(payload, default=str)
    return text if len(text) <= MAX_TOOL_CHARS else text[:MAX_TOOL_CHARS] + '..."TRUNCATED"'


# ===== FUNCTION: _safe() =====
# ID: F0502 · function · used
# ORIGINAL FILE: backend/app/tools.py:18-22
# ROLE: Call a backend method and return JSON; any exception becomes {"error": ...} (never crashes the agent).
# INPUTS:
#   fn: callable, *args, **kwargs.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0503 sap_snapshot() (calls)
#   <- F0504 factory_material_readiness() (calls)
#   <- F0505 warehouse_stock_balance() (calls)
#   <- F0506 demand_forecast() (calls)
#   <- F0507 supplier_risk() (calls)
#   <- F0508 quality_status() (calls)
#   <- F0509 logistics_status() (calls)
#   <- F0510 inventory_overview() (calls)
#   <- F0511 sales_order_fulfilment() (calls)
#   <- F0512 stocktake_reconciliation() (calls)
#   <- F0513 search_governed_knowledge() (calls)
# CALLS:
#   -> F0501 _dump() (calls)
def _safe(fn, *args, **kwargs) -> str:
    try:
        return _dump(fn(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - tool errors go back to the model so it can correct its arguments
        return json.dumps({"error": str(exc)[:600]})


# ===== FUNCTION: sap_snapshot() =====
# ID: F0503 · function · used
# ORIGINAL FILE: backend/app/tools.py:25-28
# ROLE: Tool: snapshot provenance + valid codes.
# INPUTS:
#   none.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0454 LocalBackend.snapshot() (references)
#   -> F0471 ApiBackend.snapshot() (references)
#   -> F0484 get_backend() (calls)
@tool
def sap_snapshot() -> str:
    """Return SAP snapshot provenance plus valid plant, material and supplier codes. Call this before using any code."""
    return _safe(get_backend().snapshot)


# ===== FUNCTION: factory_material_readiness() =====
# ID: F0504 · function · used
# ORIGINAL FILE: backend/app/tools.py:31-41
# ROLE: Tool: factory material readiness (codes upper-cased).
# INPUTS:
#   plant, material: str; quantity: float; need_by: str.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0455 LocalBackend.factory_readiness() (references)
#   -> F0472 ApiBackend.factory_readiness() (references)
#   -> F0484 get_backend() (calls)
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


# ===== FUNCTION: warehouse_stock_balance() =====
# ID: F0505 · function · used
# ORIGINAL FILE: backend/app/tools.py:44-47
# ROLE: Tool: XGBoost forecast + OR-Tools transfers across the three DCs.
# INPUTS:
#   material: str, horizon_days: int, service_level: float.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0456 LocalBackend.stock_balance() (references)
#   -> F0473 ApiBackend.stock_balance() (references)
#   -> F0484 get_backend() (calls)
@tool
def warehouse_stock_balance(material: str, horizon_days: int = 14, service_level: float = 0.95) -> str:
    """Forecast demand (XGBoost) and optimise stock transfers between DC01, DC21 and DC22 (OR-Tools)."""
    return _safe(get_backend().stock_balance, material.upper(), horizon_days, service_level)


# ===== FUNCTION: demand_forecast() =====
# ID: F0506 · function · used
# ORIGINAL FILE: backend/app/tools.py:50-53
# ROLE: Tool: demand forecast (empty warehouse string -> None = all DCs).
# INPUTS:
#   material: str, warehouse: str, horizon_days: int.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0457 LocalBackend.demand_forecast() (references)
#   -> F0474 ApiBackend.demand_forecast() (references)
#   -> F0484 get_backend() (calls)
@tool
def demand_forecast(material: str, warehouse: str = "", horizon_days: int = 14) -> str:
    """XGBoost daily demand forecast for a finished good, optionally for one warehouse (DC01, DC21, DC22)."""
    return _safe(get_backend().demand_forecast, material.upper(), warehouse.upper() or None, horizon_days)


# ===== FUNCTION: supplier_risk() =====
# ID: F0507 · function · used
# ORIGINAL FILE: backend/app/tools.py:56-59
# ROLE: Tool: supplier risk scorecard.
# INPUTS:
#   supplier: str.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0458 LocalBackend.supplier_risk() (references)
#   -> F0475 ApiBackend.supplier_risk() (references)
#   -> F0484 get_backend() (calls)
@tool
def supplier_risk(supplier: str) -> str:
    """Supplier scorecard: OTIF, delays, quality rejects, open PO exposure, single-source risk. Accepts supplier name or vendor code."""
    return _safe(get_backend().supplier_risk, supplier)


# ===== FUNCTION: quality_status() =====
# ID: F0508 · function · used
# ORIGINAL FILE: backend/app/tools.py:62-65
# ROLE: Tool: quality inspection lots.
# INPUTS:
#   plant, material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0459 LocalBackend.quality_status() (references)
#   -> F0476 ApiBackend.quality_status() (references)
#   -> F0484 get_backend() (calls)
@tool
def quality_status(plant: str = "", material: str = "") -> str:
    """Quality inspection lots (QM): inspection/blocked/expired batches and which production orders they affect."""
    return _safe(get_backend().quality_status, plant.upper() or None, material.upper() or None)


# ===== FUNCTION: logistics_status() =====
# ID: F0509 · function · used
# ORIGINAL FILE: backend/app/tools.py:68-71
# ROLE: Tool: shipments and delays.
# INPUTS:
#   warehouse, material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0460 LocalBackend.logistics_status() (references)
#   -> F0477 ApiBackend.logistics_status() (references)
#   -> F0484 get_backend() (calls)
@tool
def logistics_status(warehouse: str = "", material: str = "") -> str:
    """In-transit shipments, delays, revised ETAs and escalations for a warehouse and/or material."""
    return _safe(get_backend().logistics_status, warehouse.upper() or None, material.upper() or None)


# ===== FUNCTION: inventory_overview() =====
# ID: F0510 · function · used
# ORIGINAL FILE: backend/app/tools.py:74-77
# ROLE: Tool: finished-goods inventory overview.
# INPUTS:
#   material: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0461 LocalBackend.inventory() (references)
#   -> F0478 ApiBackend.inventory() (references)
#   -> F0484 get_backend() (calls)
@tool
def inventory_overview(material: str = "") -> str:
    """Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse."""
    return _safe(get_backend().inventory, material.upper() or None)


# ===== FUNCTION: sales_order_fulfilment() =====
# ID: F0511 · function · used
# ORIGINAL FILE: backend/app/tools.py:80-83
# ROLE: Tool: sales-order fulfilment.
# INPUTS:
#   warehouse: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0462 LocalBackend.sales_orders() (references)
#   -> F0479 ApiBackend.sales_orders() (references)
#   -> F0484 get_backend() (calls)
@tool
def sales_order_fulfilment(warehouse: str = "") -> str:
    """Open sales orders: can each ship on time from DC stock + inbound? Shortfalls get the cheapest on-time transfer or a partial delivery."""
    return _safe(get_backend().sales_orders, warehouse.upper() or None)


# ===== FUNCTION: stocktake_reconciliation() =====
# ID: F0512 · function · used
# ORIGINAL FILE: backend/app/tools.py:86-89
# ROLE: Tool: stocktake reconciliation.
# INPUTS:
#   tolerance_pct: float.
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0463 LocalBackend.stocktake() (references)
#   -> F0480 ApiBackend.stocktake() (references)
#   -> F0484 get_backend() (calls)
@tool
def stocktake_reconciliation(tolerance_pct: float = 1.0) -> str:
    """Explain stock count differences (unposted goods movements, scrap not posted) and recommend posting or a recount."""
    return _safe(get_backend().stocktake, tolerance_pct)


# ===== FUNCTION: search_governed_knowledge() =====
# ID: F0513 · function · used
# ORIGINAL FILE: backend/app/tools.py:92-100
# ROLE: Tool: governed knowledge search (top 5).
# INPUTS:
#   query: str, category: str (optional).
# OUTPUT:
#   str (JSON).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0502 _safe() (calls)
#   -> F0464 LocalBackend.search_knowledge() (references)
#   -> F0481 ApiBackend.search_knowledge() (references)
#   -> F0484 get_backend() (calls)
@tool
def search_governed_knowledge(query: str, category: str = "") -> str:
    """Search approved supplier contracts, SOPs, quality policies, product specs and logistics policies (RAG).

    Args:
        query: natural-language question
        category: optional filter: contract, sop, quality, product_spec, logistics
    """
    return _safe(get_backend().search_knowledge, query, 5, category or None)


# The full read-only tool set (role agents receive a subset, see roles.ROLES[...]["tools"]).
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
