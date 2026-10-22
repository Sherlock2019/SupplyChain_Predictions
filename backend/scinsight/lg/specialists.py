"""The 7 SCInsight specialists as LangGraph subgraphs, step for step the same as the Flowise specialist Agentflows:

    check_access -> [read_request (Qwen)] -> calculate (SCInsight API) -> [policy_search] -> [write_answer (Qwen)] -> check_numbers
                 \\-> stop_access                                  \\-> stop_input

Same API calls, same prompts (flowise/prompts/*.md), same number check. Each compiles to its own graph for LangGraph Studio
(scinsight_<name> in langgraph.json); the supervisor calls them as subgraphs.
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from backend.scinsight.lg import common

# key -> (graph name, role, review authority, policy topic, needs identifier extraction). Mirrors SPECIALISTS in build-scinsight.cjs.
SPECIALISTS = {
    "factory": ("factory_planning", "Factory Planning specialist (production planner)", "production_planner or supply_chain_director",
                "production order bill of materials material shortage partial production rescheduling approved supplier", True),
    "procurement": ("procurement", "Procurement specialist (procurement manager)", "procurement_manager or supply_chain_director",
                    "procurement policy approved supplier lead time purchase order supplier agreement expedite", True),
    "warehouse": ("warehouse", "Warehouse specialist (warehouse manager)", "warehouse_manager or supply_chain_director",
                  "warehouse transfer policy days of cover minimum shelf life FEFO reserved stock", True),
    "inventory": ("inventory_optimizer", "Inventory Optimizer specialist", "warehouse_manager or supply_chain_director (procurement_manager for material purchases)",
                  "replenishment days of cover safety stock allocation demand forecast", True),
    "logistics": ("logistics", "Logistics specialist (logistics manager)", "warehouse_manager or supply_chain_director (logistics_manager is consulted for the lane)",
                  "transport lane transit time freight cost transfer policy", True),
    "quality": ("quality", "Quality specialist (quality manager)", "quality_manager or supply_chain_director",
                "batch release quality inspection blocked stock expiry FEFO destruction review", True),
    "learning": ("outcome_learning", "Decision Outcome Learning specialist", "", "", False),
}


class Input(TypedDict, total=False):
    messages: Annotated[list, add_messages]


class Output(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    answer: str
    calc_id: str


class SpecialistState(Input, Output, total=False):
    question: str
    ctx_ok: bool
    ctx_message: str
    snapshot_id: str
    catalog: str
    extracted: dict
    calc_ok: bool
    calc_kind: str
    calc_has_actions: bool
    calc_summary: str
    calc_evidence: str
    calc_message: str
    policy: str
    citations: str
    draft: str


def last_question(messages: list) -> str:
    return next((common.text_of(m) for m in reversed(messages) if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human"), "")


def build_specialist(key: str, checkpointer=None):
    name, role, reviewers, topic, extract = SPECIALISTS[key]

    def check_access(state: SpecialistState, config: RunnableConfig) -> dict:
        question = last_question(state.get("messages", []))
        return {"question": question, **common.context((config.get("configurable") or {}).get("thread_id", ""))}

    def stop_access(state: SpecialistState) -> dict:
        return {"answer": state["ctx_message"], "messages": [AIMessage(state["ctx_message"])]}

    def read_request(state: SpecialistState) -> dict:
        system = common.fill(common.prompt(f"{key}_extract"), catalog=state.get("catalog", ""))
        reply = common.llm(300).invoke([SystemMessage(system), HumanMessage(f"QUESTION: {state['question']}")])
        return {"extracted": common.parse_extracted(common.text_of(reply))}

    def calculate(state: SpecialistState) -> dict:
        identifiers = common.merge_identifiers(common.detect_codes(state["question"], state.get("catalog", "")), state.get("extracted") or {})
        return common.CALCULATE[key](identifiers, state["question"])

    def stop_input(state: SpecialistState) -> dict:
        return {"answer": state["calc_message"], "messages": [AIMessage(state["calc_message"])]}

    def policy_search(state: SpecialistState) -> dict:
        return common.policy(topic, state["question"])

    def write_answer(state: SpecialistState) -> dict:
        system, user = common.explain_prompt(key)
        reply = common.llm(900).invoke([SystemMessage(system), HumanMessage(common.fill(user, question=state["question"], calc_summary=state.get("calc_summary", ""),
                                                                                        policy=state.get("policy", "")))])
        return {"draft": common.text_of(reply)}

    def check_numbers(state: SpecialistState) -> dict:
        answer = common.gate(state.get("draft", ""), state, state["question"], reviewers or "n/a")
        return {"answer": answer, "messages": [AIMessage(answer)]}

    g = StateGraph(SpecialistState, input_schema=Input, output_schema=Output)
    g.add_node("check_access", check_access)
    g.add_node("stop_access", stop_access)
    g.add_node("calculate", calculate)
    g.add_node("stop_input", stop_input)
    g.add_node("check_numbers", check_numbers)
    g.add_edge(START, "check_access")
    first = "read_request" if extract else "calculate"
    g.add_conditional_edges("check_access", lambda s: first if s.get("ctx_ok") else "stop_access", [first, "stop_access"])
    if extract:
        g.add_node("read_request", read_request)
        g.add_edge("read_request", "calculate")
    after_calc = "policy_search" if topic else ("write_answer" if key != "learning" else "check_numbers")
    g.add_conditional_edges("calculate", lambda s: after_calc if s.get("calc_ok") else "stop_input", [after_calc, "stop_input"])
    if topic:
        g.add_node("policy_search", policy_search)
        g.add_edge("policy_search", "write_answer")
    if key != "learning":  # the learning report stays deterministic (a 7B model mis-stated prediction errors when rewording it)
        g.add_node("write_answer", write_answer)
        g.add_edge("write_answer", "check_numbers")
    g.add_edge("check_numbers", END)
    g.add_edge("stop_access", END)
    g.add_edge("stop_input", END)
    return g.compile(checkpointer=checkpointer, name=f"scinsight_{name}")


factory_planning = build_specialist("factory")
procurement = build_specialist("procurement")
warehouse = build_specialist("warehouse")
inventory_optimizer = build_specialist("inventory")
logistics = build_specialist("logistics")
quality = build_specialist("quality")
outcome_learning = build_specialist("learning")
GRAPHS = {"factory": factory_planning, "procurement": procurement, "warehouse": warehouse, "inventory": inventory_optimizer,
          "logistics": logistics, "quality": quality, "learning": outcome_learning}
