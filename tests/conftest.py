from __future__ import annotations

import os

# Unit tests are hermetic: no LLM, no gateway, no Postgres, hashed embeddings. Integration tests opt in explicitly.
os.environ.update(
    {
        "APP_ENV": "test",
        "LLM_MODE": "deterministic",
        "RAG_BACKEND": "memory",
        "EMBEDDING_BACKEND": "hash",
        "COPILOT_API_URL": "",
        "LANGGRAPH_URL": "",
        "LANGFUSE_HOST": "",
        "DATABASE_URL": "sqlite:///:memory:",
        "SCINSIGHT_ENABLED": "false",  # gateway tests include a hermetic SCInsight router explicitly where needed
        "ERP_SCHEDULER_ENABLED": "false",
    }
)

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app.config import ROOT, Settings  # noqa: E402
from backend.app.store import Store  # noqa: E402


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        data_file=ROOT / "data" / "sap_mock.json",
        knowledge_dir=ROOT / "data" / "knowledge",
        database_url=f"sqlite:///{tmp_path / 'test.sqlite'}",
        rag_backend="memory",
        embedding_backend="hash",
        llm_mode="deterministic",
        langgraph_url="",
        copilot_api_url="",
        assistant_api_keys="flowise:test-assistant",
        manager_api_keys="manager:test-manager",
    )


@pytest.fixture()
def client(settings: Settings) -> TestClient:
    from backend.app.main import create_app

    return TestClient(create_app(settings, Store.memory()))


@pytest.fixture()
def assistant_headers() -> dict[str, str]:
    return {"X-API-Key": "test-assistant"}


@pytest.fixture()
def manager_headers() -> dict[str, str]:
    return {"X-API-Key": "test-manager"}
