"""LangGraph AgentFlow — the LangGraph counterpart of the Flowise AgentFlow V2.

START → supervisor (guardrail + Qwen router) → factory / balancing / research specialist agents (scoped tools)
      → planner approval interrupt() → manager review queue;  SAP-write requests → protected boundary.

Unlike the Flowise version, the analysis submitted for approval is taken from the specialist's *tool output* in graph state,
never from LLM text. Without an LLM the specialists fall back to deterministic calls so the flow still runs end to end.
"""
from __future__ import annotations

import json
from typing import Literal

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.copilot import get_backend
from backend.app.graphs import AS_OF, REFUSAL, WRITE_INTENT, _regex_extract, traced
from backend.app.llm import GROUNDING_RULES, chat_model, deterministic_summary
from backend.app.observability import LLM_ERRORS
from backend.app.tools import (
    factory_material_readiness,
    inventory_overview,
    logistics_status,
    quality_status,
    sap_snapshot,
    search_governed_knowledge,
    supplier_risk,
    warehouse_stock_balance,
)

Route = Literal["factory", "balancing", "research", "boundary"]

SPECIALISTS = {
    "factory": {
        "tools": [sap_snapshot, factory_material_readiness, quality_status, search_governed_knowledge],
        "use_case": "factory_material_readiness",
        "prompt": "You are the factory readiness specialist. Call factory_material_readiness with plant, finished-good code, quantity and "
        "need_by (YYYY-MM-DD). If a component is short you may call quality_status for that plant. Summarise status, short components "
        "and proposed actions, and quote the analysis_id.",
    },
    "balancing": {
        "tools": [sap_snapshot, warehouse_stock_balance, inventory_overview, logistics_status, search_governed_knowledge],
        "use_case": "three_warehouse_stock_balancing",
        "prompt": "You are the stock balancing specialist for DC01, DC21 and DC22. Call warehouse_stock_balance for the finished good "
        "(XGBoost forecast + OR-Tools). Summarise positions and every proposed transfer (from, to, quantity, cost) and quote the analysis_id.",
    },
    "research": {
        "tools": [supplier_risk, search_governed_knowledge, quality_status, logistics_status],
        "use_case": None,
        "prompt": "You are the supplier and quality research specialist. Use supplier_risk for the scorecard and search_governed_knowledge "
        "(category contract or quality) for clauses. Report risk rating, evidence with document titles, contract levers and advisory next steps.",
    },
}


class AgentFlowState(MessagesState, total=False):
    route: Route
    route_reason: str
    analysis: dict
    approval: dict
    status: str


class RouteDecision(BaseModel):
    """Pick exactly one governed specialist for the planner's latest request."""

    route: Route = Field(description="factory: production/BOM readiness; balancing: stock transfers, inventory, demand; "
                         "research: suppliers, contracts, quality lots, shipments; boundary: any request to create/change/approve/post in SAP")
    reason: str = Field(default="", description="one short sentence")


def _last_human(state: AgentFlowState) -> str:
    return next((str(m.content) for m in reversed(state["messages"]) if m.type == "human"), "")


def _keyword_route(text: str) -> Route:
    kind = _regex_extract(text).get("request_type")
    if kind == "factory_readiness":
        return "factory"
    if kind == "stock_balance" or "inventory" in text.lower() or "forecast" in text.lower():
        return "balancing"
    return "research"


def supervisor(state: AgentFlowState) -> dict:
    text = _last_human(state)
    reset = {"analysis": {}, "approval": {}, "status": ""}
    if WRITE_INTENT.search(text):
        return {**reset, "route": "boundary", "route_reason": "guardrail: SAP write intent"}
    settings = get_settings()
    if settings.llm_enabled:
        try:
            router = chat_model(settings, max_tokens=200).with_structured_output(RouteDecision, method="function_calling")
            decision = router.invoke([SystemMessage(content="Route supply-chain planner requests. " + RouteDecision.__doc__), HumanMessage(content=text)])
            return {**reset, "route": decision.route, "route_reason": decision.reason or "llm"}
        except Exception:  # noqa: BLE001
            LLM_ERRORS.labels("langgraph_agentflow").inc()
    return {**reset, "route": _keyword_route(text), "route_reason": "keyword fallback"}


def route_next(state: AgentFlowState) -> str:
    return {"factory": "factory_agent", "balancing": "balancing_agent", "research": "research_agent"}.get(state["route"], "boundary")


def _conversation(state: AgentFlowState) -> list:
    """Prior human turns and final answers only, so specialists never see dangling tool calls from earlier turns."""
    clean = [m for m in state["messages"] if m.type == "human" or (m.type == "ai" and not getattr(m, "tool_calls", None) and m.content)]
    return clean[-9:]


