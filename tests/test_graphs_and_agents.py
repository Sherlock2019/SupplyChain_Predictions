from __future__ import annotations

import pytest

from backend.app.config import Settings
from backend.app.graphs import business_graph, chat_graph
from backend.app.runner import LocalRunner


@pytest.fixture()
def runner(settings: Settings) -> LocalRunner:
    return LocalRunner(settings)


def test_graphs_have_expected_topology():
    chat_nodes = set(chat_graph.get_graph().nodes)
    assert {"guard", "refuse", "agent", "tools", "fallback"} <= chat_nodes
    business_nodes = set(business_graph.get_graph().nodes)
    assert {"intake", "validate", "factory_readiness", "stock_balance", "supplier_risk", "quality", "logistics", "approval_gate", "submit"} <= business_nodes


def test_chat_graph_guard_refuses_sap_writes(runner):
    result = runner.run("supply_chain_chat", {"messages": [{"role": "user", "content": "Please change production order 10000102 in SAP"}]})
    assert result["values"]["messages"][-1]["name"] == "guardrail"


def test_chat_graph_deterministic_fallback_keeps_thread_memory(runner):
    first = runner.run("supply_chain_chat", {"messages": [{"role": "user", "content": "rebalance FG-PERFUME-100"}]})
    assert "proposed transfer" in first["values"]["messages"][-1]["content"]
    second = runner.run("supply_chain_chat", {"messages": [{"role": "user", "content": "supplier risk for PackGlass"}]}, first["thread_id"])
    assert len(second["values"]["messages"]) == 4  # checkpointer kept the first turn
    assert "PackGlass Europe" in second["values"]["messages"][-1]["content"]


def test_business_graph_interrupts_then_submits(runner):
    started = runner.run(
        "supply_chain_business",
        {"request_type": "stock_balance", "material": "FG-PERFUME-100"},
    )
    assert started["next"] == ["approval_gate"]
    payload = started["interrupts"][0]
    assert payload["analysis_id"].startswith("AN-") and payload["proposed_actions"]
    assert started["values"]["policy_evidence"]
    finished = runner.resume("supply_chain_business", started["thread_id"], {"decision": "submit", "comment": "ok"})
    assert finished["values"]["status"] == "submitted_for_manager_review"
    assert finished["values"]["recommendation"]["status"] == "pending_review"
    assert finished["values"]["recommendation"]["actions"] == payload["proposed_actions"]


def test_business_graph_discard_and_free_text_intake(runner):
    started = runner.run("supply_chain_business", {"request_text": "Is supplier PackGlass a continuity risk?"})
    assert started["values"]["request_type"] == "supplier_risk"
    assert started["values"]["supplier"] == "PackGlass Europe"
    finished = runner.resume("supply_chain_business", started["thread_id"], {"decision": "discard"})
    assert finished["values"]["status"] == "discarded_by_planner"


def test_business_graph_rejects_invalid_and_completes_no_action(runner):
    invalid = runner.run("supply_chain_business", {"request_type": "factory_readiness", "plant": "FR20"})
    assert invalid["values"]["status"] == "invalid_request" and invalid["values"]["errors"]
    ready = runner.run("supply_chain_business", {"request_type": "factory_readiness", "plant": "FR10", "material": "FG-PERFUME-100", "quantity": 3000, "need_by": "2026-10-30"})
    assert ready["values"]["status"] == "completed_no_action_required" and not ready["interrupts"]


def test_langgraph_agentflow_topology():
    from backend.app.agentflow import graph

    nodes = set(graph.get_graph().nodes)
    assert {"sap_read", "rag_retrieve", "supervisor", "approval_gate", "boundary"} <= nodes
    roles = ["director", "demand", "production", "procurement", "warehouse", "logistics", "quality", "finance", "mlops"]
    assert {f"{r}_agent" for r in roles} <= nodes  # one specialist per SPARC business role


def test_langgraph_agentflow_routes_interrupts_and_submits(runner):
    started = runner.run("supply_chain_agentflow", {"messages": [{"role": "user", "content": "Can FR20 produce 6000 FG-SERUM-50 by 2026-10-27?"}]})
    assert started["values"]["route"] == "production"
    assert started["values"]["sap_context"]["read_only"] is True and started["values"]["sap_context"]["plants"]  # SAP read step
    assert started["values"]["knowledge"]  # RAG step (governed documents)
    payload = started["interrupts"][0]
    assert payload["analysis_id"] == started["values"]["analysis"]["analysis_id"]
    assert any(a.get("purchase_order") == "4500001002" for a in payload["proposed_actions"])
    finished = runner.resume("supply_chain_agentflow", started["thread_id"], {"decision": "submit", "comment": "ok"})
    assert finished["values"]["status"] == "submitted_for_manager_review"
    assert "manager review queue" in finished["values"]["messages"][-1]["content"]
    # same thread, next turn: procurement specialist; an advisory role (finance) never asks for approval
    research = runner.run("supply_chain_agentflow", {"messages": [{"role": "user", "content": "Is supplier PackGlass a risk?"}]}, started["thread_id"])
    assert research["values"]["route"] == "procurement"
    finance = runner.run("supply_chain_agentflow", {"messages": [{"role": "user", "content": "What is the working capital tied up in stock?"}]})
    assert finance["values"]["route"] == "finance" and not finance["interrupts"]


