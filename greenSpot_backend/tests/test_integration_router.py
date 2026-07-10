"""Integration tests for external-data router endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """FastAPI TestClient with startup DB init disabled."""
    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c


class TestKosisPopulation:
    """F-25 KOSIS 공개 API 제거 확인."""

    def test_population_endpoint_removed(self, client):
        response = client.get("/api/v1/gs/kosis/population?district=강남구&year=2023")
        assert response.status_code == 404

    def test_households_endpoint_removed(self, client):
        response = client.get("/api/v1/gs/kosis/households?district=강남구")
        assert response.status_code == 404


class TestVisualCrossingClimate:
    """GET /api/v1/gs/visualcrossing/climate endpoint integration tests."""

    def test_climate_returns_200(self, client):
        mock_client = AsyncMock()
        mock_client.get_climate_for_district.return_value = {
            "source": "visualcrossing",
            "district": None,
            "location": "37.5145,127.0533",
            "start": "2025-06-01",
            "end": "2025-07-01",
            "solarIrradiance": 4.2,
            "sunlightHours": 6.1,
            "avgTemperature": 24.5,
            "dataAvailable": True,
        }
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_client,
        ):
            response = client.get(
                "/api/v1/gs/visualcrossing/climate?lat=37.5145&lng=127.0533&days=30"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "visualcrossing"
        assert body["location"] == "37.5145,127.0533"
        assert body["solarIrradiance"] == 4.2
        assert body["dataAvailable"] is True
        mock_client.get_climate_for_district.assert_awaited_once()
        assert (
            mock_client.get_climate_for_district.await_args.kwargs["location"]
            == "37.5145,127.0533"
        )

    def test_climate_invalid_coordinates_returns_400(self, client):
        response = client.get("/api/v1/gs/visualcrossing/climate?lat=120&lng=0")
        assert response.status_code == 400

    def test_climate_unconfigured_returns_400(self, client):
        from app.services.visual_crossing_service import VisualCrossingNotConfigured

        mock_client = AsyncMock()
        mock_client.get_climate_for_district.side_effect = VisualCrossingNotConfigured(
            "VISUAL_CROSSING_API_KEY unset"
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_client,
        ):
            response = client.get("/api/v1/gs/visualcrossing/climate?lat=37.5&lng=127.0")
        assert response.status_code == 400
        assert "VISUAL_CROSSING" in response.json()["detail"]


class TestVisualCrossingHeat:
    """GET /api/v1/gs/visualcrossing/heat endpoint integration tests."""

    def test_heat_returns_200(self, client):
        mock_client = AsyncMock()
        mock_client.get_heat_estimates.return_value = {
            "source": "visualcrossing",
            "district": None,
            "location": "37.5145,127.0533",
            "period": {"start": "2025-06-01", "end": "2025-08-31"},
            "heatIsland": 2.3,
            "surfaceTempSummer": 32.4,
            "avgTemperature": 27.4,
            "maxTemperature": 33.1,
            "dataAvailable": True,
        }
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_client,
        ):
            response = client.get(
                "/api/v1/gs/visualcrossing/heat?lat=37.5145&lng=127.0533&days=30"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["heatIsland"] == 2.3
        assert body["surfaceTempSummer"] == 32.4
        assert body["dataAvailable"] is True
        mock_client.get_heat_estimates.assert_awaited_once()
        assert (
            mock_client.get_heat_estimates.await_args.kwargs["location"]
            == "37.5145,127.0533"
        )


class TestVisualCrossingTimeline:
    """GET /api/v1/gs/visualcrossing/timeline endpoint integration tests."""

    def test_timeline_returns_200(self, client):
        mock_client = AsyncMock()
        mock_client.get_timeline.return_value = [
            {"datetime": "2025-07-01", "temp": 27.0, "solarenergy": 18.0},
            {"datetime": "2025-07-02", "temp": 28.5, "solarenergy": 19.2},
        ]
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_client,
        ):
            response = client.get(
                "/api/v1/gs/visualcrossing/timeline?location=Seoul,South Korea"
                "&start=2025-07-01&end=2025-07-02"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 2
        assert body["location"] == "Seoul,South Korea"
        assert body["start"] == "2025-07-01"
        assert body["end"] == "2025-07-02"
        assert body["dataAvailable"] is True
        mock_client.get_timeline.assert_awaited_once_with(
            "Seoul,South Korea", start="2025-07-01", end="2025-07-02",
        )

    def test_timeline_unconfigured_returns_400(self, client):
        from app.services.visual_crossing_service import VisualCrossingNotConfigured

        mock_client = AsyncMock()
        mock_client.get_timeline.side_effect = VisualCrossingNotConfigured(
            "VISUAL_CROSSING_API_KEY unset"
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_client,
        ):
            response = client.get(
                "/api/v1/gs/visualcrossing/timeline?location=Seoul,South Korea"
            )
        assert response.status_code == 400



class TestCors:
    """개발 환경에서 임의의 로컬 origin CORS 가 허용되는지 확인."""

    def test_preflight_allows_arbitrary_local_origin_in_development(self, client):
        origin = "http://" + "localhost" + ":" + "5173"
        response = client.options(
            "/api/gs/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_actual_request_includes_cors_headers_in_development(self, client):
        # 개발 CORS 정규식: localhost / 127.0.0.1 / 사설망
        origin = "http://192.168.0.10:3000"
        response = client.get("/api/gs/health", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