def _analysis_from(messages: list, use_case: str | None) -> dict:
    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            continue
        try:
            payload = json.loads(str(message.content))
        except ValueError:
            continue
        if isinstance(payload, dict) and payload.get("analysis_id") and (use_case is None or payload.get("use_case") == use_case):
            return payload
    return {}


def _deterministic(route: str, text: str) -> dict:
    backend, params = get_backend(), _regex_extract(text)
    if route == "factory":
        plant = params.get("plant") or {"FG-PERFUME-100": "FR10", "FG-CREAM-50": "TPM1"}.get(params.get("material", ""), "FR20")
        return backend.factory_readiness(plant, params.get("material", "FG-SERUM-50"), float(params.get("quantity", 5000)), params.get("need_by", AS_OF.isoformat()))
    if route == "balancing":
        return backend.stock_balance(params.get("material", "FG-PERFUME-100"))
    return backend.supplier_risk(params.get("supplier", "BioActive Labs"))


def _specialist(route: str):
    spec = SPECIALISTS[route]
    agent = None

    def node(state: AgentFlowState, config: RunnableConfig) -> dict:
        nonlocal agent
        settings = get_settings()
        if settings.llm_enabled:
            try:
                if agent is None:
                    agent = create_agent(chat_model(settings), spec["tools"], system_prompt=GROUNDING_RULES + "\n\n" + spec["prompt"], name=f"{route}_specialist")
                history = _conversation(state)
                result = agent.invoke({"messages": history}, config)
                produced = result["messages"][len(history):]
                return {"messages": produced, "analysis": _analysis_from(produced, spec["use_case"])}
            except Exception as exc:  # noqa: BLE001 - degrade to the deterministic path, never to invented numbers
                LLM_ERRORS.labels("langgraph_agentflow").inc()
                note = f" (LLM unavailable: {str(exc)[:100]})"
        else:
            note = ""
        result = _deterministic(route, _last_human(state))
        return {"messages": [AIMessage(content=deterministic_summary(result) + f" analysis_id={result.get('analysis_id')}{note}", name=f"{route}_specialist")],
                "analysis": result if spec["use_case"] else {}}

    node.__name__ = f"{route}_agent"
    return node


def approval_gate(state: AgentFlowState) -> dict:
    """Planner Human Input: submit the specialist's stored analysis to the manager queue, or discard it."""
    analysis = state.get("analysis") or {}
    if not analysis.get("proposed_actions"):
        return {"status": "completed_no_action_required"}
    decision = interrupt(
        {
            "question": "Submit this recommendation to the manager review queue?",
            "specialist": state["route"],
            "analysis_id": analysis["analysis_id"],
            "proposed_actions": analysis["proposed_actions"],
            "allowed_decisions": ["submit", "discard"],
            "note": "Quantities come from the stored deterministic analysis; nothing is written to SAP.",
        }
    )
    decision = decision if isinstance(decision, dict) else {"decision": str(decision)}
    if str(decision.get("decision", "")).lower() not in ("submit", "proceed", "approve", "yes"):
        return {"approval": decision, "status": "discarded_by_planner",
                "messages": [AIMessage(content="Discarded by the planner. Nothing was submitted or written to SAP.", name="approval")]}
    final = next((str(m.content) for m in reversed(state["messages"]) if m.type == "ai" and m.content), "")
    comment = str(decision.get("comment", ""))[:2000]
    rec = get_backend().submit_recommendation(analysis["analysis_id"], final[:8000] + (f"\n\nPlanner comment: {comment}" if comment else ""))
    return {"approval": decision, "status": "submitted_for_manager_review",
            "messages": [AIMessage(content=f"Recommendation #{rec['id']} ({analysis['analysis_id']}) is in the manager review queue "
                                   f"(status {rec['status']}). No SAP record was changed.", name="approval")]}


def boundary(state: AgentFlowState) -> dict:
    return {"status": "refused_sap_write", "messages": [AIMessage(content=REFUSAL, name="guardrail")]}


builder = StateGraph(AgentFlowState)
builder.add_node("supervisor", supervisor)
builder.add_node("factory_agent", _specialist("factory"))
builder.add_node("balancing_agent", _specialist("balancing"))
builder.add_node("research_agent", _specialist("research"))
builder.add_node("approval_gate", approval_gate)
builder.add_node("boundary", boundary)
builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_next, ["factory_agent", "balancing_agent", "research_agent", "boundary"])
builder.add_edge("factory_agent", "approval_gate")
builder.add_edge("balancing_agent", "approval_gate")
builder.add_edge("research_agent", END)
builder.add_edge("approval_gate", END)
builder.add_edge("boundary", END)
graph = traced(builder.compile(name="supply_chain_agentflow"))
