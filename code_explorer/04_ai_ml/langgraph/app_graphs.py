# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/graphs.py
# What this module is: two LangGraph graphs of the SPARC platform, registered in langgraph.json:
#   - Chat Graph ("supply_chain_chat"): input guard (SAP-write refusal) -> Qwen tool-calling agent <-> read-only tools, with a
#     deterministic keyword fallback when no LLM is configured; optional role-specialised agents (scoped tools + role prompt).
#   - Business Graph ("supply_chain_business"): typed state machine intake -> validate -> one of six workflows -> policy RAG ->
#     explanation -> human-in-the-loop interrupt -> submit to the manager review queue / discard.
# Only comment lines were added (AST-verified).
# ======================================================================================================

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
# MessagesState: built-in state with a "messages" list merged by add_messages.
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

# Business date of the default SAP snapshot (read once at import).
AS_OF: date = SapRepository(get_settings().data_file).as_of
PLANTS = ("FR10", "FR20", "TPM1")
WAREHOUSES = ("DC01", "DC21", "DC22")
FINISHED_GOODS = ("FG-PERFUME-100", "FG-SERUM-50", "FG-CREAM-50")
# After 6 tool results in one turn the model must answer without tools (loop guard).
MAX_TOOL_ROUNDS = 6
# Deterministic SAP-write intent detector: a write verb within 40 characters of an SAP object.
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


# ===== FUNCTION: _last_text() =====
# ID: F0573 · function · used
# ORIGINAL FILE: backend/app/graphs.py:51-52
# ROLE: Text of the last message.
# INPUTS:
#   state: MessagesState.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0575 route_after_guard() (calls)
#   <- F0584 fallback() (calls)
# CALLS:
#   (none found)
def _last_text(state: MessagesState) -> str:
    return str(state["messages"][-1].content)


# ===== FUNCTION: guard() =====
# ID: F0574 · function · used
# ORIGINAL FILE: backend/app/graphs.py:55-56
# ROLE: Guard node (no state change); routing happens in route_after_guard.
# INPUTS:
#   state.
# OUTPUT:
#   dict -> {}.
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
def guard(state: MessagesState) -> dict:
    return {}


# ===== FUNCTION: route_after_guard() =====
# ID: F0575 · function · used
# ORIGINAL FILE: backend/app/graphs.py:59-62
# ROLE: Route: SAP-write intent -> refuse; LLM enabled -> agent; else deterministic fallback.
# INPUTS:
#   state.
# OUTPUT:
#   Literal["refuse", "agent", "fallback"].
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0573 _last_text() (calls)
#   -> F0008 get_settings() (calls)
def route_after_guard(state: MessagesState) -> Literal["refuse", "agent", "fallback"]:
    if WRITE_INTENT.search(_last_text(state)):
        return "refuse"
    return "agent" if get_settings().llm_enabled else "fallback"


# ===== FUNCTION: refuse() =====
# ID: F0576 · function · used
# ORIGINAL FILE: backend/app/graphs.py:65-66
# ROLE: Fixed read-only refusal (message name "guardrail").
# INPUTS:
#   state.
# OUTPUT:
#   dict -> messages.
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
def refuse(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content=REFUSAL, name="guardrail")]}


# ===== FUNCTION: _tool_rounds() =====
# ID: F0577 · function · used
# ORIGINAL FILE: backend/app/graphs.py:69-76
# ROLE: Number of tool results since the last human message (for the MAX_TOOL_ROUNDS guard).
# INPUTS:
#   messages: list.
# OUTPUT:
#   int.
# CALLED BY:
#   <- F0580 agent() (calls)
# CALLS:
#   (none found)
def _tool_rounds(messages: list) -> int:
    rounds = 0
    for message in reversed(messages):
        if message.type == "human":
            break
        if isinstance(message, ToolMessage):
            rounds += 1
    return rounds


