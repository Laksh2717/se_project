"""Every test gets its own fresh temporary SQLite database (never the shared .db file)."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(f"sqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def client(app):
    return TestClient(app)
