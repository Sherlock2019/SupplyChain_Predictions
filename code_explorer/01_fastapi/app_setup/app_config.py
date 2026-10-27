# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/config.py
# What this module is: configuration of the SPARC / Aurelia gateway (backend/app), read from environment variables / .env.
# The default key strings below are public development defaults; real deployments generate their own (scripts/gen-env.py).
# Only comment lines were added (AST-verified).
# ======================================================================================================
from __future__ import annotations

# lru_cache: get_settings() builds the Settings object once and reuses it.
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root (backend/app/config.py -> parents[2]).
ROOT = Path(__file__).resolve().parents[2]


# ===== CLASS: Settings =====
# ID: F0001 · pydantic_model · used
# ORIGINAL FILE: backend/app/config.py:11-119
# ROLE: All gateway settings: environment, API keys per role, tenant scopes, databases / RAG, Qwen, service URLs, SAP execution mode.
# FIELDS:
#   (see the attributes below; each maps to an UPPERCASE environment variable).
# CALLED BY:
#   <- F0769 ApiKeyAuth.__init__() (references)
#   <- F0008 get_settings() (calls)
#   <- F0008 get_settings() (references)
#   <- F0483 build_backend() (references)
#   <- F0728 chat_model() (references)
#   <- F0729 llm_health() (references)
#   <- F0017 create_app() (references)
#   <- F0610 LocalRunner.__init__() (references)
#   <- F0622 GraphRunner.__init__() (references)
#   <- F0904 settings() (calls)
#   <- F0904 settings() (references)
#   <- F0905 client() (references)
# CALLS:
#   (none found)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: str = "development"
    cloud_provider: str = "local"
    public_base_url: str = "http://localhost:8000"
    # "identity:key,identity:key" lists, parsed by parse_keys() (development defaults).
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

    # ERP / SAP Setup page. Hosts a connection may call (comma-separated; required for production connections, optional otherwise).
    erp_allowed_hosts: str = ""
    # Password of the development-only SAP OData emulator (/erp-emulator, user SPARC_COMM); never mounted outside development/test.
    erp_emulator_password: str = "dev-erp-emulator"
    # Runs scheduled ERP syncs (staging only: a sync never activates a snapshot).
    erp_scheduler_enabled: bool = True

    # LOCAL DEMO ONLY: the dashboard signs in automatically (GET /api/v1/demo/session hands out the demo keys).
    demo_auto_login: bool = False

    # Backend code section of the UI: everyone with a key can read the code; saving a function also needs a manager key,
    # CODE_EDITOR_ENABLED=true and APP_ENV=development|test (never enable it on a shared or cloud deployment).
    # Off by default, so the deployed app is read-only.
    code_editor_enabled: bool = False
    # "Open in VS Code" links of the Backend code page: vscode:// prefix of the repository on the developer's machine,
    # e.g. vscode://vscode-remote/wsl+UbuntuD/home/me/Supplychain-AI-optimizer (empty = links hidden)
    code_vscode_base: str = ""

    # RAG Tuning page: the gateway forwards calls to the SCInsight API with a server-side key (the browser never sees it; the
    # SCInsight API derives tenant and roles from it). Managers: director key (may publish / roll back). Other roles: MLOps key
    # (inspect, preview, build candidates, benchmark; never publish).
    sci_api_url: str = ""          # only when SCInsight is NOT mounted in this app (scinsight_enabled=false)
    # The SCInsight API is mounted in this app at /scinsight (one FastAPI app, one port). It reads its own SCI_* settings.
    scinsight_enabled: bool = True
    sci_tuning_key: str = ""
    sci_tuning_reader_key: str = ""

    log_level: str = "INFO"
    # The SAP mock snapshot and the governed knowledge documents.
    data_file: Path = ROOT / "data" / "sap_mock.json"
    knowledge_dir: Path = ROOT / "data" / "knowledge"

    # ===== FUNCTION: Settings.parse_keys() =====
    # ID: F0002 · method · used (framework)
    # ORIGINAL FILE: backend/app/config.py:87-94
    # ROLE: Parse "identity:key,identity:key" into {key: identity} (lookup by presented key).
    # INPUTS:
    #   raw: str.
    # OUTPUT:
    #   dict[str, str].
    # CALLED BY:
    #   <- F0003 Settings.assistants() (calls)
    #   <- F0004 Settings.managers() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def parse_keys(raw: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for pair in raw.split(","):
            # partition(":") -> (identity, ":", key); `separator` is "" when there is no colon (malformed pair skipped).
            identity, separator, key = pair.strip().partition(":")
            if separator and identity and key:
                result[key] = identity
        return result

    # ===== FUNCTION: Settings.assistants() =====
    # ID: F0003 · method · used (framework)
    # ORIGINAL FILE: backend/app/config.py:96-98
    # ROLE: Assistant keys as {key: identity}.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict[str, str].
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0002 Settings.parse_keys() (calls)
    @property
    def assistants(self) -> dict[str, str]:
        return self.parse_keys(self.assistant_api_keys)

    # ===== FUNCTION: Settings.managers() =====
    # ID: F0004 · method · used (framework)
    # ORIGINAL FILE: backend/app/config.py:100-102
    # ROLE: Manager keys as {key: identity}.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict[str, str].
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0002 Settings.parse_keys() (calls)
    @property
    def managers(self) -> dict[str, str]:
        return self.parse_keys(self.manager_api_keys)

    # ===== FUNCTION: Settings.tenants_for() =====
    # ID: F0005 · method · used
    # ORIGINAL FILE: backend/app/config.py:104-111
    # ROLE: Tenants an identity may use, from TENANT_SCOPES ("identity=t1|t2;other=*"); None = unrestricted.
    # INPUTS:
    #   identity: str.
    # OUTPUT:
    #   set[str] | None.
    # CALLED BY:
    #   <- F0019 create_app.principal() (calls)
    # CALLS:
    #   (none found)
    def tenants_for(self, identity: str) -> set[str] | None:
        """Tenants an identity may use; None = unrestricted."""
        for rule in filter(None, (r.strip() for r in self.tenant_scopes.split(";"))):
            who, _, tenants = rule.partition("=")
            if who.strip() == identity:
                allowed = {t.strip() for t in tenants.split("|") if t.strip()}
                return None if "*" in allowed else allowed
        return None

    # ===== FUNCTION: Settings.llm_enabled() =====
    # ID: F0006 · method · used (framework)
    # ORIGINAL FILE: backend/app/config.py:113-115
    # ROLE: True when the LLM is enabled (llm_mode == "qwen"); "deterministic" disables model calls.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   bool.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @property
    def llm_enabled(self) -> bool:
        return self.llm_mode == "qwen"

    # ===== FUNCTION: Settings.langfuse_enabled() =====
    # ID: F0007 · method · used (framework)
    # ORIGINAL FILE: backend/app/config.py:117-119
    # ROLE: True when all three Langfuse settings are present.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   bool.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_host and self.langfuse_public_key and self.langfuse_secret_key)


# ===== FUNCTION: get_settings() =====
# ID: F0008 · function · used
# ORIGINAL FILE: backend/app/config.py:122-124
# ROLE: Process-wide Settings singleton (cached), used by create_app() and the observability helpers.
# INPUTS:
#   none.
# OUTPUT:
#   Settings.
# CALLED BY:
#   <- F0544 supervisor() (calls)
#   <- F0551 _specialist.node() (calls)
#   <- F0484 get_backend() (calls)
#   <- F0565 build_deep_agent() (calls)
#   <- F0575 route_after_guard() (calls)
#   <- F0580 agent() (calls)
#   <- F0589 intake() (calls)
#   <- F0599 explain() (calls)
#   <- F0017 create_app() (calls)
#   <- F0009 _langfuse_client() (calls)
#   <- F0010 langfuse_callbacks() (calls)
# CALLS:
#   -> F0001 Settings (calls)
#   -> F0001 Settings (references)
@lru_cache
def get_settings() -> Settings:
    return Settings()
