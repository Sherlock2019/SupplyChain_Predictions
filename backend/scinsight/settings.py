"""Runtime settings for the SupplyChain Insight AI service (environment variables; see .env.example)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class SciSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

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

    SLOTS: ClassVar[tuple[str, ...]] = ("agent", "planner", "procurement", "warehouse", "logistics", "quality", "director", "sap_executor", "mlops", "other_tenant")

    def user_keys(self) -> dict[str, str]:
        return {slot: getattr(self, f"sci_{slot}_key") for slot in self.SLOTS if getattr(self, f"sci_{slot}_key")}

    def missing_keys(self) -> list[str]:
        return [f"SCI_{slot.upper()}_KEY" for slot in self.SLOTS if not getattr(self, f"sci_{slot}_key")]