# ===== CLASS: ChatState =====
# ID: F0578 · class · used
# ORIGINAL FILE: backend/app/graphs.py:79-80
# ROLE: Chat state = messages + optional role of the specialised agent.
# FIELDS:
#   messages (inherited), role: str.
# CALLED BY:
#   <- F0580 agent() (references)
# CALLS:
#   (none found)
class ChatState(MessagesState, total=False):
    role: str  # optional: specialised role agent (director, demand, production, procurement, warehouse, ...)


# ===== FUNCTION: _role_setup() =====
# ID: F0579 · function · used
# ORIGINAL FILE: backend/app/graphs.py:83-92
# ROLE: System prompt and tool subset of a role agent; no / unknown role = general copilot with every tool.
# INPUTS:
#   role: str | None.
# OUTPUT:
#   tuple[str, list] -> (system prompt, tools).
# CALLED BY:
#   <- F0580 agent() (calls)
#   <- F0961 test_role_agent_gets_scoped_tools_and_industry_rules() (calls)
# CALLS:
#   -> F0256 agent_system_prompt() (calls)
def _role_setup(role: str | None) -> tuple[str, list]:
    """System prompt and tool set for the role's specialised agent; no role = the general copilot with every tool."""
    # Local import: roles.py imports the engine stack; deferring keeps import order simple.
    from backend.app.roles import ROLES, agent_system_prompt

    if not role or role not in ROLES:
        return CHAT_SYSTEM, READ_ONLY_TOOLS
    allowed = ROLES[role]["tools"]
    tools = [t for t in READ_ONLY_TOOLS if allowed is None or t.name in allowed]
    # The tools read the Aurelia (cosmetics) tenant, so the agent applies cosmetics industry rules.
    return CHAT_SYSTEM + "\n" + agent_system_prompt(role, "cosmetics"), tools


# ===== FUNCTION: agent() =====
# ID: F0580 · function · used
# ORIGINAL FILE: backend/app/graphs.py:95-106
# ROLE: Agent node: Qwen with the role's tools bound (unless the tool budget is exhausted); last 24 messages as context; an LLM error
#       falls back to the deterministic answer and increments the LLM error metric.
# INPUTS:
#   state: ChatState.
# OUTPUT:
#   dict -> messages [model reply].
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0578 ChatState (references)
#   -> F0008 get_settings() (calls)
#   -> F0728 chat_model() (calls)
#   -> F0579 _role_setup() (calls)
#   -> F0577 _tool_rounds() (calls)
#   -> F0805 ScriptedModel.bind_tools() (calls)
#   -> F0583 fallback_answer() (calls)
#   -> F0581 _first_human() (calls)
def agent(state: ChatState) -> dict:
    settings = get_settings()
    model = chat_model(settings)
    system, tools = _role_setup(state.get("role"))
    exhausted = _tool_rounds(state["messages"]) >= MAX_TOOL_ROUNDS
    runnable = model if exhausted else model.bind_tools(tools)
    try:
        response = runnable.invoke([SystemMessage(content=system), *state["messages"][-24:]])
    except Exception as exc:  # noqa: BLE001 - LLM outage falls back to deterministic routing
        LLM_ERRORS.labels("langgraph_chat").inc()
        return {"messages": [AIMessage(content=f"{fallback_answer(_first_human(state))}\n\n(LLM unavailable: {str(exc)[:120]})", name="fallback")]}
    return {"messages": [response]}


# ===== FUNCTION: _first_human() =====
# ID: F0581 · function · used
# ORIGINAL FILE: backend/app/graphs.py:109-113
# ROLE: Text of the most recent human message.
# INPUTS:
#   state.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0580 agent() (calls)
# CALLS:
#   (none found)
def _first_human(state: MessagesState) -> str:
    for message in reversed(state["messages"]):
        if message.type == "human":
            return str(message.content)
    return ""


