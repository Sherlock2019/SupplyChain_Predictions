# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/optimizer.py
# What this module is: warehouse rebalancing as a linear program solved by Google OR-Tools (GLOP): choose transfer quantities on
# the transport lanes that bring every warehouse to its target at minimum transport cost, with a heavy penalty on unresolved
# shortage. A greedy cheapest-lane fallback is used only if OR-Tools is unavailable.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Warehouse rebalancing with OR-Tools and deterministic constraint inputs."""
from __future__ import annotations

from typing import Any


# ===== FUNCTION: optimize_transfers() =====
# ID: F0291 · function · used
# ORIGINAL FILE: backend/app/optimizer.py:7-57
# ROLE: Optimise transfers between warehouses.
#       Variables: ship[from,to] >= 0 per lane, short[w] >= 0 per warehouse.
#       Constraints: stock + incoming - outgoing + short >= target (per warehouse); outgoing <= surplus (donors keep their target).
#       Objective: minimise sum(cost_per_unit x ship) + 1000 x sum(short).
# INPUTS:
#   stock: dict[str, float] (on hand + in transit), targets: dict[str, float], lanes: list[dict] (from, to, cost_per_unit, lead_days, carbon_kg_per_unit).
# OUTPUT:
#   dict -> engine, solver_status, transfers[{action, from, to, quantity, lead_days, estimated_cost, carbon_kg}], unresolved_shortages, objective_cost.
# CALLED BY:
#   <- F0198 SupplyChainEngine.stock_balance() (calls)
#   <- F0200 SupplyChainEngine.what_if() (calls)
# CALLS:
#   -> F0292 _greedy() (calls)
def optimize_transfers(stock: dict[str, float], targets: dict[str, float], lanes: list[dict[str, Any]]) -> dict:
    try:
        from ortools.linear_solver import pywraplp
    except ImportError:  # pragma: no cover
        # dict | dict merges the fallback result with the engine name.
        return _greedy(stock, targets, lanes) | {"engine": "greedy-fallback"}

    # GLOP = Google's linear-programming solver (continuous variables).
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if solver is None:  # pragma: no cover
        return _greedy(stock, targets, lanes) | {"engine": "greedy-fallback"}
    variables: dict[tuple[str, str], Any] = {}
    lane_map = {(lane["from"], lane["to"]): lane for lane in lanes}
    # One non-negative decision variable per lane.
    for pair in lane_map:
        variables[pair] = solver.NumVar(0, solver.infinity(), f"ship_{pair[0]}_{pair[1]}")
    # Slack variable per warehouse: shortage that cannot be covered.
    shortage = {warehouse: solver.NumVar(0, solver.infinity(), f"short_{warehouse}") for warehouse in stock}
    for warehouse in stock:
        # Linear expressions: sums of variables on lanes into / out of the warehouse.
        incoming = sum(var for (source, target), var in variables.items() if target == warehouse)
        outgoing = sum(var for (source, target), var in variables.items() if source == warehouse)
        solver.Add(stock[warehouse] + incoming - outgoing + shortage[warehouse] >= targets[warehouse])
        # A donor may only ship its surplus above its own target.
        solver.Add(outgoing <= max(0.0, stock[warehouse] - targets[warehouse]))
    objective = solver.Objective()
    for pair, var in variables.items():
        objective.SetCoefficient(var, float(lane_map[pair]["cost_per_unit"]))
    # 1000 EUR per unit short: covering demand always beats saving transport cost.
    for var in shortage.values():
        objective.SetCoefficient(var, 1000.0)
    objective.SetMinimization()
    status = solver.Solve()
    transfers = []
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for pair, variable in variables.items():
            quantity = round(variable.solution_value(), 3)
            # Ignore numerical dust below half a unit.
            if quantity >= 0.5:
                lane = lane_map[pair]
                transfers.append(
                    {
                        "action": "stock_transfer",
                        "from": pair[0],
                        "to": pair[1],
                        "quantity": quantity,
                        "lead_days": lane["lead_days"],
                        "estimated_cost": round(quantity * float(lane["cost_per_unit"]), 2),
                        "carbon_kg": round(quantity * float(lane["carbon_kg_per_unit"]), 2),
                    }
                )
    unresolved = {warehouse: round(variable.solution_value(), 3) for warehouse, variable in shortage.items() if variable.solution_value() >= 0.5}
    return {
        "engine": "ortools-glop",
        "solver_status": int(status),
        "transfers": transfers,
        "unresolved_shortages": unresolved,
        "objective_cost": round(objective.Value(), 2),
    }


# ===== FUNCTION: _greedy() =====
# ID: F0292 · function · used
# ORIGINAL FILE: backend/app/optimizer.py:60-71
# ROLE: Fallback heuristic: walk lanes from cheapest to most expensive and move min(donor excess, receiver shortage).
# INPUTS:
#   stock, targets, lanes (as above).
# OUTPUT:
#   dict -> transfers[], unresolved_shortages.
# CALLED BY:
#   <- F0291 optimize_transfers() (calls)
# CALLS:
#   (none found)
def _greedy(stock: dict[str, float], targets: dict[str, float], lanes: list[dict[str, Any]]) -> dict:
    excess = {key: max(0.0, stock[key] - targets[key]) for key in stock}
    shortage = {key: max(0.0, targets[key] - stock[key]) for key in stock}
    transfers = []
    for lane in sorted(lanes, key=lambda item: item["cost_per_unit"]):
        qty = min(excess[lane["from"]], shortage[lane["to"]])
        if qty <= 0:
            continue
        excess[lane["from"]] -= qty
        shortage[lane["to"]] -= qty
        transfers.append({"action": "stock_transfer", "from": lane["from"], "to": lane["to"], "quantity": round(qty, 3)})
    return {"transfers": transfers, "unresolved_shortages": {key: value for key, value in shortage.items() if value > 0}}
