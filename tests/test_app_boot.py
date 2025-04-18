"""Smoke test for the FastAPI application."""

from fastapi.testclient import TestClient
from app.api.main import app

def test_root():
    """Test that the root endpoint returns a 200 status code."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "docs" in response.json()

def test_languages_endpoint():
    """Test that the languages endpoint returns a 200 status code."""
    client = TestClient(app)
    response = client.get("/languages")
    assert response.status_code == 200
    assert "1" in response.json()  # At least Japanese should be present
    assert response.json()["1"] == "Japanese"

def test_sections_endpoint():
    """Test that the sections endpoint returns a 200 status code."""
    client = TestClient(app)
    response = client.get("/sections")
    assert response.status_code == 200
    assert "1" in response.json()  # At least one section should be present 