"""LangGraph Chat Graph and Business Graph (exposed to LangGraph Server / LangSmith Studio by langgraph.json).

Chat Graph  : MessagesState conversation. Input guard -> Qwen tool-calling agent <-> read-only tools. Studio Chat mode.
Business Graph: typed state machine for the five governed workflows with a human-in-the-loop interrupt before any
                recommendation reaches the manager review queue. Studio Graph mode.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any, Literal, TypedDict

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.copilot import get_backend
from backend.app.llm import GROUNDING_RULES, chat_model, deterministic_summary
from backend.app.observability import LLM_ERRORS, langfuse_callbacks
from backend.app.sap import SapRepository
from backend.app.tools import READ_ONLY_TOOLS

AS_OF: date = SapRepository(get_settings().data_file).as_of
PLANTS = ("FR10", "FR20", "TPM1")
WAREHOUSES = ("DC01", "DC21", "DC22")
FINISHED_GOODS = ("FG-PERFUME-100", "FG-SERUM-50", "FG-CREAM-50")
MAX_TOOL_ROUNDS = 6
WRITE_INTENT = re.compile(
    r"\b(create|post|change|modify|update|delete|cancel|release|approve|book|place)\b.{0,40}"
    r"\b(purchase order|po|production order|goods (movement|receipt)|transfer order|stock transport order|sap|usage decision|inspection lot)\b",
    re.IGNORECASE,
)
REFUSAL = (
    "I can't create or change SAP records — this copilot has read-only SAP access by design. "
    "I can analyse the situation and prepare an advisory recommendation for manager approval; "
    "an authorized planner then executes any accepted action manually in SAP."
)
CHAT_SYSTEM = (
    GROUNDING_RULES
    + f"\nSAP snapshot business date: {AS_OF.isoformat()}. Plants: FR10 (Paris fragrance), FR20 (Lyon skincare), TPM1 (contract filler). "
    "Warehouses: DC01 Paris, DC21 Dubai, DC22 Singapore. Finished goods: FG-PERFUME-100, FG-SERUM-50, FG-CREAM-50. "
    "Use the tools for every number. Keep answers short and structured: status, key numbers, proposed actions, evidence."
)


# ============================================================================ Chat Graph
def _last_text(state: MessagesState) -> str:
    return str(state["messages"][-1].content)


def guard(state: MessagesState) -> dict:
    return {}


def route_after_guard(state: MessagesState) -> Literal["refuse", "agent", "fallback"]:
    if WRITE_INTENT.search(_last_text(state)):
        return "refuse"
    return "agent" if get_settings().llm_enabled else "fallback"


def refuse(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content=REFUSAL, name="guardrail")]}


def _tool_rounds(messages: list) -> int:
    rounds = 0
    for message in reversed(messages):
        if message.type == "human":
            break
        if isinstance(message, ToolMessage):
            rounds += 1
    return rounds


def agent(state: MessagesState) -> dict:
    settings = get_settings()
    model = chat_model(settings)
    exhausted = _tool_rounds(state["messages"]) >= MAX_TOOL_ROUNDS
    runnable = model if exhausted else model.bind_tools(READ_ONLY_TOOLS)
    try:
        response = runnable.invoke([SystemMessage(content=CHAT_SYSTEM), *state["messages"][-24:]])
    except Exception as exc:  # noqa: BLE001 - LLM outage falls back to deterministic routing
        LLM_ERRORS.labels("langgraph_chat").inc()
        return {"messages": [AIMessage(content=f"{fallback_answer(_first_human(state))}\n\n(LLM unavailable: {str(exc)[:120]})", name="fallback")]}
    return {"messages": [response]}


def _first_human(state: MessagesState) -> str:
    for message in reversed(state["messages"]):
        if message.type == "human":
            return str(message.content)
    return ""


def route_after_agent(state: MessagesState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def fallback_answer(text: str) -> str:
    """Deterministic keyword router used when no LLM is configured; it only restates engine output."""
    upper = text.upper()
    backend = get_backend()
    material = next((code for code in FINISHED_GOODS if code in upper), "FG-SERUM-50")
    lower = text.lower()
    try:
        if any(word in lower for word in ("ready", "factory", "produce", "bom", "production")):
            plant = next((code for code in PLANTS if code in upper), {"FG-PERFUME-100": "FR10", "FG-CREAM-50": "TPM1"}.get(material, "FR20"))
            quantity = float(next(iter(re.findall(r"\b(\d{3,7})\b", text.replace(",", ""))), 5000))
            dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
            need_by = dates[0] if dates else (AS_OF + timedelta(days=14)).isoformat()
            result = backend.factory_readiness(plant, material, quantity, need_by)
        elif any(word in lower for word in ("balance", "transfer", "rebalanc")):
            result = backend.stock_balance(material)
        elif "supplier" in lower or any(s.lower() in lower for s in ("aromachem", "bioactive", "packglass", "carton luxe", "ethapure", "airless", "basechem")):
            name = next((s for s in ("AromaChem SAS", "BioActive Labs", "PackGlass Europe", "Carton Luxe", "EthaPure Iberia", "AirlessPack Asia", "BaseChem Iberia") if s.split()[0].lower() in lower), "BioActive Labs")
            result = backend.supplier_risk(name)
        elif any(word in lower for word in ("contract", "sop", "policy", "spec", "clause")):
            result = backend.search_knowledge(text, 4)
        else:
            result = backend.inventory(None)
            return f"Inventory overview ({len(result['positions'])} positions). Ask about readiness, balancing, suppliers, quality or logistics."
        return deterministic_summary(result) + (f" analysis_id={result['analysis_id']}" if result.get("analysis_id") else "")
    except Exception as exc:  # noqa: BLE001
        return f"Could not complete the deterministic analysis: {exc}"


def fallback(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content=fallback_answer(_last_text(state)), name="deterministic")]}


chat_builder = StateGraph(MessagesState)
chat_builder.add_node("guard", guard)
chat_builder.add_node("refuse", refuse)
chat_builder.add_node("agent", agent)
chat_builder.add_node("tools", ToolNode(READ_ONLY_TOOLS, handle_tool_errors=True))
chat_builder.add_node("fallback", fallback)
chat_builder.add_edge(START, "guard")
chat_builder.add_conditional_edges("guard", route_after_guard, ["refuse", "agent", "fallback"])
chat_builder.add_conditional_edges("agent", route_after_agent, ["tools", END])
chat_builder.add_edge("tools", "agent")
chat_builder.add_edge("refuse", END)
chat_builder.add_edge("fallback", END)


def traced(graph):
    """Attach Langfuse tracing to a compiled graph (still a Pregel graph, so LangGraph Server accepts it)."""
    callbacks = langfuse_callbacks()
    return graph.with_config({"callbacks": callbacks}) if callbacks else graph


chat_graph = traced(chat_builder.compile(name="supply_chain_chat"))


# ======================================================================== Business Graph
RequestType = Literal["factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "inventory"]


class BusinessState(TypedDict, total=False):
    request_text: str
    request_type: RequestType
    plant: str
    material: str
    quantity: float
    need_by: str
    horizon_days: int
    service_level: float
    supplier: str
    warehouse: str
    errors: list[str]
    analysis: dict
    analysis_id: str
    policy_evidence: list[dict]
    narrative: str
    narrative_source: str
    approval: dict
    recommendation: dict
    status: str


class ExtractedRequest(BaseModel):
    """Structured parameters for a supply-chain request. Leave a field empty when it is not stated."""

    request_type: RequestType = Field(description="factory_readiness, stock_balance, supplier_risk, quality, logistics or inventory")
    plant: str = Field(default="", description="FR10, FR20 or TPM1")
    material: str = Field(default="", description="SAP material code, e.g. FG-SERUM-50")
    quantity: float = Field(default=0, description="units to produce")
    need_by: str = Field(default="", description="YYYY-MM-DD")
    supplier: str = Field(default="", description="supplier name")
    warehouse: str = Field(default="", description="DC01, DC21 or DC22")


def _regex_extract(text: str) -> dict:
    upper, lower = text.upper(), text.lower()
    found: dict[str, Any] = {}
    if any(w in lower for w in ("ready", "produce", "production", "bom")):
        found["request_type"] = "factory_readiness"
    elif any(w in lower for w in ("balance", "transfer")):
        found["request_type"] = "stock_balance"
    elif "supplier" in lower:
        found["request_type"] = "supplier_risk"
    elif any(w in lower for w in ("quality", "inspection", "lot")):
        found["request_type"] = "quality"
    elif any(w in lower for w in ("shipment", "logistic", "delay", "carrier")):
        found["request_type"] = "logistics"
    for code in PLANTS:
        if code in upper:
            found["plant"] = code
    for code in WAREHOUSES:
        if code in upper:
            found["warehouse"] = code
    material = re.search(r"\b(?:FG|RM|PK)-[A-Z0-9-]+\b", upper)
    if material:
        found["material"] = material.group(0)
    quantity = re.findall(r"\b(\d{3,7})\b", text.replace(",", ""))
    if quantity:
        found["quantity"] = float(quantity[0])
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    if dates:
        found["need_by"] = dates[0]
    for name in ("AromaChem SAS", "BioActive Labs", "PackGlass Europe", "Carton Luxe", "EthaPure Iberia", "AirlessPack Asia", "BaseChem Iberia"):
        if name.split()[0].lower() in lower:
            found["supplier"] = name
    return found


def intake(state: BusinessState) -> BusinessState:
    """Fill missing parameters from free text: Qwen structured output, deterministic regex as fallback."""
    text = state.get("request_text", "")
    if not text or state.get("request_type"):
        return {}
    extracted = _regex_extract(text)
    settings = get_settings()
    if settings.llm_enabled:
        try:
            model = chat_model(settings).with_structured_output(ExtractedRequest, method="function_calling")
            result = model.invoke(
                [
                    SystemMessage(content=f"Extract parameters exactly as stated. Business date {AS_OF.isoformat()}. Do not invent codes or numbers."),
                    ("user", text),
                ]
            )
            llm_values = {k: v for k, v in result.model_dump().items() if v not in ("", 0, None)}
            extracted = {**llm_values, **{k: v for k, v in extracted.items() if k not in llm_values}}
        except Exception:  # noqa: BLE001
            LLM_ERRORS.labels("langgraph_business").inc()
    return {k: v for k, v in extracted.items() if not state.get(k)}  # type: ignore[return-value]


def validate(state: BusinessState) -> BusinessState:
    errors: list[str] = []
    kind = state.get("request_type")
    snapshot = get_backend().snapshot()
    plants = {row["code"] for row in snapshot["plants"]}
    materials = {row["code"] for row in snapshot["materials"]}
    if kind not in RequestType.__args__:  # type: ignore[attr-defined]
        errors.append("request_type must be one of factory_readiness, stock_balance, supplier_risk, quality, logistics, inventory")
    if state.get("plant") and state["plant"] not in plants:
        errors.append(f"Unknown plant {state['plant']}")
    if state.get("material") and state["material"] not in materials:
        errors.append(f"Unknown material {state['material']}")
    if kind == "factory_readiness":
        for field in ("plant", "material", "quantity"):
            if not state.get(field):
                errors.append(f"factory_readiness requires {field}")
    if kind == "stock_balance" and not state.get("material"):
        errors.append("stock_balance requires material")
    if kind == "supplier_risk" and not state.get("supplier"):
        errors.append("supplier_risk requires supplier")
    if errors:
        return {"errors": errors, "status": "invalid_request"}
    defaults: BusinessState = {"errors": []}
    if kind == "factory_readiness" and not state.get("need_by"):
        defaults["need_by"] = (AS_OF + timedelta(days=14)).isoformat()
    return defaults


def route_workflow(state: BusinessState) -> str:
    return "rejected" if state.get("errors") else state["request_type"]


def run_factory(state: BusinessState) -> BusinessState:
    result = get_backend().factory_readiness(state["plant"], state["material"], float(state["quantity"]), state["need_by"])
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


def run_balance(state: BusinessState) -> BusinessState:
    result = get_backend().stock_balance(state["material"], int(state.get("horizon_days") or 14), float(state.get("service_level") or 0.95))
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


def run_supplier(state: BusinessState) -> BusinessState:
    result = get_backend().supplier_risk(state["supplier"])
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


def run_quality(state: BusinessState) -> BusinessState:
    result = get_backend().quality_status(state.get("plant") or None, state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


def run_logistics(state: BusinessState) -> BusinessState:
    result = get_backend().logistics_status(state.get("warehouse") or None, state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


def run_inventory(state: BusinessState) -> BusinessState:
    result = get_backend().inventory(state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


POLICY_QUERIES = {
    "factory_readiness": ("material readiness quality inspection excluded expedite", "sop"),
    "stock_balance": ("stock transfer approval matrix target stock", "sop"),
    "supplier_risk": ("{supplier} lead time OTIF secondary source expedite", "contract"),
    "quality": ("quality release inspection rejected lot defect", "quality"),
    "logistics": ("shipment delay escalation carrier SLA", "logistics"),
    "inventory": ("target stock safety stock transfer", None),
}


def policy_context(state: BusinessState) -> BusinessState:
    query, category = POLICY_QUERIES[state["request_type"]]
    query = query.format(supplier=state.get("supplier", ""))
    results = get_backend().search_knowledge(query, 3, category).get("results", [])
    return {"policy_evidence": [{"title": r["title"], "source": r["source"], "text": r["text"][:700]} for r in results]}


def explain(state: BusinessState) -> BusinessState:
    analysis = state["analysis"]
    settings = get_settings()
    if settings.llm_enabled:
        try:
            response = chat_model(settings, max_tokens=600).invoke(
                [
                    SystemMessage(content=GROUNDING_RULES),
                    (
                        "user",
                        "Write a 4-6 sentence briefing for the supply planner: status, the key numbers, each proposed action, and the policy "
                        "that governs it. Use only this evidence.\n"
                        f"ANALYSIS: {json.dumps(analysis, default=str)[:8000]}\nPOLICY: {json.dumps(state.get('policy_evidence', []))[:3000]}",
                    ),
                ]
            )
            return {"narrative": str(response.content), "narrative_source": f"llm:{settings.qwen_model}"}
        except Exception:  # noqa: BLE001
            LLM_ERRORS.labels("langgraph_business").inc()
    return {"narrative": deterministic_summary(analysis), "narrative_source": "deterministic-template"}


def needs_approval(state: BusinessState) -> str:
    return "approval_gate" if state["analysis"].get("proposed_actions") and state.get("analysis_id") else "no_action"


def approval_gate(state: BusinessState) -> BusinessState:
    """Human-in-the-loop: the planner decides whether the advisory recommendation goes to the manager queue."""
    decision = interrupt(
        {
            "question": "Submit this advisory recommendation to the manager review queue?",
            "analysis_id": state["analysis_id"],
            "request_type": state["request_type"],
            "proposed_actions": state["analysis"]["proposed_actions"],
            "narrative": state["narrative"],
            "allowed_decisions": ["submit", "discard"],
            "note": "Quantities are fixed by the stored deterministic analysis and cannot be edited here.",
        }
    )
    if isinstance(decision, str):
        decision = {"decision": decision}
    choice = str((decision or {}).get("decision", "discard")).lower()
    return {"approval": {"decision": "submit" if choice in ("submit", "approve", "yes") else "discard", "comment": str((decision or {}).get("comment", ""))[:2000]}}


def route_approval(state: BusinessState) -> str:
    return "submit" if state["approval"]["decision"] == "submit" else "discard"


def submit(state: BusinessState) -> BusinessState:
    comment = state["approval"].get("comment")
    explanation = state["narrative"] + (f"\n\nPlanner comment: {comment}" if comment else "")
    recommendation = get_backend().submit_recommendation(state["analysis_id"], explanation)
    return {"recommendation": recommendation, "status": "submitted_for_manager_review"}


def discard(state: BusinessState) -> BusinessState:
    return {"status": "discarded_by_planner"}


def no_action(state: BusinessState) -> BusinessState:
    return {"status": "completed_no_action_required"}


def rejected(state: BusinessState) -> BusinessState:
    return {"status": "invalid_request"}


business_builder = StateGraph(BusinessState)
business_builder.add_node("intake", intake)
business_builder.add_node("validate", validate)
business_builder.add_node("rejected", rejected)
business_builder.add_node("factory_readiness", run_factory)
business_builder.add_node("stock_balance", run_balance)
business_builder.add_node("supplier_risk", run_supplier)
business_builder.add_node("quality", run_quality)
business_builder.add_node("logistics", run_logistics)
business_builder.add_node("inventory", run_inventory)
business_builder.add_node("policy_context", policy_context)
business_builder.add_node("explain", explain)
business_builder.add_node("approval_gate", approval_gate)
business_builder.add_node("submit", submit)
business_builder.add_node("discard", discard)
business_builder.add_node("no_action", no_action)
business_builder.add_edge(START, "intake")
business_builder.add_edge("intake", "validate")
business_builder.add_conditional_edges(
    "validate", route_workflow, ["rejected", "factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "inventory"]
)
for workflow in ("factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "inventory"):
    business_builder.add_edge(workflow, "policy_context")
business_builder.add_edge("policy_context", "explain")
business_builder.add_conditional_edges("explain", needs_approval, ["approval_gate", "no_action"])
business_builder.add_conditional_edges("approval_gate", route_approval, ["submit", "discard"])
for terminal in ("submit", "discard", "no_action", "rejected"):
    business_builder.add_edge(terminal, END)
business_graph = traced(business_builder.compile(name="supply_chain_business"))
