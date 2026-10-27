# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py
# What this module is: the SC Agent Manager (supervisor) as a LangGraph StateGraph — node for node the same as the Flowise
# Agentflow SCInsight-Cosmetics-Supervisor-Agentflow-v1 (check access -> classify -> guard -> route -> specialist subgraph ->
# save recommendation -> human approval pause -> show verified decision / withdraw). Registered in langgraph.json.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""SC Agent Manager (supervisor) as a LangGraph graph, node for node the same as SCInsight-Cosmetics-Supervisor-Agentflow-v1:

    check_access -> understand (Qwen) -> safety_guard -> route -> specialist_<x> (subgraph) -> save_recommendation
        -> action proposed? -> prepare_approval -> human_approval (interrupt) -> show_decision | withdraw
                            \\-> analysis_only            (or handoff when pause_for_approval is false, e.g. called by the chat bot)

Human approval uses interrupt(): the run pauses with the recommendation id; resume with "proceed" or "reject"
(Command(resume=...), or Resume in Studio). Like Flowise, resuming is NOT the approval: the decision is read back from the
SCInsight API, where only an authorised manager can record it.
"""
from __future__ import annotations

# Annotated[list, add_messages]: a state field whose updates are MERGED by the add_messages reducer (append, replace by id).
# TypedDict: typed dict schema of the graph state; total=False = every key optional.
from typing import Annotated, TypedDict

# LangChain message classes used to talk to the model and to write replies into the state.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
# RunnableConfig: per-run configuration (thread_id, assistant configurable values).
from langchain_core.runnables import RunnableConfig
# END / START: special node names; StateGraph: the graph builder.
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
# interrupt(): pauses the graph (checkpointed) until it is resumed with a value.
from langgraph.types import interrupt

from backend.scinsight.lg import common
from backend.scinsight.lg.specialists import GRAPHS, SPECIALISTS, last_question

# intent -> specialist key, e.g. "factory_planning" -> "factory". `(intent, *_rest)` unpacks the first tuple element.
ROUTE = {intent: key for key, (intent, *_rest) in SPECIALISTS.items()}  # intent -> specialist key


# ===== CLASS: Input =====
# ID: F0699 · class · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:27-29
# ROLE: Public input schema of the graph (what a caller may send).
# FIELDS:
#   messages: conversation messages (merged with add_messages).
#   pause_for_approval: bool -> False = save and hand back instead of pausing (used by the chat bot tool).
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   (none found)
class Input(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    pause_for_approval: bool  # default true; false = save the recommendation and hand back (chat bot front door)


# ===== CLASS: Output =====
# ID: F0700 · class · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:32-36
# ROLE: Public output schema (what a caller receives).
# FIELDS:
#   messages, answer: str, intent: str, rec_id: str.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   (none found)
class Output(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    answer: str
    intent: str
    rec_id: str


# ===== CLASS: SupervisorState =====
# ID: F0701 · class · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:39-53
# ROLE: Full internal state = Input + Output + working fields (multiple inheritance of TypedDicts merges their keys).
# FIELDS:
#   question, chat_id, ctx_ok, ctx_message, snapshot_id, catalog, classified, guard, specialist_output,
#   rec_domain, rec_status, reviewers, save_message, approval.
# CALLED BY:
#   <- F0703 check_access() (references)
#   <- F0704 stop_access() (references)
#   <- F0705 understand() (references)
#   <- F0706 safety_guard() (references)
#   <- F0707 route() (references)
#   <- F0709 specialist_node.run() (references)
#   <- F0710 refuse_sap_change() (references)
#   <- F0711 out_of_scope() (references)
#   <- F0712 learning_report() (references)
#   <- F0713 save_recommendation() (references)
#   <- F0714 after_save() (references)
#   <- F0715 analysis_only() (references)
# CALLS:
#   (none found)
class SupervisorState(Input, Output, total=False):
    question: str
    chat_id: str
    ctx_ok: bool
    ctx_message: str
    snapshot_id: str
    catalog: str
    classified: str
    guard: str
    specialist_output: str
    rec_domain: str
    rec_status: str
    reviewers: str
    save_message: str
    approval: str


# ===== FUNCTION: _reply() =====
# ID: F0702 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:56-57
# ROLE: State update for a final reply: sets "answer" and appends an AIMessage.
# INPUTS:
#   text: str.
# OUTPUT:
#   dict -> partial state update.
# CALLED BY:
#   <- F0704 stop_access() (calls)
#   <- F0710 refuse_sap_change() (calls)
#   <- F0711 out_of_scope() (calls)
#   <- F0712 learning_report() (calls)
#   <- F0715 analysis_only() (calls)
#   <- F0717 handoff() (calls)
#   <- F0718 prepare_approval() (calls)
#   <- F0720 show_decision() (calls)
#   <- F0721 withdraw() (calls)
# CALLS:
#   (none found)
def _reply(text: str) -> dict:
    return {"answer": text, "messages": [AIMessage(text)]}


# ===== FUNCTION: check_access() =====
# ID: F0703 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:60-65
# ROLE: Node 1 (Flowise "2 · Check access"): last user question + SCInsight context check + pause setting.
# INPUTS:
#   state: SupervisorState, config: RunnableConfig (thread_id, configurable.pause_for_approval).
# OUTPUT:
#   dict -> question, chat_id, ctx_ok, ctx_message, snapshot_id, catalog, pause_for_approval.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0689 last_question() (calls)
#   -> F0656 context() (calls)
def check_access(state: SupervisorState, config: RunnableConfig) -> dict:
    configurable = config.get("configurable") or {}
    thread = configurable.get("thread_id", "")
    pause = state.get("pause_for_approval")  # input wins, then the assistant's configuration, then the default (pause)
    # **common.context(thread) merges the context-check result into the update.
    return {"question": last_question(state.get("messages", [])), "chat_id": thread, **common.context(thread),
            "pause_for_approval": configurable.get("pause_for_approval", True) if pause is None else pause}


# ===== FUNCTION: stop_access() =====
# ID: F0704 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:68-69
# ROLE: Stop node when the context check failed ("Stop · access refused").
# INPUTS:
#   state.
# OUTPUT:
#   dict -> reply with ctx_message.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
def stop_access(state: SupervisorState) -> dict:
    return _reply(state["ctx_message"])


# ===== FUNCTION: understand() =====
# ID: F0705 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:72-74
# ROLE: Node 2 (Flowise "3 · Understand the request"): Qwen classifies the question into one intent (max 20 tokens).
# INPUTS:
#   state (question).
# OUTPUT:
#   dict -> {"classified": raw model text}.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0642 llm() (calls)
#   -> F0643 prompt() (calls)
#   -> F0646 text_of() (calls)
def understand(state: SupervisorState) -> dict:
    reply = common.llm(20).invoke([SystemMessage(common.prompt("supervisor_classifier")), HumanMessage(f"REQUEST: {state['question']}")])
    return {"classified": common.text_of(reply)}


# ===== FUNCTION: safety_guard() =====
# ID: F0706 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:77-79
# ROLE: Node 3 (Flowise "4 · Safety guard"): deterministic guard over the classifier output.
# INPUTS:
#   state (question, classified).
# OUTPUT:
#   dict -> {"intent", "guard"}.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0682 guard() (calls)
def safety_guard(state: SupervisorState) -> dict:
    intent, why = common.guard(state["question"], state.get("classified", ""))
    return {"intent": intent, "guard": why}


# ===== FUNCTION: route() =====
# ID: F0707 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:82-86
# ROLE: Router (Flowise "5 · Route to a specialist"): name of the next node for the intent.
# INPUTS:
#   state (intent).
# OUTPUT:
#   str -> "specialist_<key>" | "refuse_sap_change" | "out_of_scope".
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
def route(state: SupervisorState) -> str:
    intent = state.get("intent", "")
    if intent in ROUTE:
        return f"specialist_{ROUTE[intent]}"
    return "refuse_sap_change" if intent == "sap_write_request" else "out_of_scope"


# ===== FUNCTION: specialist_node() =====
# ID: F0708 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:89-94
# ROLE: Factory returning a node function that runs one specialist SUBGRAPH with the question (Flowise "6 · Specialist").
# INPUTS:
#   key: str -> specialist key.
# OUTPUT:
#   callable run(state, config) -> {"specialist_output": answer}.
# CALLED BY:
#   <- F0722 build_supervisor() (calls)
# CALLS:
#   -> F0709 specialist_node.run() (references)
def specialist_node(key: str):
    # ===== FUNCTION: specialist_node.run() =====
    # ID: F0709 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/supervisor.py:90-92
    # ROLE: The node: invoke the compiled specialist graph and keep its final answer.
    # INPUTS:
    #   state, config (passed through so the subgraph shares the thread / tracing).
    # OUTPUT:
    #   dict -> {"specialist_output": str}.
    # CALLED BY:
    #   <- F0708 specialist_node() (references)
    # CALLS:
    #   -> F0701 SupervisorState (references)
    def run(state: SupervisorState, config: RunnableConfig) -> dict:
        out = GRAPHS[key].invoke({"messages": [HumanMessage(state["question"])]}, config)  # subgraph: visible step by step in Studio
        return {"specialist_output": out.get("answer", "")}
    # A readable function name for traces / Studio.
    run.__name__ = f"specialist_{key}"
    return run


# ===== FUNCTION: refuse_sap_change() =====
# ID: F0710 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:97-98
# ROLE: Refusal node for SAP write requests ("Stop · SAP change refused").
# INPUTS:
#   state.
# OUTPUT:
#   dict -> fixed read-only reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
def refuse_sap_change(state: SupervisorState) -> dict:
    return _reply(common.SAP_READ_ONLY_REPLY)


# ===== FUNCTION: out_of_scope() =====
# ID: F0711 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:101-102
# ROLE: Out-of-scope node ("Stop · out of scope"), includes the guard reason.
# INPUTS:
#   state (guard).
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
#   -> F0637 out_of_scope_reply() (calls)
def out_of_scope(state: SupervisorState) -> dict:
    return _reply(common.out_of_scope_reply(state.get("guard", "")))


# ===== FUNCTION: learning_report() =====
# ID: F0712 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:105-106
# ROLE: End node for the learning specialist: its report is returned as is (no recommendation is created).
# INPUTS:
#   state (specialist_output).
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
def learning_report(state: SupervisorState) -> dict:  # learning reports end the run; they never create a recommendation
    return _reply(state.get("specialist_output", ""))


# ===== FUNCTION: save_recommendation() =====
# ID: F0713 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:109-110
# ROLE: Node "7 · Save recommendation": common.save() verifies the CALC id and creates the pending recommendation.
# INPUTS:
#   state (specialist_output, chat_id).
# OUTPUT:
#   dict -> rec_id, rec_domain, rec_status, reviewers, save_message.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0683 save() (calls)
def save_recommendation(state: SupervisorState) -> dict:
    return common.save(state.get("specialist_output", ""), state.get("chat_id", ""))


# ===== FUNCTION: after_save() =====
# ID: F0714 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:113-116
# ROLE: Router "8 · Action proposed?": no recommendation -> analysis only; else pause for approval or hand off (chat bot).
# INPUTS:
#   state (rec_id, pause_for_approval).
# OUTPUT:
#   str -> "analysis_only" | "prepare_approval" | "handoff".
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
def after_save(state: SupervisorState) -> str:
    if not state.get("rec_id"):
        return "analysis_only"
    return "prepare_approval" if state.get("pause_for_approval", True) else "handoff"


# ===== FUNCTION: analysis_only() =====
# ID: F0715 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:119-120
# ROLE: End node "End · analysis only": specialist answer + save message.
# INPUTS:
#   state.
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
def analysis_only(state: SupervisorState) -> dict:
    return _reply(f"{state.get('specialist_output', '')}\n\n{state.get('save_message', '')}")


# ===== FUNCTION: _approval_text() =====
# ID: F0716 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:123-125
# ROLE: Text shown with a saved recommendation: analysis + who must approve, and where (the SCInsight API review endpoint).
# INPUTS:
#   state.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0717 handoff() (calls)
#   <- F0718 prepare_approval() (calls)
# CALLS:
#   -> F0701 SupervisorState (references)
def _approval_text(state: SupervisorState) -> str:
    return (f"{state.get('specialist_output', '')}\n\n---\n{state.get('save_message', '')}\nApproval is recorded ONLY in the SCInsight API by an authorised "
            f"{state.get('reviewers', '')} with their own key (POST /api/v1/decisions/{state.get('rec_id', '')}/review).")


# ===== FUNCTION: handoff() =====
# ID: F0717 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:128-129
# ROLE: End node when called without pausing (chat bot): approval text + "ask for the status later".
# INPUTS:
#   state.
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
#   -> F0716 _approval_text() (calls)
def handoff(state: SupervisorState) -> dict:
    return _reply(_approval_text(state) + f" Then ask for the status of {state.get('rec_id', '')}.")


# ===== FUNCTION: prepare_approval() =====
# ID: F0718 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:132-133
# ROLE: Message shown while the run is paused for approval.
# INPUTS:
#   state.
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
#   -> F0716 _approval_text() (calls)
def prepare_approval(state: SupervisorState) -> dict:  # message shown while the run is paused
    return _reply(_approval_text(state) + " Resume with 'proceed' to read the verified decision, or 'reject' to withdraw this recommendation.")


# ===== FUNCTION: human_approval() =====
# ID: F0719 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:136-140
# ROLE: Node "9 · Human approval (pause)": interrupt() checkpoints the run; on resume, the value decides proceed / reject.
#       Resuming is NOT an approval — show_decision reads the real decision from the API.
# INPUTS:
#   state (rec_id, reviewers).
# OUTPUT:
#   dict -> {"approval": "proceed" | "reject"}.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
def human_approval(state: SupervisorState) -> dict:
    # The dict passed to interrupt() is what Studio / the caller sees while paused.
    value = interrupt({"recommendation_id": state.get("rec_id"), "reviewers": state.get("reviewers"),
                       "resume_with": ["proceed", "reject"], "note": "Resuming is not an approval; the decision is read from the SCInsight API."})
    # Accept {"type": "reject"} or a plain "reject" string.
    choice = value.get("type") if isinstance(value, dict) else value
    return {"approval": "reject" if str(choice).strip().lower() == "reject" else "proceed"}


# ===== FUNCTION: show_decision() =====
# ID: F0720 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:143-144
# ROLE: Node "10 · Show the verified decision": common.verify() reads the review status from the API.
# INPUTS:
#   state (rec_id).
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
#   -> F0684 verify() (calls)
def show_decision(state: SupervisorState) -> dict:
    return _reply(common.verify(state["rec_id"]))


# ===== FUNCTION: withdraw() =====
# ID: F0721 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:147-148
# ROLE: Node "10 · Withdraw": common.withdraw() withdraws the pending recommendation.
# INPUTS:
#   state (rec_id).
# OUTPUT:
#   dict -> reply.
# CALLED BY:
#   <- F0722 build_supervisor() (references)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0702 _reply() (calls)
#   -> F0685 withdraw() (calls)
def withdraw(state: SupervisorState) -> dict:
    return _reply(common.withdraw(state["rec_id"]))


# ===== FUNCTION: build_supervisor() =====
# ID: F0722 · function · used
# ORIGINAL FILE: backend/scinsight/lg/supervisor.py:151-170
# ROLE: Build and compile the supervisor graph: register the nodes, the 7 specialist subgraph nodes and all (conditional) edges.
# INPUTS:
#   checkpointer -> optional LangGraph checkpointer (needed for interrupt/resume; the LangGraph server provides one).
# OUTPUT:
#   compiled graph named "scinsight_supervisor".
# CALLED BY:
#   <- F0810 test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api() (calls)
#   <- F0811 test_supervisor_reject_withdraws_and_guards_refuse() (calls)
# CALLS:
#   -> F0701 SupervisorState (references)
#   -> F0699 Input (references)
#   -> F0700 Output (references)
#   -> F0703 check_access() (references)
#   -> F0704 stop_access() (references)
#   -> F0705 understand() (references)
#   -> F0706 safety_guard() (references)
#   -> F0710 refuse_sap_change() (references)
#   -> F0711 out_of_scope() (references)
#   -> F0712 learning_report() (references)
#   -> F0713 save_recommendation() (references)
#   -> F0715 analysis_only() (references)
def build_supervisor(checkpointer=None):
    # input_schema / output_schema restrict what callers send and receive.
    g = StateGraph(SupervisorState, input_schema=Input, output_schema=Output)
    # Register each plain node under its function name.
    for fn in (check_access, stop_access, understand, safety_guard, refuse_sap_change, out_of_scope, learning_report, save_recommendation,
               analysis_only, handoff, prepare_approval, human_approval, show_decision, withdraw):
        g.add_node(fn.__name__, fn)
    specialists = [f"specialist_{key}" for key in SPECIALISTS]
    for key in SPECIALISTS:
        g.add_node(f"specialist_{key}", specialist_node(key))
    g.add_edge(START, "check_access")
    # Conditional edge: the lambda returns the next node name; the list declares the possible targets (for the drawn graph).
    g.add_conditional_edges("check_access", lambda s: "understand" if s.get("ctx_ok") else "stop_access", ["understand", "stop_access"])
    g.add_edge("understand", "safety_guard")
    g.add_conditional_edges("safety_guard", route, [*specialists, "refuse_sap_change", "out_of_scope"])
    for key in SPECIALISTS:
        g.add_edge(f"specialist_{key}", "learning_report" if key == "learning" else "save_recommendation")
    g.add_conditional_edges("save_recommendation", after_save, ["analysis_only", "prepare_approval", "handoff"])
    g.add_edge("prepare_approval", "human_approval")
    g.add_conditional_edges("human_approval", lambda s: "withdraw" if s.get("approval") == "reject" else "show_decision", ["show_decision", "withdraw"])
    # Every terminal node goes to END.
    for end in ("stop_access", "refuse_sap_change", "out_of_scope", "learning_report", "analysis_only", "handoff", "show_decision", "withdraw"):
        g.add_edge(end, END)
    return g.compile(checkpointer=checkpointer, name="scinsight_supervisor")


# Module-level compiled graph: langgraph.json points at backend/scinsight/lg/supervisor.py:graph.
graph = build_supervisor()
