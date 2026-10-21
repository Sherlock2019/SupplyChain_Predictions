from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.scinsight.app import create_app
from backend.scinsight.db import Database
from backend.scinsight.settings import SciSettings


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