# ===== FUNCTION: route_after_agent() =====
# ID: F0582 · function · used
# ORIGINAL FILE: backend/app/graphs.py:116-118
# ROLE: Route after the agent: tool calls -> tools node, else END.
# INPUTS:
#   state.
# OUTPUT:
#   Literal["tools", "__end__"].
# CALLED BY:
#   (none found)
# CALLS:
#   (none found)
def route_after_agent(state: MessagesState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


# ===== FUNCTION: fallback_answer() =====
# ID: F0583 · function · used
# ORIGINAL FILE: backend/app/graphs.py:121-146
# ROLE: Deterministic keyword router (no LLM): pick readiness / balancing / supplier risk / knowledge / inventory from words in the
#       text, extract codes / quantity / date with regexes, call the backend and restate its output.
# INPUTS:
#   text: str.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0580 agent() (calls)
#   <- F0584 fallback() (calls)
# CALLS:
#   -> F0484 get_backend() (calls)
#   -> F0730 deterministic_summary() (calls)
def fallback_answer(text: str) -> str:
    """Deterministic keyword router used when no LLM is configured; it only restates engine output."""
    upper = text.upper()
    backend = get_backend()
    material = next((code for code in FINISHED_GOODS if code in upper), "FG-SERUM-50")
    lower = text.lower()
    try:
        if any(word in lower for word in ("ready", "factory", "produce", "bom", "production")):
            # Plant from the text, else the plant that makes the product.
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


# ===== FUNCTION: fallback() =====
# ID: F0584 · function · used
# ORIGINAL FILE: backend/app/graphs.py:149-150
# ROLE: Fallback node (LLM disabled).
# INPUTS:
#   state.
# OUTPUT:
#   dict -> messages.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0583 fallback_answer() (calls)
#   -> F0573 _last_text() (calls)
def fallback(state: MessagesState) -> dict:
    return {"messages": [AIMessage(content=fallback_answer(_last_text(state)), name="deterministic")]}


# Chat graph wiring (module level, built at import).
chat_builder = StateGraph(ChatState)
chat_builder.add_node("guard", guard)
chat_builder.add_node("refuse", refuse)
chat_builder.add_node("agent", agent)
# handle_tool_errors=True: a tool exception becomes a ToolMessage the model can read.
chat_builder.add_node("tools", ToolNode(READ_ONLY_TOOLS, handle_tool_errors=True))
chat_builder.add_node("fallback", fallback)
chat_builder.add_edge(START, "guard")
chat_builder.add_conditional_edges("guard", route_after_guard, ["refuse", "agent", "fallback"])
chat_builder.add_conditional_edges("agent", route_after_agent, ["tools", END])
chat_builder.add_edge("tools", "agent")
chat_builder.add_edge("refuse", END)
chat_builder.add_edge("fallback", END)


# ===== FUNCTION: traced() =====
# ID: F0585 · function · used
# ORIGINAL FILE: backend/app/graphs.py:167-170
# ROLE: Attach Langfuse tracing to a compiled graph (still a Pregel graph accepted by LangGraph Server).
# INPUTS:
#   graph: compiled graph.
# OUTPUT:
#   graph (with_config) or the same graph.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0010 langfuse_callbacks() (calls)
def traced(graph):
    """Attach Langfuse tracing to a compiled graph (still a Pregel graph, so LangGraph Server accepts it)."""
    callbacks = langfuse_callbacks()
    return graph.with_config({"callbacks": callbacks}) if callbacks else graph


chat_graph = traced(chat_builder.compile(name="supply_chain_chat"))


# ======================================================================== Business Graph
RequestType = Literal["factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "inventory"]


# ===== CLASS: BusinessState =====
# ID: F0586 · class · used
# ORIGINAL FILE: backend/app/graphs.py:180-199
# ROLE: Typed state of the business workflow (all keys optional).
# FIELDS:
#   request fields, errors, analysis, analysis_id, policy_evidence, narrative, narrative_source, approval, recommendation, status.
# CALLED BY:
#   <- F0589 intake() (references)
#   <- F0590 validate() (references)
#   <- F0591 route_workflow() (references)
#   <- F0592 run_factory() (references)
#   <- F0593 run_balance() (references)
#   <- F0594 run_supplier() (references)
#   <- F0595 run_quality() (references)
#   <- F0596 run_logistics() (references)
#   <- F0597 run_inventory() (references)
#   <- F0598 policy_context() (references)
#   <- F0599 explain() (references)
#   <- F0600 needs_approval() (references)
# CALLS:
#   (none found)
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


# ===== CLASS: ExtractedRequest =====
# ID: F0587 · pydantic_model · used
# ORIGINAL FILE: backend/app/graphs.py:202-211
# ROLE: Pydantic schema for the LLM's structured extraction (function calling).
# FIELDS:
#   request_type, plant, material, quantity, need_by, supplier, warehouse.
# CALLED BY:
#   <- F0589 intake() (references)
# CALLS:
#   (none found)
class ExtractedRequest(BaseModel):
    """Structured parameters for a supply-chain request. Leave a field empty when it is not stated."""

    request_type: RequestType = Field(description="factory_readiness, stock_balance, supplier_risk, quality, logistics or inventory")
    plant: str = Field(default="", description="FR10, FR20 or TPM1")
    material: str = Field(default="", description="SAP material code, e.g. FG-SERUM-50")
    quantity: float = Field(default=0, description="units to produce")
    need_by: str = Field(default="", description="YYYY-MM-DD")
    supplier: str = Field(default="", description="supplier name")
    warehouse: str = Field(default="", description="DC01, DC21 or DC22")


# ===== FUNCTION: _regex_extract() =====
# ID: F0588 · function · used
# ORIGINAL FILE: backend/app/graphs.py:214-245
# ROLE: Deterministic regex extraction of request type, plant, warehouse, material, quantity, date and supplier from free text.
# INPUTS:
#   text: str.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0543 _keyword_route() (calls)
#   <- F0548 _deterministic() (calls)
#   <- F0589 intake() (calls)
# CALLS:
#   (none found)
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


# ===== FUNCTION: intake() =====
# ID: F0589 · function · used
# ORIGINAL FILE: backend/app/graphs.py:248-268
# ROLE: Intake node: fill missing parameters from free text (LLM structured output first, regex values fill the gaps); fields the
#       caller already gave are never overwritten.
# INPUTS:
#   state: BusinessState.
# OUTPUT:
#   BusinessState (partial update).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0588 _regex_extract() (calls)
#   -> F0008 get_settings() (calls)
#   -> F0728 chat_model() (calls)
#   -> F0587 ExtractedRequest (references)
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


# ===== FUNCTION: validate() =====
# ID: F0590 · function · used
# ORIGINAL FILE: backend/app/graphs.py:271-296
# ROLE: Validate node: request type, codes against the SAP snapshot, required fields per workflow; default need_by = as_of + 14 days.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> {"errors", "status": "invalid_request"} or defaults.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0454 LocalBackend.snapshot() (calls)
#   -> F0471 ApiBackend.snapshot() (calls)
#   -> F0484 get_backend() (calls)
def validate(state: BusinessState) -> BusinessState:
    errors: list[str] = []
    kind = state.get("request_type")
    snapshot = get_backend().snapshot()
    plants = {row["code"] for row in snapshot["plants"]}
    materials = {row["code"] for row in snapshot["materials"]}
    # RequestType.__args__: the allowed strings of the Literal type.
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


# ===== FUNCTION: route_workflow() =====
# ID: F0591 · function · used
# ORIGINAL FILE: backend/app/graphs.py:299-300
# ROLE: Route to "rejected" on errors, else to the workflow node named like the request type.
# INPUTS:
#   state.
# OUTPUT:
#   str.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def route_workflow(state: BusinessState) -> str:
    return "rejected" if state.get("errors") else state["request_type"]


# ===== FUNCTION: run_factory() =====
# ID: F0592 · function · used
# ORIGINAL FILE: backend/app/graphs.py:303-305
# ROLE: Workflow node: factory readiness through the backend (stored analysis).
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> analysis, analysis_id.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0455 LocalBackend.factory_readiness() (calls)
#   -> F0472 ApiBackend.factory_readiness() (calls)
#   -> F0484 get_backend() (calls)
def run_factory(state: BusinessState) -> BusinessState:
    result = get_backend().factory_readiness(state["plant"], state["material"], float(state["quantity"]), state["need_by"])
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# ===== FUNCTION: run_balance() =====
# ID: F0593 · function · used
# ORIGINAL FILE: backend/app/graphs.py:308-310
# ROLE: Workflow node: stock balancing.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0456 LocalBackend.stock_balance() (calls)
#   -> F0473 ApiBackend.stock_balance() (calls)
#   -> F0484 get_backend() (calls)
def run_balance(state: BusinessState) -> BusinessState:
    result = get_backend().stock_balance(state["material"], int(state.get("horizon_days") or 14), float(state.get("service_level") or 0.95))
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# ===== FUNCTION: run_supplier() =====
# ID: F0594 · function · used
# ORIGINAL FILE: backend/app/graphs.py:313-315
# ROLE: Workflow node: supplier risk.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0458 LocalBackend.supplier_risk() (calls)
#   -> F0475 ApiBackend.supplier_risk() (calls)
#   -> F0484 get_backend() (calls)
def run_supplier(state: BusinessState) -> BusinessState:
    result = get_backend().supplier_risk(state["supplier"])
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# ===== FUNCTION: run_quality() =====
# ID: F0595 · function · used
# ORIGINAL FILE: backend/app/graphs.py:318-320
# ROLE: Workflow node: quality status.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0459 LocalBackend.quality_status() (calls)
#   -> F0476 ApiBackend.quality_status() (calls)
#   -> F0484 get_backend() (calls)
def run_quality(state: BusinessState) -> BusinessState:
    result = get_backend().quality_status(state.get("plant") or None, state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# ===== FUNCTION: run_logistics() =====
# ID: F0596 · function · used
# ORIGINAL FILE: backend/app/graphs.py:323-325
# ROLE: Workflow node: logistics status.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0460 LocalBackend.logistics_status() (calls)
#   -> F0477 ApiBackend.logistics_status() (calls)
#   -> F0484 get_backend() (calls)
def run_logistics(state: BusinessState) -> BusinessState:
    result = get_backend().logistics_status(state.get("warehouse") or None, state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# ===== FUNCTION: run_inventory() =====
# ID: F0597 · function · used
# ORIGINAL FILE: backend/app/graphs.py:328-330
# ROLE: Workflow node: inventory overview (no analysis_id: nothing to approve).
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0461 LocalBackend.inventory() (calls)
#   -> F0478 ApiBackend.inventory() (calls)
#   -> F0484 get_backend() (calls)
def run_inventory(state: BusinessState) -> BusinessState:
    result = get_backend().inventory(state.get("material") or None)
    return {"analysis": result, "analysis_id": result.get("analysis_id", "")}


# Policy RAG query and category per workflow ({supplier} filled in).
POLICY_QUERIES = {
    "factory_readiness": ("material readiness quality inspection excluded expedite", "sop"),
    "stock_balance": ("stock transfer approval matrix target stock", "sop"),
    "supplier_risk": ("{supplier} lead time OTIF secondary source expedite", "contract"),
    "quality": ("quality release inspection rejected lot defect", "quality"),
    "logistics": ("shipment delay escalation carrier SLA", "logistics"),
    "inventory": ("target stock safety stock transfer", None),
}


# ===== FUNCTION: policy_context() =====
# ID: F0598 · function · used
# ORIGINAL FILE: backend/app/graphs.py:343-347
# ROLE: Policy node: top 3 governed passages for the workflow (text truncated to 700 characters).
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> policy_evidence.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0464 LocalBackend.search_knowledge() (calls)
#   -> F0481 ApiBackend.search_knowledge() (calls)
#   -> F0484 get_backend() (calls)
def policy_context(state: BusinessState) -> BusinessState:
    query, category = POLICY_QUERIES[state["request_type"]]
    query = query.format(supplier=state.get("supplier", ""))
    results = get_backend().search_knowledge(query, 3, category).get("results", [])
    return {"policy_evidence": [{"title": r["title"], "source": r["source"], "text": r["text"][:700]} for r in results]}


# ===== FUNCTION: explain() =====
# ID: F0599 · function · used
# ORIGINAL FILE: backend/app/graphs.py:350-369
# ROLE: Explain node: Qwen writes a 4-6 sentence briefing from the analysis + policy evidence only; deterministic template otherwise.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> narrative, narrative_source.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0008 get_settings() (calls)
#   -> F0728 chat_model() (calls)
#   -> F0730 deterministic_summary() (calls)
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


# ===== FUNCTION: needs_approval() =====
# ID: F0600 · function · used
# ORIGINAL FILE: backend/app/graphs.py:372-373
# ROLE: Route: proposed actions + a stored analysis -> approval gate, else no action.
# INPUTS:
#   state.
# OUTPUT:
#   str.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def needs_approval(state: BusinessState) -> str:
    return "approval_gate" if state["analysis"].get("proposed_actions") and state.get("analysis_id") else "no_action"


# ===== FUNCTION: approval_gate() =====
# ID: F0601 · function · used
# ORIGINAL FILE: backend/app/graphs.py:376-392
# ROLE: Human-in-the-loop: interrupt() pauses with the proposal; on resume the planner's "submit" / "discard" (+ comment) is recorded.
#       Quantities cannot be edited here (they come from the stored analysis).
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> approval {decision, comment}.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
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


# ===== FUNCTION: route_approval() =====
# ID: F0602 · function · used
# ORIGINAL FILE: backend/app/graphs.py:395-396
# ROLE: Route after the gate.
# INPUTS:
#   state.
# OUTPUT:
#   str -> "submit" | "discard".
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def route_approval(state: BusinessState) -> str:
    return "submit" if state["approval"]["decision"] == "submit" else "discard"


# ===== FUNCTION: submit() =====
# ID: F0603 · function · used
# ORIGINAL FILE: backend/app/graphs.py:399-403
# ROLE: Submit node: the stored analysis goes to the manager review queue with the narrative (+ planner comment).
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState -> recommendation, status.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
#   -> F0465 LocalBackend.submit_recommendation() (calls)
#   -> F0482 ApiBackend.submit_recommendation() (calls)
#   -> F0484 get_backend() (calls)
def submit(state: BusinessState) -> BusinessState:
    comment = state["approval"].get("comment")
    explanation = state["narrative"] + (f"\n\nPlanner comment: {comment}" if comment else "")
    recommendation = get_backend().submit_recommendation(state["analysis_id"], explanation)
    return {"recommendation": recommendation, "status": "submitted_for_manager_review"}


# ===== FUNCTION: discard() =====
# ID: F0604 · function · used
# ORIGINAL FILE: backend/app/graphs.py:406-407
# ROLE: Terminal: discarded by the planner.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def discard(state: BusinessState) -> BusinessState:
    return {"status": "discarded_by_planner"}


# ===== FUNCTION: no_action() =====
# ID: F0605 · function · used
# ORIGINAL FILE: backend/app/graphs.py:410-411
# ROLE: Terminal: nothing to approve.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def no_action(state: BusinessState) -> BusinessState:
    return {"status": "completed_no_action_required"}


# ===== FUNCTION: rejected() =====
# ID: F0606 · function · used
# ORIGINAL FILE: backend/app/graphs.py:414-415
# ROLE: Terminal: invalid request.
# INPUTS:
#   state.
# OUTPUT:
#   BusinessState.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0586 BusinessState (references)
def rejected(state: BusinessState) -> BusinessState:
    return {"status": "invalid_request"}


# Business graph wiring.
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
