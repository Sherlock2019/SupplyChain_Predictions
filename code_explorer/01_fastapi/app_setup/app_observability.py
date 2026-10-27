# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/observability.py
# What this module is: Prometheus metrics of the SPARC gateway (counters / histograms exported on GET /metrics) and the Langfuse
# tracing helpers used by every LangChain / LangGraph run. Tracing failures never break a business call.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Langfuse tracing for LangChain/LangGraph runs and Prometheus metrics shared by all services."""
from __future__ import annotations

import logging
from functools import lru_cache

# Counter: value that only goes up (requests). Histogram: distribution of durations in buckets (latency).
from prometheus_client import Counter, Histogram

from backend.app.config import get_settings

log = logging.getLogger(__name__)

# Metric objects (module-level singletons); labels split one metric into series, e.g. per method/path/status.
REQUESTS = Counter("copilot_http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("copilot_http_request_seconds", "HTTP request latency", ["method", "path"])
ANALYSES = Counter("copilot_analyses_total", "Deterministic analyses", ["kind"])
AGENT_RUNS = Counter("copilot_agent_runs_total", "Agent runs", ["runtime", "outcome"])
AGENT_LATENCY = Histogram("copilot_agent_run_seconds", "Agent run latency", ["runtime"], buckets=(1, 2, 5, 10, 20, 40, 80, 160, 320))
LLM_ERRORS = Counter("copilot_llm_errors_total", "LLM endpoint failures", ["runtime"])
DENIALS = Counter("copilot_auth_denials_total", "Rejected requests", ["reason"])


# ===== FUNCTION: _langfuse_client() =====
# ID: F0009 · function · used
# ORIGINAL FILE: backend/app/observability.py:22-38
# ROLE: The Langfuse client, created once (cached) when Langfuse is configured; None otherwise or on any error.
# INPUTS:
#   none (reads Settings).
# OUTPUT:
#   Langfuse | None.
# CALLED BY:
#   <- F0010 langfuse_callbacks() (calls)
#   <- F0012 flush() (calls)
# CALLS:
#   -> F0008 get_settings() (calls)
@lru_cache
def _langfuse_client():
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None
    try:
        # Optional dependency imported only when tracing is on.
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_host,
            environment=settings.app_env.replace("_", "-")[:40] or "default",
        )
    except Exception as exc:  # noqa: BLE001 - tracing must never break business calls
        log.warning("Langfuse disabled: %s", exc)
        return None


# ===== FUNCTION: langfuse_callbacks() =====
# ID: F0010 · function · used
# ORIGINAL FILE: backend/app/observability.py:41-48
# ROLE: LangChain callback handlers for one run (a Langfuse handler, or an empty list).
# INPUTS:
#   none.
# OUTPUT:
#   list.
# CALLED BY:
#   <- F0572 build_graph() (calls)
#   <- F0585 traced() (calls)
#   <- F0011 run_config() (calls)
# CALLS:
#   -> F0009 _langfuse_client() (calls)
#   -> F0008 get_settings() (calls)
def langfuse_callbacks() -> list:
    """LangChain callback handlers for one run; empty when Langfuse is not configured."""
    client = _langfuse_client()
    if client is None:
        return []
    from langfuse.langchain import CallbackHandler

    return [CallbackHandler(public_key=get_settings().langfuse_public_key)]


# ===== FUNCTION: run_config() =====
# ID: F0011 · function · used
# ORIGINAL FILE: backend/app/observability.py:51-56
# ROLE: Standard LangGraph run config: callbacks, metadata (runtime + extras), run name, and thread id / Langfuse session id.
# INPUTS:
#   runtime: str, thread_id: str | None, **metadata.
# OUTPUT:
#   dict -> config passed to graph.invoke(..., config).
# CALLED BY:
#   <- F0614 LocalRunner.run() (calls)
#   <- F0615 LocalRunner.resume() (calls)
# CALLS:
#   -> F0010 langfuse_callbacks() (calls)
def run_config(runtime: str, thread_id: str | None = None, **metadata) -> dict:
    config: dict = {"callbacks": langfuse_callbacks(), "metadata": {"runtime": runtime, **metadata}, "run_name": runtime}
    if thread_id:
        # thread_id selects the checkpoint (conversation memory / interrupt resume).
        config["configurable"] = {"thread_id": thread_id}
        config["metadata"]["langfuse_session_id"] = thread_id
    return config


# ===== FUNCTION: flush() =====
# ID: F0012 · function · used
# ORIGINAL FILE: backend/app/observability.py:59-65
# ROLE: Send buffered Langfuse events now (end of a run); errors are only logged.
# INPUTS:
#   none.
# OUTPUT:
#   None.
# CALLED BY:
#   <- F0614 LocalRunner.run() (calls)
#   <- F0615 LocalRunner.resume() (calls)
# CALLS:
#   -> F0009 _langfuse_client() (calls)
def flush() -> None:
    client = _langfuse_client()
    if client is not None:
        try:
            client.flush()
        except Exception as exc:  # noqa: BLE001
            log.warning("Langfuse flush failed: %s", exc)