def test_langgraph_agentflow_boundary_and_discard(runner):
    refused = runner.run("supply_chain_agentflow", {"messages": [{"role": "user", "content": "Create a purchase order in SAP for RM-ACTIVE"}]})
    assert refused["values"]["route"] == "boundary" and refused["values"]["status"] == "refused_sap_write"
    started = runner.run("supply_chain_agentflow", {"messages": [{"role": "user", "content": "Rebalance FG-PERFUME-100 stock"}]})
    assert started["values"]["route"] == "warehouse" and started["interrupts"]
    discarded = runner.resume("supply_chain_agentflow", started["thread_id"], {"decision": "discard"})
    assert discarded["values"]["status"] == "discarded_by_planner"


def test_deep_agent_is_built_with_subagents_and_planning_tools():
    from backend.app.deep_agent import SUBAGENTS, build_deep_agent, graph

    assert {s["name"] for s in SUBAGENTS} == {"contract-analyst", "quality-analyst", "logistics-analyst"}
    assert "deep_research" in set(graph.get_graph().nodes)  # harness wrapper served by LangGraph Server
    nodes = set(build_deep_agent().get_graph().nodes)
    assert "tools" in nodes and "model" in nodes


def test_deep_agent_harness_controls_tools_subagents_steps_and_prompt():
    import pytest as _pytest
    from pydantic import ValidationError

    from backend.app.deep_agent import build_deep_agent, harness_of, system_prompt

    h = harness_of({"tools": ["supplier_risk", "search_governed_knowledge"], "subagents": ["contract-analyst"], "max_steps": 30,
                    "report_style": "executive", "require_plan": False, "temperature": 0.2})
    agent = build_deep_agent(harness=h)
    assert agent.config["recursion_limit"] == 30
    prompt = system_prompt(h)
    assert "executive summary" in prompt and "todo plan" not in prompt and "contract-analyst" in prompt and "quality-analyst" not in prompt
    none = system_prompt(harness_of({"subagents": []}))
    assert "no subagents are enabled" in none
    with _pytest.raises(ValidationError):
        harness_of({"max_steps": 5000})
    with _pytest.raises(ValidationError):
        harness_of({"tools": ["delete_purchase_order"]})


def test_harness_guard_enforces_loop_controls_per_run():
    from types import SimpleNamespace

    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    from backend.app.deep_agent import HarnessGuard, build_deep_agent, harness_of, system_prompt

    h = harness_of({"max_model_calls": 3, "max_tool_calls": 4, "max_calls_per_tool": 2, "max_subagent_calls": 0, "tool_retries": 2})
    guard = HarnessGuard(h)
    call = lambda name, i: {"name": name, "id": f"c{i}", "args": {}}  # noqa: E731
    history = [HumanMessage("old question"), AIMessage("", tool_calls=[call("supplier_risk", 0)] * 1), ToolMessage("x", tool_call_id="c0"),
               HumanMessage("Assess BioActive Labs"),  # limits count from here (new run)
               AIMessage("", tool_calls=[call("supplier_risk", 1), call("supplier_risk", 2), call("supplier_risk", 3), call("task", 4), call("write_todos", 5)])]
    tool_req = lambda c: SimpleNamespace(tool_call=c, state={"messages": history})  # noqa: E731
    executed = lambda req: "ran"  # noqa: E731
    assert guard.wrap_tool_call(tool_req(call("supplier_risk", 1)), executed) == "ran"
    assert guard.wrap_tool_call(tool_req(call("supplier_risk", 2)), executed) == "ran"
    third = guard.wrap_tool_call(tool_req(call("supplier_risk", 3)), executed)      # repeat guard: 2 per tool
    assert isinstance(third, ToolMessage) and "2 calls of supplier_risk" in third.content and third.status == "error"
    assert "subagent delegations" in guard.wrap_tool_call(tool_req(call("task", 4)), executed).content  # 0 = no delegation
    assert guard.wrap_tool_call(tool_req(call("write_todos", 5)), executed) == "ran"  # planning tools are not limited
    model_req = lambda msgs: SimpleNamespace(state={"messages": msgs})  # noqa: E731
    assert guard.wrap_model_call(model_req(history), lambda r: "model") == "model"   # 1 turn so far in this run
    stopped = guard.wrap_model_call(model_req(history + [AIMessage("a"), AIMessage("b")]), lambda r: "model")
    assert isinstance(stopped, AIMessage) and "3 model calls" in stopped.content          # graceful end, no exception
    assert "Do the research yourself" in system_prompt(h)                                # 0 delegations -> instructions say so
    agent = build_deep_agent(harness=h)
    assert agent.config["recursion_limit"] == h["max_steps"]
