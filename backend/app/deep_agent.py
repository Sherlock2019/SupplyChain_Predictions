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

from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware, ToolRetryMiddleware
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, MessagesState, StateGraph

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

TOOLS = {t.name: t for t in (supplier_risk, sap_snapshot, search_governed_knowledge, quality_status, logistics_status, factory_material_readiness)}

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


def harness_of(value: dict | None) -> dict:
    """Validated harness: stored settings merged over the defaults (invalid or unknown values are rejected)."""
    return DeepAgentHarness(**{**DEFAULT_HARNESS, **(value or {})}).model_dump()


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


def _this_run(messages: list) -> list:
    """Messages of the current run: everything after the last user message (limits reset on every new request)."""
    start = max((i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=-1)
    return messages[start + 1:]


class HarnessGuard(AgentMiddleware):
    """Loop controls of the harness, enforced around each model and tool call (no extra graph steps).

    Counts come from the run's own message history, so they are exact and reset per request. Hitting a limit never
    raises: a model-call limit ends the run with a final note; a tool limit answers the call with a "limit reached"
    result so the agent finishes with what it already has. Deep Agents' own planning / scratch-file tools are not counted.
    """

    def __init__(self, h: dict):
        super().__init__()
        self.h = h

    def _stop_message(self, request) -> AIMessage | None:
        turns = sum(1 for m in _this_run(request.state.get("messages", [])) if isinstance(m, AIMessage))
        if turns < self.h["max_model_calls"]:
            return None
        return AIMessage(content=f"Stopped by the harness: the limit of {self.h['max_model_calls']} model calls for one run was reached. "
                                 "The findings above are what was gathered so far; raise 'Max model calls' or narrow the question for a fuller report.")

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

    def wrap_model_call(self, request, handler):
        return self._stop_message(request) or handler(request)

    async def awrap_model_call(self, request, handler):
        return self._stop_message(request) or await handler(request)

    def wrap_tool_call(self, request, handler):
        return self._refusal(request) or handler(request)

    async def awrap_tool_call(self, request, handler):
        return self._refusal(request) or await handler(request)


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


_AGENTS: dict[str, object] = {}


def _agent_for(h: dict):
    key = json.dumps(h, sort_keys=True)
    if key not in _AGENTS:
        _AGENTS[key] = build_deep_agent(harness=h)
    return _AGENTS[key]


class ResearchState(MessagesState, total=False):
    harness: dict
    harness_used: dict
    todos: list
    files: dict


def deep_research(state: ResearchState, config: RunnableConfig) -> dict:
    """Run the Deep Agent configured by this run's harness settings.

    Precedence: code defaults < the LangGraph assistant's configuration (configurable.harness, e.g. the presets created by
    scripts/langgraph_assistants.py and chosen in Studio) < the harness passed in this run's input (what SPARC sends)."""
    h = harness_of({**((config.get("configurable") or {}).get("harness") or {}), **(state.get("harness") or {})})
    run_config = {**config, "recursion_limit": h["max_steps"]}
    out = _agent_for(h).invoke({"messages": state["messages"], "todos": state.get("todos") or [], "files": state.get("files") or {}}, run_config)
    produced = out["messages"][len(state["messages"]):]
    return {"messages": produced, "todos": out.get("todos") or [], "files": out.get("files") or {}, "harness_used": h}


def build_graph(checkpointer=None):
    builder = StateGraph(ResearchState)
    builder.add_node("deep_research", deep_research)
    builder.add_edge(START, "deep_research")
    compiled = builder.compile(checkpointer=checkpointer, name="supplier_deep_agent")
    callbacks = langfuse_callbacks()
    return compiled.with_config({"callbacks": callbacks}) if callbacks else compiled


graph = build_graph()
