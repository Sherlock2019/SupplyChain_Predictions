"""SC Agent Manager (supervisor) as a LangGraph graph, node for node the same as SCInsight-Cosmetics-Supervisor-Agentflow-v1:

    check_access -> understand (Qwen) -> safety_guard -> route -> specialist_<x> (subgraph) -> save_recommendation
        -> action proposed? -> prepare_approval -> human_approval (interrupt) -> show_decision | withdraw
                            \\-> analysis_only            (or handoff when pause_for_approval is false, e.g. called by the chat bot)

Human approval uses interrupt(): the run pauses with the recommendation id; resume with "proceed" or "reject"
(Command(resume=...), or Resume in Studio). Like Flowise, resuming is NOT the approval: the decision is read back from the
SCInsight API, where only an authorised manager can record it.
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from backend.scinsight.lg import common
from backend.scinsight.lg.specialists import GRAPHS, SPECIALISTS, last_question

ROUTE = {intent: key for key, (intent, *_rest) in SPECIALISTS.items()}  # intent -> specialist key


class Input(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    pause_for_approval: bool  # default true; false = save the recommendation and hand back (chat bot front door)


class Output(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    answer: str
    intent: str
    rec_id: str


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


def _reply(text: str) -> dict:
    return {"answer": text, "messages": [AIMessage(text)]}


def check_access(state: SupervisorState, config: RunnableConfig) -> dict:
    configurable = config.get("configurable") or {}
    thread = configurable.get("thread_id", "")
    pause = state.get("pause_for_approval")  # input wins, then the assistant's configuration, then the default (pause)
    return {"question": last_question(state.get("messages", [])), "chat_id": thread, **common.context(thread),
            "pause_for_approval": configurable.get("pause_for_approval", True) if pause is None else pause}


def stop_access(state: SupervisorState) -> dict:
    return _reply(state["ctx_message"])


def understand(state: SupervisorState) -> dict:
    reply = common.llm(20).invoke([SystemMessage(common.prompt("supervisor_classifier")), HumanMessage(f"REQUEST: {state['question']}")])
    return {"classified": common.text_of(reply)}


def safety_guard(state: SupervisorState) -> dict:
    intent, why = common.guard(state["question"], state.get("classified", ""))
    return {"intent": intent, "guard": why}


def route(state: SupervisorState) -> str:
    intent = state.get("intent", "")
    if intent in ROUTE:
        return f"specialist_{ROUTE[intent]}"
    return "refuse_sap_change" if intent == "sap_write_request" else "out_of_scope"


def specialist_node(key: str):
    def run(state: SupervisorState, config: RunnableConfig) -> dict:
        out = GRAPHS[key].invoke({"messages": [HumanMessage(state["question"])]}, config)  # subgraph: visible step by step in Studio
        return {"specialist_output": out.get("answer", "")}
    run.__name__ = f"specialist_{key}"
    return run


def refuse_sap_change(state: SupervisorState) -> dict:
    return _reply(common.SAP_READ_ONLY_REPLY)


def out_of_scope(state: SupervisorState) -> dict:
    return _reply(common.out_of_scope_reply(state.get("guard", "")))


def learning_report(state: SupervisorState) -> dict:  # learning reports end the run; they never create a recommendation
    return _reply(state.get("specialist_output", ""))


def save_recommendation(state: SupervisorState) -> dict:
    return common.save(state.get("specialist_output", ""), state.get("chat_id", ""))


def after_save(state: SupervisorState) -> str:
    if not state.get("rec_id"):
        return "analysis_only"
    return "prepare_approval" if state.get("pause_for_approval", True) else "handoff"


def analysis_only(state: SupervisorState) -> dict:
    return _reply(f"{state.get('specialist_output', '')}\n\n{state.get('save_message', '')}")


def _approval_text(state: SupervisorState) -> str:
    return (f"{state.get('specialist_output', '')}\n\n---\n{state.get('save_message', '')}\nApproval is recorded ONLY in the SCInsight API by an authorised "
            f"{state.get('reviewers', '')} with their own key (POST /api/v1/decisions/{state.get('rec_id', '')}/review).")


def handoff(state: SupervisorState) -> dict:
    return _reply(_approval_text(state) + f" Then ask for the status of {state.get('rec_id', '')}.")


def prepare_approval(state: SupervisorState) -> dict:  # message shown while the run is paused
    return _reply(_approval_text(state) + " Resume with 'proceed' to read the verified decision, or 'reject' to withdraw this recommendation.")


def human_approval(state: SupervisorState) -> dict:
    value = interrupt({"recommendation_id": state.get("rec_id"), "reviewers": state.get("reviewers"),
                       "resume_with": ["proceed", "reject"], "note": "Resuming is not an approval; the decision is read from the SCInsight API."})
    choice = value.get("type") if isinstance(value, dict) else value
    return {"approval": "reject" if str(choice).strip().lower() == "reject" else "proceed"}


def show_decision(state: SupervisorState) -> dict:
    return _reply(common.verify(state["rec_id"]))


def withdraw(state: SupervisorState) -> dict:
    return _reply(common.withdraw(state["rec_id"]))


def build_supervisor(checkpointer=None):
    g = StateGraph(SupervisorState, input_schema=Input, output_schema=Output)
    for fn in (check_access, stop_access, understand, safety_guard, refuse_sap_change, out_of_scope, learning_report, save_recommendation,
               analysis_only, handoff, prepare_approval, human_approval, show_decision, withdraw):
        g.add_node(fn.__name__, fn)
    specialists = [f"specialist_{key}" for key in SPECIALISTS]
    for key in SPECIALISTS:
        g.add_node(f"specialist_{key}", specialist_node(key))
    g.add_edge(START, "check_access")
    g.add_conditional_edges("check_access", lambda s: "understand" if s.get("ctx_ok") else "stop_access", ["understand", "stop_access"])
    g.add_edge("understand", "safety_guard")
    g.add_conditional_edges("safety_guard", route, [*specialists, "refuse_sap_change", "out_of_scope"])
    for key in SPECIALISTS:
        g.add_edge(f"specialist_{key}", "learning_report" if key == "learning" else "save_recommendation")
    g.add_conditional_edges("save_recommendation", after_save, ["analysis_only", "prepare_approval", "handoff"])
    g.add_edge("prepare_approval", "human_approval")
    g.add_conditional_edges("human_approval", lambda s: "withdraw" if s.get("approval") == "reject" else "show_decision", ["show_decision", "withdraw"])
    for end in ("stop_access", "refuse_sap_change", "out_of_scope", "learning_report", "analysis_only", "handoff", "show_decision", "withdraw"):
        g.add_edge(end, END)
    return g.compile(checkpointer=checkpointer, name="scinsight_supervisor")


graph = build_supervisor()
