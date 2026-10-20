"""Warehouse rebalancing with OR-Tools and deterministic constraint inputs."""
from __future__ import annotations

from typing import Any


def optimize_transfers(stock: dict[str, float], targets: dict[str, float], lanes: list[dict[str, Any]]) -> dict:
    try:
        from ortools.linear_solver import pywraplp
    except ImportError:  # pragma: no cover
        return _greedy(stock, targets, lanes) | {"engine": "greedy-fallback"}

    solver = pywraplp.Solver.CreateSolver("GLOP")
    if solver is None:  # pragma: no cover
        return _greedy(stock, targets, lanes) | {"engine": "greedy-fallback"}
    variables: dict[tuple[str, str], Any] = {}
    lane_map = {(lane["from"], lane["to"]): lane for lane in lanes}
    for pair in lane_map:
        variables[pair] = solver.NumVar(0, solver.infinity(), f"ship_{pair[0]}_{pair[1]}")
    shortage = {warehouse: solver.NumVar(0, solver.infinity(), f"short_{warehouse}") for warehouse in stock}
    for warehouse in stock:
        incoming = sum(var for (source, target), var in variables.items() if target == warehouse)
        outgoing = sum(var for (source, target), var in variables.items() if source == warehouse)
        solver.Add(stock[warehouse] + incoming - outgoing + shortage[warehouse] >= targets[warehouse])
        solver.Add(outgoing <= max(0.0, stock[warehouse] - targets[warehouse]))
    objective = solver.Objective()
    for pair, var in variables.items():
        objective.SetCoefficient(var, float(lane_map[pair]["cost_per_unit"]))
    for var in shortage.values():
        objective.SetCoefficient(var, 1000.0)
    objective.SetMinimization()
    status = solver.Solve()
    transfers = []
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        for pair, variable in variables.items():
            quantity = round(variable.solution_value(), 3)
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

