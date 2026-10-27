# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/deep_agent.py
# What this module is: the Deep Agents supplier-continuity research agent ("supplier_deep_agent"): planning (write_todos), a virtual
# scratch filesystem, delegation to three subagents (contract / quality / logistics analyst), read-only tools only. Its "harness"
# (temperature, token and step budgets, loop limits, retries, allowed subagents and tools, plan / citation rules, report style) is
# stored by a manager and enforced at run time by the HarnessGuard middleware.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Deep Agents supplier-continuity research harness — with run-time harness settings.

Planning (write_todos), a virtual scratch filesystem for working notes, and delegation to focused subagents.
Every tool is read-only and goes through the governed gateway; the agent can recommend but never act.

The harness (model temperature / max tokens, step budget, enabled subagents, allowed tools, plan and citation rules,
report style) is stored in the governance database and edited by a manager in SPARC. Each run carries the harness in
graph state; the `deep_research` node builds (and caches) the Deep Agent for exactly those settings, so the same graph
works in-process and on LangGraph Server / Studio.
"""
from __future__ import annotations

import json

# create_deep_agent: the deepagents library (planning, files, subagents on top of a tool-calling agent).
from deepagents import create_deep_agent
# AgentMiddleware: hooks around model / tool calls. ToolRetryMiddleware: retries failed tool calls.
from langchain.agents.middleware import AgentMiddleware, ToolRetryMiddleware
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, MessagesState, StateGraph
# Runtime[...]: gives the node access to the typed run context (Studio configuration panel).
from langgraph.runtime import Runtime
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.llm import GROUNDING_RULES, chat_model
from backend.app.observability import langfuse_callbacks
from backend.app.schemas import DeepAgentHarness
from backend.app.tools import (
    factory_material_readiness,
    logistics_status,
    quality_status,
    sap_snapshot,
    search_governed_knowledge,
    supplier_risk,
)

# Tools the harness may enable, by name.
TOOLS = {t.name: t for t in (supplier_risk, sap_snapshot, search_governed_knowledge, quality_status, logistics_status, factory_material_readiness)}

# The three subagents (name, description shown to the main agent, own prompt, own tools).
SUBAGENTS = [
    {
        "name": "contract-analyst",
        "description": "Finds contractual lead time, OTIF target, expedite clause, penalties and secondary-source terms for one supplier.",
        "system_prompt": GROUNDING_RULES + "\nSearch the governed knowledge base (category contract) and return exact clauses with document titles.",
        "tools": [search_governed_knowledge],
    },
    {
        "name": "quality-analyst",
        "description": "Assesses inspection lots, rejected/blocked batches and quality policy for a supplier's materials.",
        "system_prompt": GROUNDING_RULES + "\nUse quality_status and quality policies. Report lot numbers, quantities, defects and release dates.",
        "tools": [quality_status, search_governed_knowledge],
    },
    {
        "name": "logistics-analyst",
        "description": "Checks inbound shipments, delays and carrier SLAs affecting a supplier's deliveries.",
        "system_prompt": GROUNDING_RULES + "\nUse logistics_status and logistics policies. Report shipment ids, delays and revised ETAs.",
        "tools": [logistics_status, search_governed_knowledge],
    },
]

DEFAULT_HARNESS = DeepAgentHarness().model_dump()


# ===== FUNCTION: harness_of() =====
# ID: F0554 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:62-64
# ROLE: Validated harness: stored / given settings merged over the defaults, re-validated by the Pydantic model (bad values -> error).
# INPUTS:
#   value: dict | None.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0565 build_deep_agent() (calls)
#   <- F0571 deep_research() (calls)
#   <- F0832 test_deep_agent_harness_controls_tools_subagents_steps_and_prompt() (calls)
#   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
# CALLS:
#   -> F0172 DeepAgentHarness (calls)
def harness_of(value: dict | None) -> dict:
    """Validated harness: stored settings merged over the defaults (invalid or unknown values are rejected)."""
    return DeepAgentHarness(**{**DEFAULT_HARNESS, **(value or {})}).model_dump()


# ===== FUNCTION: system_prompt() =====
# ID: F0555 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:67-88
# ROLE: Build the main agent's system prompt from the harness (plan step, scorecard step, delegation step, report style, citations,
#       tool budget, never claim execution).
# INPUTS:
#   h: dict (harness).
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0565 build_deep_agent() (calls)
#   <- F0832 test_deep_agent_harness_controls_tools_subagents_steps_and_prompt() (calls)
#   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
# CALLS:
#   (none found)
def system_prompt(h: dict) -> str:
    steps = ["You are the supplier-continuity research agent. For each request:"]
    if h["require_plan"]:
        steps.append("1. Write a short todo plan first.")
    steps.append("2. Call supplier_risk for the supplier to get the deterministic scorecard." if "supplier_risk" in h["tools"]
                 else "2. Use the available read-only tools for every number.")
    delegate = {"contract-analyst": "contract terms to the contract-analyst", "quality-analyst": "quality evidence to the quality-analyst",
                "logistics-analyst": "shipments to the logistics-analyst (only when they matter)"}
    if h["subagents"] and h["max_subagent_calls"]:
        steps.append("3. Delegate " + "; ".join(delegate[s] for s in h["subagents"]) + f" (at most {h['max_subagent_calls']} delegations).")
    else:
        steps.append("3. Do the research yourself; no subagents are enabled.")
    if h["report_style"] == "executive":
        steps.append("4. Finish with an executive summary of at most 8 bullet points: risk rating, the 3 key facts, the recommended advisory actions.")
    else:
        steps.append("4. Finish with a report in markdown: Risk rating, Evidence, Contract levers (lead time, expedite clause, secondary source), "
                     "Recommended advisory actions, Approvals required.")
    if h["require_citations"]:
        steps.append("Cite analysis_id, PO numbers, inspection lots and document titles for every claim.")
    steps.append(f"Budget: at most {h['max_tool_calls']} tool calls in total and {h['max_calls_per_tool']} per tool; do not repeat a call that already answered.")
    steps.append("Never claim an action was executed.")
    return GROUNDING_RULES + "\n\n" + "\n".join(steps)


SUBAGENT_TOOL = "task"  # Deep Agents delegates to a subagent through this tool


# ===== FUNCTION: _this_run() =====
# ID: F0556 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:94-97
# ROLE: Messages of the current run (after the last user message), so limits reset per request.
# INPUTS:
#   messages: list.
# OUTPUT:
#   list.
# CALLED BY:
#   <- F0559 HarnessGuard._stop_message() (calls)
#   <- F0560 HarnessGuard._refusal() (calls)
# CALLS:
#   (none found)
def _this_run(messages: list) -> list:
    """Messages of the current run: everything after the last user message (limits reset on every new request)."""
    start = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1)
    return messages[start + 1:]


# ===== CLASS: HarnessGuard =====
# ID: F0557 · class · used
# ORIGINAL FILE: backend/app/deep_agent.py:100-155
# ROLE: Middleware enforcing the harness loop controls around each model and tool call: a model-call limit ends the run with a final
#       note; a tool / per-tool / subagent limit answers the call with an error ToolMessage instead of executing it. Never raises.
# FIELDS:
#   h: dict (harness).
# CALLED BY:
#   <- F0565 build_deep_agent() (calls)
#   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
# CALLS:
#   (none found)
class HarnessGuard(AgentMiddleware):
    """Loop controls of the harness, enforced around each model and tool call (no extra graph steps).

    Counts come from the run's own message history, so they are exact and reset per request. Hitting a limit never
    raises: a model-call limit ends the run with a final note; a tool limit answers the call with a "limit reached"
    result so the agent finishes with what it already has. Deep Agents' own planning / scratch-file tools are not counted.
    """

    # ===== FUNCTION: HarnessGuard.__init__() =====
    # ID: F0558 · method · used (framework)
    # ORIGINAL FILE: backend/app/deep_agent.py:108-110
    # ROLE: Keep the harness.
    # INPUTS:
    #   h: dict.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, h: dict):
        super().__init__()
        self.h = h

    # ===== FUNCTION: HarnessGuard._stop_message() =====
    # ID: F0559 · method · used
    # ORIGINAL FILE: backend/app/deep_agent.py:112-117
    # ROLE: Final AIMessage when the run already used max_model_calls AI turns, else None.
    # INPUTS:
    #   request (model request with .state).
    # OUTPUT:
    #   AIMessage | None.
    # CALLED BY:
    #   <- F0561 HarnessGuard.wrap_model_call() (calls)
    #   <- F0562 HarnessGuard.awrap_model_call() (calls)
    # CALLS:
    #   -> F0556 _this_run() (calls)
    def _stop_message(self, request) -> AIMessage | None:
        turns = sum(1 for m in _this_run(request.state.get("messages", [])) if isinstance(m, AIMessage))
        if turns < self.h["max_model_calls"]:
            return None
        return AIMessage(content=f"Stopped by the harness: the limit of {self.h['max_model_calls']} model calls for one run was reached. "
                                 "The findings above are what was gathered so far; raise 'Max model calls' or narrow the question for a fuller report.")

    # ===== FUNCTION: HarnessGuard._refusal() =====
    # ID: F0560 · method · used
    # ORIGINAL FILE: backend/app/deep_agent.py:119-143
    # ROLE: Error ToolMessage when this tool call would exceed a limit (subagent delegations, calls of this tool, all counted calls); None
    #       otherwise. Planning and scratch-file tools are not limited.
    # INPUTS:
    #   request (tool request with .tool_call and .state).
    # OUTPUT:
    #   ToolMessage | None.
    # CALLED BY:
    #   <- F0563 HarnessGuard.wrap_tool_call() (calls)
    #   <- F0564 HarnessGuard.awrap_tool_call() (calls)
    # CALLS:
    #   -> F0556 _this_run() (calls)
    def _refusal(self, request) -> ToolMessage | None:
        call = request.tool_call
        name = call["name"]
        if name != SUBAGENT_TOOL and name not in TOOLS:
            return None  # planning (write_todos) and scratch-file tools are not limited
        earlier, found = [], False  # tool calls made before this one in the current run
        for m in _this_run(request.state.get("messages", [])):
            for c in getattr(m, "tool_calls", None) or []:
                if c.get("id") == call.get("id"):
                    found = True
                    break
                earlier.append(c["name"])
            if found:
                break
        counted = [n for n in earlier if n == SUBAGENT_TOOL or n in TOOLS]
        if name == SUBAGENT_TOOL and counted.count(SUBAGENT_TOOL) >= self.h["max_subagent_calls"]:
            reason = f"the limit of {self.h['max_subagent_calls']} subagent delegations per run"
        elif name != SUBAGENT_TOOL and counted.count(name) >= self.h["max_calls_per_tool"]:
            reason = f"the limit of {self.h['max_calls_per_tool']} calls of {name} per run"
        elif len(counted) >= self.h["max_tool_calls"]:
            reason = f"the limit of {self.h['max_tool_calls']} tool calls per run"
        else:
            return None
        return ToolMessage(content=f"Not executed: {reason} was reached (harness). Do not call it again; finish the report with the evidence you already have.",
                           tool_call_id=call["id"], name=name, status="error")

    # ===== FUNCTION: HarnessGuard.wrap_model_call() =====
    # ID: F0561 · method · used
    # ORIGINAL FILE: backend/app/deep_agent.py:145-146
    # ROLE: Middleware hook around a model call (sync): stop message or the real call.
    # INPUTS:
    #   request, handler.
    # OUTPUT:
    #   model response.
    # CALLED BY:
    #   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
    # CALLS:
    #   -> F0559 HarnessGuard._stop_message() (calls)
    def wrap_model_call(self, request, handler):
        return self._stop_message(request) or handler(request)

    # ===== FUNCTION: HarnessGuard.awrap_model_call() =====
    # ID: F0562 · method · used (framework)
    # ORIGINAL FILE: backend/app/deep_agent.py:148-149
    # ROLE: Same hook, async version.
    # INPUTS:
    #   request, handler.
    # OUTPUT:
    #   model response.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0559 HarnessGuard._stop_message() (calls)
    async def awrap_model_call(self, request, handler):
        return self._stop_message(request) or await handler(request)

    # ===== FUNCTION: HarnessGuard.wrap_tool_call() =====
    # ID: F0563 · method · used
    # ORIGINAL FILE: backend/app/deep_agent.py:151-152
    # ROLE: Middleware hook around a tool call (sync): refusal or the real call.
    # INPUTS:
    #   request, handler.
    # OUTPUT:
    #   ToolMessage.
    # CALLED BY:
    #   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
    # CALLS:
    #   -> F0560 HarnessGuard._refusal() (calls)
    def wrap_tool_call(self, request, handler):
        return self._refusal(request) or handler(request)

    # ===== FUNCTION: HarnessGuard.awrap_tool_call() =====
    # ID: F0564 · method · used (framework)
    # ORIGINAL FILE: backend/app/deep_agent.py:154-155
    # ROLE: Same hook, async version.
    # INPUTS:
    #   request, handler.
    # OUTPUT:
    #   ToolMessage.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0560 HarnessGuard._refusal() (calls)
    async def awrap_tool_call(self, request, handler):
        return self._refusal(request) or await handler(request)


# ===== FUNCTION: build_deep_agent() =====
# ID: F0565 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:158-174
# ROLE: Build the Deep Agent for one harness: model settings, allowed tools, system prompt, HarnessGuard (+ tool retries), enabled
#       subagents; recursion_limit = max_steps.
# INPUTS:
#   checkpointer (optional), harness: dict | None.
# OUTPUT:
#   compiled agent graph.
# CALLED BY:
#   <- F0566 _agent_for() (calls)
#   <- F0831 test_deep_agent_is_built_with_subagents_and_planning_tools() (calls)
#   <- F0832 test_deep_agent_harness_controls_tools_subagents_steps_and_prompt() (calls)
#   <- F0833 test_harness_guard_enforces_loop_controls_per_run() (calls)
# CALLS:
#   -> F0554 harness_of() (calls)
#   -> F0557 HarnessGuard (calls)
#   -> F0728 chat_model() (calls)
#   -> F0008 get_settings() (calls)
#   -> F0555 system_prompt() (calls)
def build_deep_agent(checkpointer=None, harness: dict | None = None):
    """The Deep Agent for one harness (compiled LangGraph with model, tools and subagent task tool)."""
    h = harness_of(harness)
    middleware = [HarnessGuard(h)]
    if h["tool_retries"]:
        middleware.append(ToolRetryMiddleware(max_retries=h["tool_retries"], tools=[TOOLS[name] for name in h["tools"]]))
    agent = create_deep_agent(
        model=chat_model(get_settings(), temperature=h["temperature"], max_tokens=h["max_tokens"],
                         timeout=h["model_timeout_seconds"], max_retries=h["model_retries"]),
        tools=[TOOLS[name] for name in h["tools"]],
        system_prompt=system_prompt(h),
        middleware=middleware,
        subagents=[s for s in SUBAGENTS if s["name"] in h["subagents"]],
        checkpointer=checkpointer,
        name="supplier_deep_agent",
    )
    return agent.with_config({"recursion_limit": h["max_steps"]})


# Cache of built agents keyed by the canonical JSON of their harness.
_AGENTS: dict[str, object] = {}


# ===== FUNCTION: _agent_for() =====
# ID: F0566 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:180-184
# ROLE: Cached agent for a harness.
# INPUTS:
#   h: dict.
# OUTPUT:
#   compiled agent.
# CALLED BY:
#   <- F0571 deep_research() (calls)
# CALLS:
#   -> F0565 build_deep_agent() (calls)
def _agent_for(h: dict):
    key = json.dumps(h, sort_keys=True)
    if key not in _AGENTS:
        _AGENTS[key] = build_deep_agent(harness=h)
    return _AGENTS[key]


# ===== CLASS: ResearchState =====
# ID: F0567 · class · used
# ORIGINAL FILE: backend/app/deep_agent.py:187-191
# ROLE: Graph state of the research graph.
# FIELDS:
#   messages, harness, harness_used, todos, files.
# CALLED BY:
#   <- F0571 deep_research() (references)
#   <- F0572 build_graph() (references)
# CALLS:
#   (none found)
class ResearchState(MessagesState, total=False):
    harness: dict
    harness_used: dict
    todos: list
    files: dict


# ===== CLASS: ResearchInput =====
# ID: F0568 · class · used
# ORIGINAL FILE: backend/app/deep_agent.py:194-196
# ROLE: Input schema (Studio input form): the question + optional harness overrides for this run.
# FIELDS:
#   messages, harness.
# CALLED BY:
#   <- F0572 build_graph() (references)
# CALLS:
#   (none found)
class ResearchInput(MessagesState, total=False):
    """What a run takes (Studio's Input form): the question, and optionally harness overrides for this run only."""
    harness: dict


# ===== CLASS: HarnessConfig =====
# ID: F0569 · pydantic_model · used
# ORIGINAL FILE: backend/app/deep_agent.py:199-201
# ROLE: Context schema (Studio configuration panel): the assistant's harness settings.
# FIELDS:
#   harness: DeepAgentHarness.
# CALLED BY:
#   <- F0570 _context_harness() (references)
#   <- F0571 deep_research() (references)
#   <- F0572 build_graph() (references)
# CALLS:
#   (none found)
class HarnessConfig(BaseModel):
    """Assistant context: Studio's configuration panel shows every harness setting with its current value."""
    harness: DeepAgentHarness = Field(default=DeepAgentHarness(), description="Harness settings for every run of this assistant")


# ===== FUNCTION: _context_harness() =====
# ID: F0570 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:204-208
# ROLE: Harness values explicitly set in the run / assistant context (unset defaults never mask a preset).
# INPUTS:
#   context: HarnessConfig | dict | None.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0571 deep_research() (calls)
# CALLS:
#   -> F0569 HarnessConfig (references)
def _context_harness(context) -> dict:
    """Harness settings given in the run/assistant context (only the ones actually set, so defaults never mask a preset)."""
    if isinstance(context, HarnessConfig):
        return context.harness.model_dump(include=context.harness.model_fields_set) if "harness" in context.model_fields_set else {}
    return (context or {}).get("harness") or {} if isinstance(context, dict) else {}


# ===== FUNCTION: deep_research() =====
# ID: F0571 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:211-222
# ROLE: The only node: merge harness sources (defaults < configurable < context < run input), run the cached Deep Agent, and return the
#       new messages, todos, files and the harness actually used.
# INPUTS:
#   state: ResearchState, config: RunnableConfig, runtime: Runtime[HarnessConfig].
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0572 build_graph() (references)
# CALLS:
#   -> F0567 ResearchState (references)
#   -> F0569 HarnessConfig (references)
#   -> F0554 harness_of() (calls)
#   -> F0570 _context_harness() (calls)
#   -> F0566 _agent_for() (calls)
def deep_research(state: ResearchState, config: RunnableConfig, runtime: Runtime[HarnessConfig]) -> dict:
    """Run the Deep Agent configured by this run's harness settings.

    Precedence: code defaults < the assistant's configurable.harness (older assistants) < the assistant's context.harness
    (Studio's configuration panel; the presets created by scripts/langgraph_assistants.py) < the harness in this run's input
    (what SPARC sends)."""
    h = harness_of({**((config.get("configurable") or {}).get("harness") or {}), **_context_harness(runtime.context),
                    **(state.get("harness") or {})})
    run_config = {**config, "recursion_limit": h["max_steps"]}
    out = _agent_for(h).invoke({"messages": state["messages"], "todos": state.get("todos") or [], "files": state.get("files") or {}}, run_config)
    produced = out["messages"][len(state["messages"]):]
    return {"messages": produced, "todos": out.get("todos") or [], "files": out.get("files") or {}, "harness_used": h}


# ===== FUNCTION: build_graph() =====
# ID: F0572 · function · used
# ORIGINAL FILE: backend/app/deep_agent.py:225-231
# ROLE: Build the one-node research graph (context + input schemas for Studio) with optional Langfuse tracing.
# INPUTS:
#   checkpointer (optional).
# OUTPUT:
#   compiled graph.
# CALLED BY:
#   <- F0612 LocalRunner.graph() (calls)
# CALLS:
#   -> F0567 ResearchState (references)
#   -> F0569 HarnessConfig (references)
#   -> F0568 ResearchInput (references)
#   -> F0571 deep_research() (references)
#   -> F0010 langfuse_callbacks() (calls)
def build_graph(checkpointer=None):
    builder = StateGraph(ResearchState, context_schema=HarnessConfig, input_schema=ResearchInput)
    builder.add_node("deep_research", deep_research)
    builder.add_edge(START, "deep_research")
    compiled = builder.compile(checkpointer=checkpointer, name="supplier_deep_agent")
    callbacks = langfuse_callbacks()
    return compiled.with_config({"callbacks": callbacks}) if callbacks else compiled


graph = build_graph()
