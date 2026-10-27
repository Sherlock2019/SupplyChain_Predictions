# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/settings.py
# What this module is: the configuration of the SCInsight API, read from environment variables / .env
# (pydantic-settings). Each attribute maps to an UPPERCASE variable, e.g. sci_database_url <- SCI_DATABASE_URL.
# Secret values (API keys) are never printed by this documentation; only the variable names appear here.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Runtime settings for the SupplyChain Insight AI service (environment variables; see .env.example)."""
from __future__ import annotations

from datetime import date
# Path: filesystem paths that work on any OS.
from pathlib import Path
# ClassVar marks a class constant that pydantic must NOT treat as a setting.
from typing import ClassVar

# BaseSettings = a Pydantic model whose fields are filled from the environment. SettingsConfigDict configures that loading.
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root: this file is backend/scinsight/settings.py, so parents[2] is the folder that contains "backend".
ROOT = Path(__file__).resolve().parents[2]


# ===== CLASS: SciSettings =====
# ID: F0013 · pydantic_model · used
# ORIGINAL FILE: backend/scinsight/settings.py:13-56
# ROLE: All runtime switches of the SCInsight API (database, SAP mode, safety flags, RAG, synthetic user keys).
# FIELDS:
#   sci_database_url        -> sqlite:///... (tests / local) or postgresql://... (deployments).
#   sap_mode / sap_base_url -> "synthetic" in Phase 1 (live SAP is not implemented).
#   sap_write_enabled       -> must stay False: create_app refuses to start otherwise.
#   human_approval_required -> reported by /health (approvals always need a human).
#   rag_enabled, sci_embedding_backend, sci_knowledge_dir -> RAG switch, embedding model, document folder.
#   sci_load_fixtures       -> load the synthetic SAP data at start-up.
#   sci_business_date, sci_snapshot_max_age_days -> freshness rule for the SAP snapshot.
#   sci_*_key               -> API keys of the 10 synthetic users (stored hashed in the DB, never sent to the LLM).
# CALLED BY:
#   <- F0112 create_app() (references)
#   <- F0112 create_app() (calls)
#   <- F0312 Service.__init__() (references)
#   <- F0908 settings() (calls)
#   <- F0908 settings() (references)
# CALLS:
#   (none found)
class SciSettings(BaseSettings):
    # env_file=".env": also read a local .env file; extra="ignore": other variables in .env are fine; case_sensitive=False.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Default database: a SQLite file under backend/.data (the f-string builds the absolute path).
    sci_database_url: str = f"sqlite:///{ROOT / 'backend' / '.data' / 'scinsight.sqlite'}"
    sap_mode: str = "synthetic"            # synthetic | live (live requires an authorised SAP adapter; not implemented in Phase 1)
    sap_base_url: str = ""
    sap_write_enabled: bool = False        # Phase 1: must stay false — the service refuses to start otherwise
    human_approval_required: bool = True
    industry_sharing_enabled: bool = False
    rag_enabled: bool = True
    sci_embedding_backend: str = "fastembed"  # fastembed (BAAI/bge-small-en-v1.5) | hash (offline tests)
    sci_knowledge_dir: Path = ROOT / "data" / "scinsight" / "knowledge"
    sci_load_fixtures: bool = True
    sci_business_date: date | None = None     # defaults to the SAP snapshot date (synthetic data is frozen in time)
    sci_snapshot_max_age_days: int = 2
    # RAG tuning: the Flowise chatflow whose RAG DB follows the published configuration (server-side only, never sent to a browser)
    sci_flowise_url: str = ""
    sci_flowise_api_key: str = ""
    sci_flowise_chatflow_id: str = ""
    sci_flowise_chatflow_name: str = "SCInsight-Cosmetics-Chatflow-v1"
    sci_jobs_inline: bool = False             # tests: run index builds / benchmarks synchronously
    # optional answer evaluation in the RAG benchmark (same OpenAI-compatible Qwen endpoint as the agents)
    qwen_base_url: str = ""
    qwen_model: str = "qwen2.5-7b-scm"
    qwen_api_key: str = ""
    # API keys of the synthetic users (hashed in the database; never sent to the LLM)
    sci_agent_key: str = ""
    sci_planner_key: str = ""
    sci_procurement_key: str = ""
    sci_warehouse_key: str = ""
    sci_logistics_key: str = ""
    sci_quality_key: str = ""
    sci_director_key: str = ""
    sci_sap_executor_key: str = ""
    sci_mlops_key: str = ""
    sci_other_tenant_key: str = ""

    # The 10 key "slots"; ClassVar keeps this tuple out of the environment loading.
    SLOTS: ClassVar[tuple[str, ...]] = ("agent", "planner", "procurement", "warehouse", "logistics", "quality", "director", "sap_executor", "mlops", "other_tenant")

    # ===== FUNCTION: SciSettings.user_keys() =====
    # ID: F0014 · method · used
    # ORIGINAL FILE: backend/scinsight/settings.py:52-53
    # ROLE: The configured (non-empty) user keys by slot, handed to fixtures.load() which stores their SHA-256 hashes.
    # INPUTS:
    #   self -> the settings.
    # OUTPUT:
    #   dict[str, str] -> {"agent": "<key>", "planner": "<key>", ...} only for slots that have a value.
    # CALLED BY:
    #   <- F0112 create_app() (calls)
    # CALLS:
    #   (none found)
    def user_keys(self) -> dict[str, str]:
        # Dict comprehension; getattr(self, "sci_agent_key") reads the attribute whose name is built at run time.
        return {slot: getattr(self, f"sci_{slot}_key") for slot in self.SLOTS if getattr(self, f"sci_{slot}_key")}

    # ===== FUNCTION: SciSettings.missing_keys() =====
    # ID: F0015 · method · used
    # ORIGINAL FILE: backend/scinsight/settings.py:55-56
    # ROLE: Names of the environment variables that are still empty (deployments must set all of them).
    # INPUTS:
    #   self -> the settings.
    # OUTPUT:
    #   list[str] -> e.g. ["SCI_QUALITY_KEY"]; empty list when everything is configured.
    # CALLED BY:
    #   <- F0112 create_app() (calls)
    # CALLS:
    #   (none found)
    def missing_keys(self) -> list[str]:
        return [f"SCI_{slot.upper()}_KEY" for slot in self.SLOTS if not getattr(self, f"sci_{slot}_key")]
