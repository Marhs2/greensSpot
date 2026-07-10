"""Integration tests for greenspot router endpoints."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """FastAPI TestClient with startup DB init disabled."""
    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c


class TestHealthCheck:
    """GET /api/gs/health endpoint tests."""

    def test_health_kosis_api_key_configured_is_bool(self, client):
        response = client.get("/api/gs/health")

        assert response.status_code == 200
        body = response.json()
        assert "environment" in body
        assert isinstance(body["environment"]["kosisApiKeyConfigured"], bool)

    def test_health_includes_visual_crossing_flag(self, client):
        """health environment 에 Visual Crossing 키 설정 플래그가 있어야 한다."""
        response = client.get("/api/gs/health")

        assert response.status_code == 200
        body = response.json()
        assert "visualCrossingApiKeyConfigured" in body["environment"]
        assert isinstance(body["environment"]["visualCrossingApiKeyConfigured"], bool)


class TestCorsOnHttpException:
    """HTTPException responses must include CORS headers for allowed origins."""

    def test_404_simulate_includes_cors_headers_for_allowed_origin(self, client):
        response = client.post(
            "/api/gs/parcels/NONEXISTENT/simulate",
            json={"scenarioType": "PLANT_TREES", "quantity": 10},
            headers={"Origin": "http://localhost:5173"},
        )

        assert response.status_code == 404
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_404_simulate_omits_allowed_origin_for_disallowed_origin(self, client):
        response = client.post(
            "/api/gs/parcels/NONEXISTENT/simulate",
            json={"scenarioType": "PLANT_TREES", "quantity": 10},
            headers={"Origin": "http://evil.example.com"},
        )

        assert response.status_code == 404
        assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"
