"""Langfuse tracing for LangChain/LangGraph runs and Prometheus metrics shared by all services."""
from __future__ import annotations

import logging
from functools import lru_cache

from prometheus_client import Counter, Histogram

from backend.app.config import get_settings

log = logging.getLogger(__name__)

REQUESTS = Counter("copilot_http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("copilot_http_request_seconds", "HTTP request latency", ["method", "path"])
ANALYSES = Counter("copilot_analyses_total", "Deterministic analyses", ["kind"])
AGENT_RUNS = Counter("copilot_agent_runs_total", "Agent runs", ["runtime", "outcome"])
AGENT_LATENCY = Histogram("copilot_agent_run_seconds", "Agent run latency", ["runtime"], buckets=(1, 2, 5, 10, 20, 40, 80, 160, 320))
LLM_ERRORS = Counter("copilot_llm_errors_total", "LLM endpoint failures", ["runtime"])
DENIALS = Counter("copilot_auth_denials_total", "Rejected requests", ["reason"])


@lru_cache
def _langfuse_client():
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None
    try:
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


def langfuse_callbacks() -> list:
    """LangChain callback handlers for one run; empty when Langfuse is not configured."""
    client = _langfuse_client()
    if client is None:
        return []
    from langfuse.langchain import CallbackHandler

    return [CallbackHandler(public_key=get_settings().langfuse_public_key)]


def run_config(runtime: str, thread_id: str | None = None, **metadata) -> dict:
    config: dict = {"callbacks": langfuse_callbacks(), "metadata": {"runtime": runtime, **metadata}, "run_name": runtime}
    if thread_id:
        config["configurable"] = {"thread_id": thread_id}
        config["metadata"]["langfuse_session_id"] = thread_id
    return config


def flush() -> None:
    client = _langfuse_client()
    if client is not None:
        try:
            client.flush()
        except Exception as exc:  # noqa: BLE001
            log.warning("Langfuse flush failed: %s", exc)
