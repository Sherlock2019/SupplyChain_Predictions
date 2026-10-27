"""TEMPLATE — a LangGraph graph served by LangGraph Server, the pattern of backend/scinsight/lg/supervisor.py and
backend/app/graphs.py.

Serve it: add  "template_graph": "./templates/backend/langgraph_graph.py:graph"  to langgraph.json, then `langgraph dev`.
Test it in-process: build_graph().invoke({"question": "..."}, config={"configurable": {"thread_id": "t1"}})

Shape used by the real graphs: typed state -> deterministic steps (code computes every number) -> conditional routing ->
a human-approval interrupt before anything is proposed -> resume with the decision.
"""
from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict, total=False):
    question: str
    route: str
    result: dict
    decision: str
    answer: str


def understand(state: State) -> dict:
    # real graphs ask the LLM to extract parameters; the route itself is validated in code
    q = state["question"].lower()
    return {"route": "transfer" if "transfer" in q else "info"}


def calculate(state: State) -> dict:
    # deterministic calculation (real graphs call the SCInsight API: POST /scinsight/api/v1/optimizer/...)
    return {"result": {"calculation_id": "CALC-TEMPLATE-1", "transfer_qty": 120, "from": "A", "to": "B"}}


def approval(state: State) -> dict:
    # pauses the run; LangGraph Server shows it as an interrupt until a human resumes it
    decision = interrupt({"proposal": state["result"], "ask": "approve or reject"})
    return {"decision": decision}


def answer(state: State) -> dict:
    if state.get("route") != "transfer":
        return {"answer": "No action needed."}
    return {"answer": f"Transfer {state['result']['transfer_qty']} units: {state.get('decision', 'pending')}"}


def route_after_understand(state: State) -> Literal["calculate", "answer"]:
    return "calculate" if state["route"] == "transfer" else "answer"


def build_graph(checkpointer=None):
    g = StateGraph(State)
    for name, fn in (("understand", understand), ("calculate", calculate), ("approval", approval), ("answer", answer)):
        g.add_node(name, fn)
    g.add_edge(START, "understand")
    g.add_conditional_edges("understand", route_after_understand)
    g.add_edge("calculate", "approval")
    g.add_edge("approval", "answer")
    g.add_edge("answer", END)
    return g.compile(checkpointer=checkpointer)


graph = build_graph()  # LangGraph Server provides the checkpointer


if __name__ == "__main__":  # quick local run with an in-memory checkpointer
    demo = build_graph(MemorySaver())
    cfg = {"configurable": {"thread_id": "demo"}}
    print(demo.invoke({"question": "Should we transfer stock to B?"}, cfg))       # stops at the approval interrupt
    print(demo.invoke(Command(resume="approved by warehouse manager"), cfg))      # resumes with the decision
