from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_ai_platform.db")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("AI_MOCK_MODE", "true")
os.environ.setdefault("AI_RETRY_DELAYS_SECONDS", "0,0")
os.environ.setdefault("ADMIN_USERNAME", "test-admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_database():
    yield
    path = Path("test_ai_platform.db")
    if path.exists():
        path.unlink()
