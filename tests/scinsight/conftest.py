from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.scinsight.app import create_router
from backend.scinsight.db import Database
from backend.scinsight.settings import SciSettings


def create_app(settings: SciSettings | None = None, db: Database | None = None) -> FastAPI:
    """Test harness only: the SCInsight router on a bare app (in production it lives in backend/app/main.py at /scinsight)."""
    router = create_router(settings, db)
    app = FastAPI()
    app.include_router(router)
    app.state.db, app.state.kb, app.state.service = router.state.db, router.state.kb, router.state.service
    app.state.security, app.state.ingest_report = router.state.security, router.state.ingest_report
    return app


def settings(**overrides) -> SciSettings:
    base = {"sci_database_url": "sqlite:///:memory:", "sci_embedding_backend": "hash", "sci_business_date": None}
    return SciSettings(_env_file=None, **{**base, **overrides})  # hermetic: never the developer's .env keys


@pytest.fixture()
def app():
    return create_app(settings(), Database("sqlite:///:memory:"))


@pytest.fixture()
def client(app) -> TestClient:
    return TestClient(app)


def key(slot: str) -> dict[str, str]:
    return {"X-API-Key": f"sci-dev-{slot.replace('_', '-')}-key"}
