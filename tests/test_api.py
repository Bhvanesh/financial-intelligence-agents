import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock, patch
from database import Base
from main import app, get_db, get_api_key
from models import APIKey

# ─── Test database setup ──────────────────────────────────────
engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_api_key():
    """Returns a fake active API key — skips auth for tests."""
    mock_key = MagicMock()
    mock_key.owner_name = "TestUser"
    mock_key.key = "sk-testkey123"
    mock_key.is_active = True
    return mock_key


app.dependency_overrides[get_db]      = override_get_db
app.dependency_overrides[get_api_key] = override_get_api_key

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ─── Tests ────────────────────────────────────────────────────

def test_register_success():
    response = client.post("/register", json={"owner_name": "Surya"})
    assert response.status_code == 200
    data = response.json()
    assert data["owner_name"] == "Surya"
    assert data["key"].startswith("sk-")
    assert data["is_active"] == True
    assert "message" in data


def test_register_missing_owner_name():
    response = client.post("/register", json={})
    assert response.status_code == 422


def test_register_owner_name_too_short():
    response = client.post("/register", json={"owner_name": "A"})
    assert response.status_code == 422


def test_list_analyses_empty():
    response = client.get("/all_analyses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_analysis_not_found():
    response = client.get("/analysis/999")
    assert response.status_code == 404


def test_analyze_no_file():
    response = client.post(
        "/analyze",
        data={"user_prompt": "analyze the risks"}
    )
    assert response.status_code == 422


def test_analyze_wrong_file_type():
    response = client.post(
        "/analyze",
        files={"file": ("test.txt", b"some text content", "text/plain")},
        data={"user_prompt": "analyze the risks"}
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_analyze_empty_prompt():
    response = client.post(
        "/analyze",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
        data={"user_prompt": "   "}
    )
    assert response.status_code == 400


def test_analyze_prompt_too_long():
    long_prompt = "a" * 501
    response = client.post(
        "/analyze",
        files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
        data={"user_prompt": long_prompt}
    )
    assert response.status_code == 400