# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/runner.py
# What this module is: how the SPARC gateway executes its LangGraph graphs: on LangGraph Server (RemoteRunner, deployments) or
# in-process with a checkpointer (LocalRunner, tests / single binary). GraphRunner picks one, normalises results (messages, interrupts)
# and records run metrics.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Execute LangGraph graphs either on LangGraph Server (deployments) or in-process (tests / single binary)."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from backend.app.config import Settings
from backend.app.observability import AGENT_LATENCY, AGENT_RUNS, flush, run_config

GRAPH_IDS = ("supply_chain_chat", "supply_chain_agentflow", "supply_chain_business", "supplier_deep_agent")


# ===== FUNCTION: _message_dict() =====
# ID: F0607 · function · used
# ORIGINAL FILE: backend/app/runner.py:15-33
# ROLE: Convert a LangChain message (or a dict from the server) into a plain dict {type, name, content, tool_calls[{name, args}]}.
# INPUTS:
#   message: Any.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0608 normalise() (calls)
# CALLS:
#   (none found)
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
    # Multi-part content -> plain text.
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return {
        "type": data.get("type"),
        "name": data.get("name"),
        "content": content,
        "tool_calls": [{"name": call.get("name"), "args": call.get("args")} for call in (data.get("tool_calls") or [])],
    }


# ===== FUNCTION: normalise() =====
# ID: F0608 · function · used
# ORIGINAL FILE: backend/app/runner.py:36-42
# ROLE: JSON-friendly graph values: messages as dicts, Deep Agent files as {path: content}.
# INPUTS:
#   values: dict.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0613 LocalRunner._result() (calls)
#   <- F0618 RemoteRunner._result() (calls)
# CALLS:
#   -> F0607 _message_dict() (calls)
def normalise(values: dict) -> dict:
    out = dict(values or {})
    if "messages" in out:
        out["messages"] = [_message_dict(message) for message in out["messages"]]
    if "files" in out and isinstance(out["files"], dict):
        out["files"] = {path: (f.get("content") if isinstance(f, dict) else f) for path, f in out["files"].items()}
    return out


