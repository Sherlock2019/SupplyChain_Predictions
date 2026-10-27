# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/lg/specialists.py
# What this module is: the 7 SCInsight specialists as LangGraph subgraphs, step for step the same as the 7 Flowise specialist
# Agentflows: check access -> [read request (Qwen)] -> calculate (SCInsight API) -> [policy search] -> [write answer (Qwen)]
# -> check numbers (evidence gate). Each compiled graph is also exposed on its own in LangGraph Studio (langgraph.json).
# Only comment lines were added (AST-verified).
# ======================================================================================================

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
    # Learning: no reviewers, no policy topic, no LLM extraction (REC ids are read deterministically).
    "learning": ("outcome_learning", "Decision Outcome Learning specialist", "", "", False),
}


# ===== CLASS: Input =====
# ID: F0686 · class · used
# ORIGINAL FILE: backend/scinsight/lg/specialists.py:38-39
# ROLE: Specialist input schema.
# FIELDS:
#   messages (merged with add_messages).
# CALLED BY:
#   <- F0690 build_specialist() (references)
# CALLS:
#   (none found)
class Input(TypedDict, total=False):
    messages: Annotated[list, add_messages]


# ===== CLASS: Output =====
# ID: F0687 · class · used
# ORIGINAL FILE: backend/scinsight/lg/specialists.py:42-45
# ROLE: Specialist output schema.
# FIELDS:
#   messages, answer: str, calc_id: str.
# CALLED BY:
#   <- F0690 build_specialist() (references)
# CALLS:
#   (none found)
class Output(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    answer: str
    calc_id: str


# ===== CLASS: SpecialistState =====
# ID: F0688 · class · used
# ORIGINAL FILE: backend/scinsight/lg/specialists.py:48-63
# ROLE: Internal specialist state (same keys as the Flowise flow state).
# FIELDS:
#   question, ctx_ok, ctx_message, snapshot_id, catalog, extracted, calc_ok, calc_kind, calc_has_actions, calc_summary,
#   calc_evidence, calc_message, policy, citations, draft.
# CALLED BY:
#   <- F0690 build_specialist() (references)
#   <- F0691 build_specialist.check_access() (references)
#   <- F0692 build_specialist.stop_access() (references)
#   <- F0693 build_specialist.read_request() (references)
#   <- F0694 build_specialist.calculate() (references)
#   <- F0695 build_specialist.stop_input() (references)
#   <- F0696 build_specialist.policy_search() (references)
#   <- F0697 build_specialist.write_answer() (references)
#   <- F0698 build_specialist.check_numbers() (references)
# CALLS:
#   (none found)
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


# ===== FUNCTION: last_question() =====
# ID: F0689 · function · used
# ORIGINAL FILE: backend/scinsight/lg/specialists.py:66-67
# ROLE: Text of the most recent human message (the question).
# INPUTS:
#   messages: list -> LangChain messages (or dicts converted by LangGraph).
# OUTPUT:
#   str -> question, or "".
# CALLED BY:
#   <- F0691 build_specialist.check_access() (calls)
#   <- F0703 check_access() (calls)
# CALLS:
#   -> F0646 text_of() (calls)
def last_question(messages: list) -> str:
    # reversed(): newest first; next(..., "") returns "" when no human message exists.
    return next((common.text_of(m) for m in reversed(messages) if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human"), "")


# ===== FUNCTION: build_specialist() =====
# ID: F0690 · function · used
# ORIGINAL FILE: backend/scinsight/lg/specialists.py:70-128
# ROLE: Build and compile one specialist graph from its SPECIALISTS entry; nodes are closures that capture key/topic/reviewers.
# INPUTS:
#   key: str -> specialist key, checkpointer -> optional.
# OUTPUT:
#   compiled graph named "scinsight_<graph name>".
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0688 SpecialistState (references)
#   -> F0686 Input (references)
#   -> F0687 Output (references)
#   -> F0691 build_specialist.check_access() (references)
#   -> F0692 build_specialist.stop_access() (references)
#   -> F0694 build_specialist.calculate() (references)
#   -> F0695 build_specialist.stop_input() (references)
#   -> F0698 build_specialist.check_numbers() (references)
#   -> F0693 build_specialist.read_request() (references)
#   -> F0696 build_specialist.policy_search() (references)
#   -> F0697 build_specialist.write_answer() (references)
def build_specialist(key: str, checkpointer=None):
    # Tuple unpacking of the specialist definition.
    name, role, reviewers, topic, extract = SPECIALISTS[key]

    # ===== FUNCTION: build_specialist.check_access() =====
    # ID: F0691 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:73-75
    # ROLE: "1 · Start / Check access": question + SCInsight context check (catalog for the prompts).
    # INPUTS:
    #   state, config (thread_id).
    # OUTPUT:
    #   dict -> question, ctx_ok, ctx_message, snapshot_id, catalog.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0689 last_question() (calls)
    #   -> F0656 context() (calls)
    def check_access(state: SpecialistState, config: RunnableConfig) -> dict:
        question = last_question(state.get("messages", []))
        return {"question": question, **common.context((config.get("configurable") or {}).get("thread_id", ""))}

    # ===== FUNCTION: build_specialist.stop_access() =====
    # ID: F0692 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:77-78
    # ROLE: "Stop · access refused".
    # INPUTS:
    #   state.
    # OUTPUT:
    #   dict -> answer + AIMessage with ctx_message.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    def stop_access(state: SpecialistState) -> dict:
        return {"answer": state["ctx_message"], "messages": [AIMessage(state["ctx_message"])]}

    # ===== FUNCTION: build_specialist.read_request() =====
    # ID: F0693 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:80-83
    # ROLE: "Read the request (LLM)": Qwen extracts identifiers as JSON using the catalog (max 300 tokens), parsed leniently.
    # INPUTS:
    #   state (question, catalog).
    # OUTPUT:
    #   dict -> {"extracted": dict}.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0645 fill() (calls)
    #   -> F0643 prompt() (calls)
    #   -> F0642 llm() (calls)
    #   -> F0662 parse_extracted() (calls)
    #   -> F0646 text_of() (calls)
    def read_request(state: SpecialistState) -> dict:
        system = common.fill(common.prompt(f"{key}_extract"), catalog=state.get("catalog", ""))
        reply = common.llm(300).invoke([SystemMessage(system), HumanMessage(f"QUESTION: {state['question']}")])
        return {"extracted": common.parse_extracted(common.text_of(reply))}

    # ===== FUNCTION: build_specialist.calculate() =====
    # ID: F0694 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:85-87
    # ROLE: "Calculate with SAP data": merge code-detected + extracted identifiers, then call this specialist's calc_* function.
    # INPUTS:
    #   state (question, catalog, extracted).
    # OUTPUT:
    #   dict -> calc_* state keys (_done / _fail).
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0661 merge_identifiers() (calls)
    #   -> F0659 detect_codes() (calls)
    def calculate(state: SpecialistState) -> dict:
        identifiers = common.merge_identifiers(common.detect_codes(state["question"], state.get("catalog", "")), state.get("extracted") or {})
        return common.CALCULATE[key](identifiers, state["question"])

    # ===== FUNCTION: build_specialist.stop_input() =====
    # ID: F0695 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:89-90
    # ROLE: "Stop · missing input": ask for what is missing / show the API error.
    # INPUTS:
    #   state.
    # OUTPUT:
    #   dict -> answer + AIMessage with calc_message.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    def stop_input(state: SpecialistState) -> dict:
        return {"answer": state["calc_message"], "messages": [AIMessage(state["calc_message"])]}

    # ===== FUNCTION: build_specialist.policy_search() =====
    # ID: F0696 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:92-93
    # ROLE: "Policy search (RAG)".
    # INPUTS:
    #   state (question).
    # OUTPUT:
    #   dict -> policy, citations.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0678 policy() (calls)
    def policy_search(state: SpecialistState) -> dict:
        return common.policy(topic, state["question"])

    # ===== FUNCTION: build_specialist.write_answer() =====
    # ID: F0697 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:95-99
    # ROLE: "Write the answer (LLM)": Qwen explains using ONLY the calculation summary and policy excerpts (max 900 tokens).
    # INPUTS:
    #   state (question, calc_summary, policy).
    # OUTPUT:
    #   dict -> {"draft": str}.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0644 explain_prompt() (calls)
    #   -> F0642 llm() (calls)
    #   -> F0645 fill() (calls)
    #   -> F0646 text_of() (calls)
    def write_answer(state: SpecialistState) -> dict:
        system, user = common.explain_prompt(key)
        reply = common.llm(900).invoke([SystemMessage(system), HumanMessage(common.fill(user, question=state["question"], calc_summary=state.get("calc_summary", ""),
                                                                                        policy=state.get("policy", "")))])
        return {"draft": common.text_of(reply)}

    # ===== FUNCTION: build_specialist.check_numbers() =====
    # ID: F0698 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/specialists.py:101-103
    # ROLE: "Check every number": evidence gate on the draft; adds CALC id, snapshot, citations, approval note.
    # INPUTS:
    #   state (draft + calc/policy keys).
    # OUTPUT:
    #   dict -> answer + AIMessage.
    # CALLED BY:
    #   <- F0690 build_specialist() (references)
    # CALLS:
    #   -> F0688 SpecialistState (references)
    #   -> F0681 gate() (calls)
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
    # Specialists with extraction go through the LLM step first; learning goes straight to calculate.
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


# The 7 compiled specialist graphs (module level: referenced from langgraph.json and by the supervisor).
factory_planning = build_specialist("factory")
procurement = build_specialist("procurement")
warehouse = build_specialist("warehouse")
inventory_optimizer = build_specialist("inventory")
logistics = build_specialist("logistics")
quality = build_specialist("quality")
outcome_learning = build_specialist("learning")
GRAPHS = {"factory": factory_planning, "procurement": procurement, "warehouse": warehouse, "inventory": inventory_optimizer,
          "logistics": logistics, "quality": quality, "learning": outcome_learning}
