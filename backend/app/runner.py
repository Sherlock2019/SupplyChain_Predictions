"""Execute LangGraph graphs either on LangGraph Server (deployments) or in-process (tests / single binary)."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from backend.app.config import Settings
from backend.app.observability import AGENT_LATENCY, AGENT_RUNS, flush, run_config

GRAPH_IDS = ("supply_chain_chat", "supply_chain_agentflow", "supply_chain_business", "supplier_deep_agent")


def _message_dict(message: Any) -> dict:
    if isinstance(message, dict):
        data = message
    else:
        data = {
            "type": getattr(message, "type", "unknown"),
            "content": getattr(message, "content", ""),
            "name": getattr(message, "name", None),
            "tool_calls": getattr(message, "tool_calls", None) or [],
        }
    content = data.get("content", "")
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return {
        "type": data.get("type"),
        "name": data.get("name"),
        "content": content,
        "tool_calls": [{"name": call.get("name"), "args": call.get("args")} for call in (data.get("tool_calls") or [])],
    }


def normalise(values: dict) -> dict:
    out = dict(values or {})
    if "messages" in out:
        out["messages"] = [_message_dict(message) for message in out["messages"]]
    if "files" in out and isinstance(out["files"], dict):
        out["files"] = {path: (f.get("content") if isinstance(f, dict) else f) for path, f in out["files"].items()}
    return out


class LocalRunner:
    mode = "in-process"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._graphs: dict[str, Any] = {}
        self._lock = threading.Lock()
        self.checkpointer = self._checkpointer()

    def _checkpointer(self):
        if self.settings.database_url.startswith(("postgresql://", "postgres://")):
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg import Connection
            from psycopg.rows import dict_row

            connection = Connection.connect(self.settings.database_url, autocommit=True, prepare_threshold=0, row_factory=dict_row)
            saver = PostgresSaver(connection)
            saver.setup()
            return saver
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()

    def graph(self, graph_id: str):
        with self._lock:
            if graph_id not in self._graphs:
                if graph_id == "supplier_deep_agent":
                    from backend.app.deep_agent import build_graph

                    self._graphs[graph_id] = build_graph(self.checkpointer)
                elif graph_id == "supply_chain_agentflow":
                    from backend.app.agentflow import builder

                    self._graphs[graph_id] = builder.compile(checkpointer=self.checkpointer, name=graph_id)
                else:
                    from backend.app import graphs

                    builder = graphs.chat_builder if graph_id == "supply_chain_chat" else graphs.business_builder
                    self._graphs[graph_id] = builder.compile(checkpointer=self.checkpointer, name=graph_id)
            return self._graphs[graph_id]

    def _result(self, graph, config: dict, thread_id: str) -> dict:
        state = graph.get_state(config)
        interrupts = [item.value for task in state.tasks for item in getattr(task, "interrupts", ())]
        return {"thread_id": thread_id, "values": normalise(state.values), "next": list(state.next), "interrupts": interrupts, "runtime": self.mode}

    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        thread_id = thread_id or str(uuid.uuid4())
        graph = self.graph(graph_id)
        config = run_config(graph_id, thread_id) | {"recursion_limit": 60}
        graph.invoke(payload, config)
        flush()
        return self._result(graph, config, thread_id)

    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        from langgraph.types import Command

        graph = self.graph(graph_id)
        config = run_config(graph_id, thread_id) | {"recursion_limit": 60}
        graph.invoke(Command(resume=value), config)
        flush()
        return self._result(graph, config, thread_id)


class RemoteRunner:
    """LangGraph Server (the same server LangSmith Studio connects to)."""

    mode = "langgraph-server"

    def __init__(self, url: str, timeout: float = 600):
        from langgraph_sdk import get_sync_client

        self.url = url
        self.client = get_sync_client(url=url, timeout=timeout)

    def _result(self, thread_id: str) -> dict:
        state = self.client.threads.get_state(thread_id)
        interrupts = [item.get("value") for item in (state.get("interrupts") or [])]
        if not interrupts:
            interrupts = [item.get("value") for task in state.get("tasks", []) for item in task.get("interrupts", [])]
        return {"thread_id": thread_id, "values": normalise(state.get("values") or {}), "next": state.get("next", []), "interrupts": interrupts, "runtime": self.mode}

    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        thread_id = thread_id or str(uuid.uuid4())
        self.client.threads.create(thread_id=thread_id, if_exists="do_nothing", metadata={"graph_id": graph_id})
        output = self.client.runs.wait(thread_id, graph_id, input=payload, config={"recursion_limit": 60})
        if isinstance(output, dict) and output.get("__error__"):
            raise RuntimeError(f"LangGraph run failed: {output['__error__']}")
        return self._result(thread_id)

    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        output = self.client.runs.wait(thread_id, graph_id, command={"resume": value}, config={"recursion_limit": 60})
        if isinstance(output, dict) and output.get("__error__"):
            raise RuntimeError(f"LangGraph run failed: {output['__error__']}")
        return self._result(thread_id)


class GraphRunner:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._impl = None

    @property
    def impl(self):
        if self._impl is None:
            self._impl = RemoteRunner(self.settings.langgraph_url) if self.settings.langgraph_url else LocalRunner(self.settings)
        return self._impl

    @property
    def mode(self) -> str:
        return "langgraph-server" if self.settings.langgraph_url else "in-process"

    def _timed(self, graph_id: str, fn, *args) -> dict:
        started = time.perf_counter()
        try:
            result = fn(*args)
        except Exception:
            AGENT_RUNS.labels(graph_id, "error").inc()
            raise
        AGENT_RUNS.labels(graph_id, "interrupted" if result["interrupts"] else "completed").inc()
        AGENT_LATENCY.labels(graph_id).observe(time.perf_counter() - started)
        result["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        return result

    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        return self._timed(graph_id, self.impl.run, graph_id, payload, thread_id)

    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        return self._timed(graph_id, self.impl.resume, graph_id, thread_id, value)