# ===== CLASS: LocalRunner =====
# ID: F0609 · class · used
# ORIGINAL FILE: backend/app/runner.py:45-106
# ROLE: In-process runner: compiles each graph once with a checkpointer (PostgreSQL when DATABASE_URL is PostgreSQL, else memory).
# FIELDS:
#   mode = "in-process", settings, _graphs (cache), _lock, checkpointer.
# CALLED BY:
#   <- F0623 GraphRunner.impl() (calls)
#   <- F0821 runner() (calls)
#   <- F0821 runner() (references)
# CALLS:
#   (none found)
class LocalRunner:
    mode = "in-process"

    # ===== FUNCTION: LocalRunner.__init__() =====
    # ID: F0610 · method · used (framework)
    # ORIGINAL FILE: backend/app/runner.py:48-52
    # ROLE: Prepare the graph cache and the checkpointer.
    # INPUTS:
    #   settings: Settings.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0001 Settings (references)
    #   -> F0611 LocalRunner._checkpointer() (calls)
    def __init__(self, settings: Settings):
        self.settings = settings
        self._graphs: dict[str, Any] = {}
        self._lock = threading.Lock()
        self.checkpointer = self._checkpointer()

    # ===== FUNCTION: LocalRunner._checkpointer() =====
    # ID: F0611 · method · used (framework)
    # ORIGINAL FILE: backend/app/runner.py:54-66
    # ROLE: Checkpointer = where paused / multi-turn graph state is saved (needed for interrupt + resume).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   PostgresSaver | InMemorySaver.
    # CALLED BY:
    #   <- F0610 LocalRunner.__init__() (calls)
    # CALLS:
    #   (none found)
    def _checkpointer(self):
        if self.settings.database_url.startswith(("postgresql://", "postgres://")):
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg import Connection
            from psycopg.rows import dict_row

            # prepare_threshold=0 disables server-side prepared statements (safe with connection poolers).
            connection = Connection.connect(self.settings.database_url, autocommit=True, prepare_threshold=0, row_factory=dict_row)
            saver = PostgresSaver(connection)
            saver.setup()
            return saver
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()

    # ===== FUNCTION: LocalRunner.graph() =====
    # ID: F0612 · method · used
    # ORIGINAL FILE: backend/app/runner.py:68-84
    # ROLE: The compiled graph for an id (built on first use, thread-safe).
    # INPUTS:
    #   graph_id: str (one of GRAPH_IDS).
    # OUTPUT:
    #   compiled graph.
    # CALLED BY:
    #   <- F0614 LocalRunner.run() (calls)
    #   <- F0615 LocalRunner.resume() (calls)
    # CALLS:
    #   -> F0572 build_graph() (calls)
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

    # ===== FUNCTION: LocalRunner._result() =====
    # ID: F0613 · method · used
    # ORIGINAL FILE: backend/app/runner.py:86-89
    # ROLE: Current thread state -> {thread_id, values, next, interrupts, runtime}.
    # INPUTS:
    #   graph, config: dict, thread_id: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0614 LocalRunner.run() (calls)
    #   <- F0615 LocalRunner.resume() (calls)
    # CALLS:
    #   -> F0608 normalise() (calls)
    def _result(self, graph, config: dict, thread_id: str) -> dict:
        state = graph.get_state(config)
        interrupts = [item.value for task in state.tasks for item in getattr(task, "interrupts", ())]
        return {"thread_id": thread_id, "values": normalise(state.values), "next": list(state.next), "interrupts": interrupts, "runtime": self.mode}

    # ===== FUNCTION: LocalRunner.run() =====
    # ID: F0614 · method · used
    # ORIGINAL FILE: backend/app/runner.py:91-97
    # ROLE: Run a graph on a (new or existing) thread and return its state.
    # INPUTS:
    #   graph_id: str, payload: dict, thread_id: str | None.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0626 GraphRunner.run() (references)
    # CALLS:
    #   -> F0612 LocalRunner.graph() (calls)
    #   -> F0011 run_config() (calls)
    #   -> F0012 flush() (calls)
    #   -> F0613 LocalRunner._result() (calls)
    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        thread_id = thread_id or str(uuid.uuid4())
        graph = self.graph(graph_id)
        # dict | dict merge adds the recursion limit to the traced run config.
        config = run_config(graph_id, thread_id) | {"recursion_limit": 60}
        graph.invoke(payload, config)
        flush()
        return self._result(graph, config, thread_id)

    # ===== FUNCTION: LocalRunner.resume() =====
    # ID: F0615 · method · used
    # ORIGINAL FILE: backend/app/runner.py:99-106
    # ROLE: Resume a paused thread with a value (Command(resume=...)) and return its state.
    # INPUTS:
    #   graph_id: str, thread_id: str, value: Any.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0627 GraphRunner.resume() (references)
    # CALLS:
    #   -> F0612 LocalRunner.graph() (calls)
    #   -> F0011 run_config() (calls)
    #   -> F0012 flush() (calls)
    #   -> F0613 LocalRunner._result() (calls)
    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        from langgraph.types import Command

        graph = self.graph(graph_id)
        config = run_config(graph_id, thread_id) | {"recursion_limit": 60}
        graph.invoke(Command(resume=value), config)
        flush()
        return self._result(graph, config, thread_id)


