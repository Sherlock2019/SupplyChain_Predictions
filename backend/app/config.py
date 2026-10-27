from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    cloud_provider: str = "local"
    public_base_url: str = "http://localhost:8000"
    assistant_api_keys: str = "flowise:dev-assistant-key,langgraph:dev-langgraph-key,mcp:dev-mcp-key"
    manager_api_keys: str = "manager:dev-manager-key"
    # Tenant-scoped authorization: "identity=tenant|tenant;identity=*". Identities not listed may use every tenant (demo default).
    tenant_scopes: str = ""

    # Governance ledger (analyses, recommendations, audit). sqlite:///path or postgresql://...
    database_url: str = f"sqlite:///{ROOT / 'backend' / '.data' / 'copilot.sqlite'}"
    # RAG vector store and LangGraph checkpoints.
    postgres_url: str = "postgresql://supplychain:supplychain@localhost:5432/supplychain"
    rag_backend: str = "memory"  # memory | pgvector
    embedding_backend: str = "fastembed"  # fastembed | hash
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Qwen through any OpenAI-compatible server: vLLM in the cloud, Ollama on a local workstation.
    qwen_base_url: str = "http://localhost:11434/v1"
    qwen_model: str = "qwen2.5:7b"
    qwen_api_key: str = "local-qwen"
    llm_mode: str = "qwen"  # qwen | deterministic
    llm_timeout_seconds: float = 180

    # When set, LangGraph/Deep Agent/MCP tools call the governed FastAPI gateway instead of the in-process engine.
    copilot_api_url: str = ""
    copilot_api_key: str = ""

    # Optional service endpoints used by the status page, chat proxies and smoke tests.
    langgraph_url: str = ""
    flowise_url: str = ""
    flowise_api_key: str = ""
    flowise_chatflow_id: str = ""
    flowise_agentflow_id: str = ""
    mcp_url: str = ""
    langfuse_host: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    grafana_url: str = ""

    # 1-click execution of ACCEPTED recommendations: "sandbox" writes documents to the SAP mock's sandbox outbox
    # (never a production SAP system); "disabled" keeps execution manual. Agents can never execute either way.
    sap_execution_mode: str = "sandbox"

    # LOCAL DEMO ONLY: the dashboard signs in automatically (GET /api/v1/demo/session hands out the demo keys).
    demo_auto_login: bool = False

    # Backend code section of the UI: everyone with a key can read the code; saving a function also needs a manager key,
    # CODE_EDITOR_ENABLED=true and APP_ENV=development|test (never enable it on a shared or cloud deployment).
    code_editor_enabled: bool = False

    log_level: str = "INFO"
    data_file: Path = ROOT / "data" / "sap_mock.json"
    knowledge_dir: Path = ROOT / "data" / "knowledge"

    @staticmethod
    def parse_keys(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for pair in raw.split(","):
            identity, separator, key = pair.strip().partition(":")
            if separator and identity and key:
                result[key] = identity
        return result

    @property
    def assistants(self) -> dict[str, str]:
        return self.parse_keys(self.assistant_api_keys)

    @property
    def managers(self) -> dict[str, str]:
        return self.parse_keys(self.manager_api_keys)

    def tenants_for(self, identity: str) -> set[str] | None:
        """Tenants an identity may use; None = unrestricted."""
        for rule in filter(None, (r.strip() for r in self.tenant_scopes.split(";"))):
            who, _, tenants = rule.partition("=")
            if who.strip() == identity:
                allowed = {t.strip() for t in tenants.split("|") if t.strip()}
                return None if "*" in allowed else allowed
        return None

    @property
    def llm_enabled(self) -> bool:
        return self.llm_mode == "qwen"

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_host and self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