# ===== CLASS: RemoteRunner =====
# ID: F0616 · class · used
# ORIGINAL FILE: backend/app/runner.py:109-139
# ROLE: LangGraph Server runner (the server LangSmith Studio connects to), through langgraph_sdk.
# FIELDS:
#   mode = "langgraph-server", url, client.
# CALLED BY:
#   <- F0623 GraphRunner.impl() (calls)
# CALLS:
#   (none found)
class RemoteRunner:
    """LangGraph Server (the same server LangSmith Studio connects to)."""

    mode = "langgraph-server"

    # ===== FUNCTION: RemoteRunner.__init__() =====
    # ID: F0617 · method · used (framework)
    # ORIGINAL FILE: backend/app/runner.py:114-118
    # ROLE: Create the synchronous SDK client.
    # INPUTS:
    #   url: str, timeout: float.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, url: str, timeout: float = 600):
        from langgraph_sdk import get_sync_client

        self.url = url
        self.client = get_sync_client(url=url, timeout=timeout)

    # ===== FUNCTION: RemoteRunner._result() =====
    # ID: F0618 · method · used
    # ORIGINAL FILE: backend/app/runner.py:120-125
    # ROLE: Thread state from the server -> the same result shape as LocalRunner (interrupts read from either location).
    # INPUTS:
    #   thread_id: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0619 RemoteRunner.run() (calls)
    #   <- F0620 RemoteRunner.resume() (calls)
    # CALLS:
    #   -> F0608 normalise() (calls)
    def _result(self, thread_id: str) -> dict:
        state = self.client.threads.get_state(thread_id)
        interrupts = [item.get("value") for item in (state.get("interrupts") or [])]
        if not interrupts:
            interrupts = [item.get("value") for task in state.get("tasks", []) for item in task.get("interrupts", [])]
        return {"thread_id": thread_id, "values": normalise(state.get("values") or {}), "next": state.get("next", []), "interrupts": interrupts, "runtime": self.mode}

    # ===== FUNCTION: RemoteRunner.run() =====
    # ID: F0619 · method · used
    # ORIGINAL FILE: backend/app/runner.py:127-133
    # ROLE: Create the thread if needed, run the graph and wait for completion (or interrupt).
    # INPUTS:
    #   graph_id, payload, thread_id.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0626 GraphRunner.run() (references)
    # CALLS:
    #   -> F0973 Flowise.wait() (calls)
    #   -> F0618 RemoteRunner._result() (calls)
    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        thread_id = thread_id or str(uuid.uuid4())
        self.client.threads.create(thread_id=thread_id, if_exists="do_nothing", metadata={"graph_id": graph_id})
        output = self.client.runs.wait(thread_id, graph_id, input=payload, config={"recursion_limit": 60})
        if isinstance(output, dict) and output.get("__error__"):
            raise RuntimeError(f"LangGraph run failed: {output['__error__']}")
        return self._result(thread_id)

    # ===== FUNCTION: RemoteRunner.resume() =====
    # ID: F0620 · method · used
    # ORIGINAL FILE: backend/app/runner.py:135-139
    # ROLE: Resume a paused run on the server.
    # INPUTS:
    #   graph_id, thread_id, value.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0627 GraphRunner.resume() (references)
    # CALLS:
    #   -> F0973 Flowise.wait() (calls)
    #   -> F0618 RemoteRunner._result() (calls)
    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        output = self.client.runs.wait(thread_id, graph_id, command={"resume": value}, config={"recursion_limit": 60})
        if isinstance(output, dict) and output.get("__error__"):
            raise RuntimeError(f"LangGraph run failed: {output['__error__']}")
        return self._result(thread_id)


# ===== CLASS: GraphRunner =====
# ID: F0621 · class · used
# ORIGINAL FILE: backend/app/runner.py:142-173
# ROLE: Facade used by the gateway: lazily chooses Remote (LANGGRAPH_URL set) or Local runner; times runs and counts outcomes.
# FIELDS:
#   settings, _impl.
# CALLED BY:
#   <- F0017 create_app() (references)
#   <- F0017 create_app() (calls)
# CALLS:
#   (none found)
class GraphRunner:
    # ===== FUNCTION: GraphRunner.__init__() =====
    # ID: F0622 · method · used (framework)
    # ORIGINAL FILE: backend/app/runner.py:143-145
    # ROLE: Keep the settings (the runner is created on first use).
    # INPUTS:
    #   settings: Settings.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0001 Settings (references)
    def __init__(self, settings: Settings):
        self.settings = settings
        self._impl = None

    # ===== FUNCTION: GraphRunner.impl() =====
    # ID: F0623 · method · used
    # ORIGINAL FILE: backend/app/runner.py:147-151
    # ROLE: The underlying runner (created once).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   RemoteRunner | LocalRunner.
    # CALLED BY:
    #   <- F0626 GraphRunner.run() (references)
    #   <- F0627 GraphRunner.resume() (references)
    # CALLS:
    #   -> F0616 RemoteRunner (calls)
    #   -> F0609 LocalRunner (calls)
    @property
    def impl(self):
        if self._impl is None:
            self._impl = RemoteRunner(self.settings.langgraph_url) if self.settings.langgraph_url else LocalRunner(self.settings)
        return self._impl

    # ===== FUNCTION: GraphRunner.mode() =====
    # ID: F0624 · method · used
    # ORIGINAL FILE: backend/app/runner.py:153-155
    # ROLE: "langgraph-server" or "in-process" (shown on /status and /config/public).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   str.
    # CALLED BY:
    #   <- F0028 create_app.public_config() (references)
    #   <- F0031 create_app.status() (references)
    # CALLS:
    #   (none found)
    @property
    def mode(self) -> str:
        return "langgraph-server" if self.settings.langgraph_url else "in-process"

    # ===== FUNCTION: GraphRunner._timed() =====
    # ID: F0625 · method · used
    # ORIGINAL FILE: backend/app/runner.py:157-167
    # ROLE: Run fn, record AGENT_RUNS (completed / interrupted / error) and AGENT_LATENCY, add elapsed_seconds.
    # INPUTS:
    #   graph_id: str, fn: callable, *args.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0626 GraphRunner.run() (calls)
    #   <- F0627 GraphRunner.resume() (calls)
    # CALLS:
    #   (none found)
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

    # ===== FUNCTION: GraphRunner.run() =====
    # ID: F0626 · method · used
    # ORIGINAL FILE: backend/app/runner.py:169-170
    # ROLE: Run a graph (timed).
    # INPUTS:
    #   graph_id, payload, thread_id.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0083 create_app.chat() (references)
    #   <- F0085 create_app.langgraph_agentflow() (references)
    #   <- F0087 create_app.business_start() (references)
    #   <- F0092 create_app.supplier_research() (references)
    #   <- F0823 test_chat_graph_guard_refuses_sap_writes() (calls)
    #   <- F0824 test_chat_graph_deterministic_fallback_keeps_thread_memory() (calls)
    #   <- F0825 test_business_graph_interrupts_then_submits() (calls)
    #   <- F0826 test_business_graph_discard_and_free_text_intake() (calls)
    #   <- F0827 test_business_graph_rejects_invalid_and_completes_no_action() (calls)
    #   <- F0829 test_langgraph_agentflow_routes_interrupts_and_submits() (calls)
    #   <- F0830 test_langgraph_agentflow_boundary_and_discard() (calls)
    # CALLS:
    #   -> F0625 GraphRunner._timed() (calls)
    #   -> F0614 LocalRunner.run() (references)
    #   -> F0619 RemoteRunner.run() (references)
    #   -> F0623 GraphRunner.impl() (references)
    def run(self, graph_id: str, payload: dict, thread_id: str | None = None) -> dict:
        return self._timed(graph_id, self.impl.run, graph_id, payload, thread_id)

    # ===== FUNCTION: GraphRunner.resume() =====
    # ID: F0627 · method · used
    # ORIGINAL FILE: backend/app/runner.py:172-173
    # ROLE: Resume a graph (timed).
    # INPUTS:
    #   graph_id, thread_id, value.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0086 create_app.langgraph_agentflow_resume() (references)
    #   <- F0088 create_app.business_resume() (references)
    #   <- F0825 test_business_graph_interrupts_then_submits() (calls)
    #   <- F0826 test_business_graph_discard_and_free_text_intake() (calls)
    #   <- F0829 test_langgraph_agentflow_routes_interrupts_and_submits() (calls)
    #   <- F0830 test_langgraph_agentflow_boundary_and_discard() (calls)
    # CALLS:
    #   -> F0625 GraphRunner._timed() (calls)
    #   -> F0615 LocalRunner.resume() (references)
    #   -> F0620 RemoteRunner.resume() (references)
    #   -> F0623 GraphRunner.impl() (references)
    def resume(self, graph_id: str, thread_id: str, value: Any) -> dict:
        return self._timed(graph_id, self.impl.resume, graph_id, thread_id, value)
