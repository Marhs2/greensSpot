"""Tests for VWorld 토지소유정보 WMS + 토지특성정보 endpoints and service methods."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.vworld_service import (
    VWorldBBoxError,
    VWorldClient,
    VWorldNotConfigured,
    client as vworld_client_factory,
)


def _run(coro):
    """asyncio.run wrapper for synchronous test functions."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# service helpers
# ---------------------------------------------------------------------------
def _make_async_client_with_content(content: bytes, content_type: str = "image/png") -> Any:
    resp = MagicMock()
    resp.raise_for_status = MagicMock(return_value=None)
    resp.content = content
    resp.headers = {"content-type": content_type}

    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    cls = MagicMock(return_value=instance)
    return cls


def _make_async_client_with_json(data: Any) -> Any:
    resp = MagicMock()
    resp.raise_for_status = MagicMock(return_value=None)
    resp.json = MagicMock(return_value=data)

    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    cls = MagicMock(return_value=instance)
    return cls


def _make_async_client_with_error(exc: Exception) -> Any:
    instance = MagicMock()
    instance.get = AsyncMock(side_effect=exc)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    cls = MagicMock(return_value=instance)
    return cls


# ---------------------------------------------------------------------------
# factory / configuration
# ---------------------------------------------------------------------------
def test_vworld_client_factory_returns_instance():
    c = vworld_client_factory()
    assert isinstance(c, VWorldClient)


def test_vworld_missing_api_key_raises():
    with patch("app.services.vworld_service.settings.vworld_api_key", ""):
        c = VWorldClient(api_key="")
        with pytest.raises(VWorldNotConfigured):
            c._check_key()


def test_vworld_whitespace_api_key_raises():
    c = VWorldClient(api_key="   ")
    with pytest.raises(VWorldNotConfigured):
        c._check_key()


# ---------------------------------------------------------------------------
# get_possession_wms — happy path
# ---------------------------------------------------------------------------
def test_get_possession_wms_success():
    png = b"\x89PNG\r\n\x1a\n"
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_content(png)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6,127.1"))

    assert result == png


def test_get_possession_wms_tuple_bbox():
    png = b"\x89PNG\r\n\x1a\n"
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_content(png)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_possession_wms("1111010100100010000", (37.5, 127.0, 37.6, 127.1)))

    assert result == png


def test_get_possession_wms_passes_params():
    captured: Dict[str, Any] = {}

    async def fake_get(url: str, params: Dict[str, Any] = None, **_kw):
        captured["url"] = url
        captured["params"] = params
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.content = b"\x89PNG"
        return resp

    instance = MagicMock()
    instance.get = fake_get
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)

    with patch("app.services.vworld_service.httpx.AsyncClient", cls):
        c = VWorldClient(api_key="K1")
        _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6,127.1", width=800, height=600))

    params = captured["params"]
    assert captured["url"] == "https://api.vworld.kr/ned/wms/getPossessionWMS"
    assert params["key"] == "K1"
    assert params["layer"] == "dt_d160"
    assert params["format"] == "image/png"
    assert params["bbox"] == "37.5,127.0,37.6,127.1"
    assert params["width"] == 800
    assert params["height"] == 600
    assert params["pnu"] == "1111010100100010000"


# ---------------------------------------------------------------------------
# get_possession_wms — failure modes
# ---------------------------------------------------------------------------
def test_get_possession_wms_html_error_returns_empty_bytes():
    html = b"<html><error></error></html>"
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_content(html)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6,127.1"))

    assert result == b""


def test_get_possession_wms_httpx_error_returns_empty_bytes():
    cls = _make_async_client_with_error(httpx.HTTPError("boom"))
    with patch("app.services.vworld_service.httpx.AsyncClient", cls):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6,127.1"))

    assert result == b""


def test_get_possession_wms_empty_content_returns_empty_bytes():
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_content(b"")):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6,127.1"))

    assert result == b""


def test_get_possession_wms_invalid_bbox_format_raises():
    c = VWorldClient(api_key="test-key")
    with pytest.raises(VWorldBBoxError):
        _run(c.get_possession_wms("1111010100100010000", "37.5,127.0,37.6"))


def test_get_possession_wms_non_numeric_bbox_raises():
    c = VWorldClient(api_key="test-key")
    with pytest.raises(VWorldBBoxError):
        _run(c.get_possession_wms("1111010100100010000", "a,b,c,d"))


def test_get_possession_wms_out_of_range_bbox_raises():
    c = VWorldClient(api_key="test-key")
    with pytest.raises(VWorldBBoxError):
        _run(c.get_possession_wms("1111010100100010000", "37.5,200.0,37.6,127.1"))


def test_get_possession_wms_reversed_bbox_raises():
    c = VWorldClient(api_key="test-key")
    with pytest.raises(VWorldBBoxError):
        _run(c.get_possession_wms("1111010100100010000", "37.6,127.0,37.5,127.1"))


# ---------------------------------------------------------------------------
# get_land_characteristics — happy path
# ---------------------------------------------------------------------------
def test_get_land_characteristics_success():
    api_response = {
        "landCharacteristics": {
            "items": [
                {"pnu": "1111010100100010000", "ldCode": "11110", "stdrYear": "2024"},
            ]
        }
    }
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_json(api_response)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_land_characteristics("1111010100100010000", "2024"))

    assert result["pnu"] == "1111010100100010000"
    assert result["count"] == 1
    assert result["dataAvailable"] is True
    assert result["source"] == "vworld"
    assert result["year"] == "2024"
    assert result["items"][0]["pnu"] == "1111010100100010000"


def test_get_land_characteristics_defaults_to_current_year():
    expected_year = str(datetime.utcnow().year)
    api_response = {"landCharacteristics": {"items": []}}
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_json(api_response)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_land_characteristics("1111010100100010000"))

    assert result["year"] == expected_year
    assert result["dataAvailable"] is False


def test_get_land_characteristics_flattens_single_dict_item():
    api_response = {
        "landCharacteristics": {
            "item": {"pnu": "1111010100100010000", "ldCode": "11110"},
        }
    }
    with patch("app.services.vworld_service.httpx.AsyncClient", _make_async_client_with_json(api_response)):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_land_characteristics("1111010100100010000"))

    assert result["count"] == 1
    assert result["items"][0]["pnu"] == "1111010100100010000"


# ---------------------------------------------------------------------------
# get_land_characteristics — failure modes
# ---------------------------------------------------------------------------
def test_get_land_characteristics_httpx_error_returns_fallback():
    cls = _make_async_client_with_error(httpx.HTTPError("boom"))
    with patch("app.services.vworld_service.httpx.AsyncClient", cls):
        c = VWorldClient(api_key="test-key")
        result = _run(c.get_land_characteristics("1111010100100010000", "2024"))

    assert result == {
        "pnu": "1111010100100010000",
        "items": [],
        "count": 0,
        "source": "vworld",
        "dataAvailable": False,
        "year": "2024",
    }


def test_get_land_characteristics_missing_key_raises():
    with patch("app.services.vworld_service.httpx.AsyncClient") as cls:
        with patch("app.services.vworld_service.settings.vworld_api_key", ""):
            c = VWorldClient(api_key="")
            with pytest.raises(VWorldNotConfigured):
                _run(c.get_land_characteristics("1111010100100010000"))
            cls.assert_not_called()


# ---------------------------------------------------------------------------
# integration router endpoints
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """FastAPI TestClient with startup DB init disabled."""
    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c


class TestVWorldPossessionEndpoint:
    """GET /api/v1/gs/vworld/possession/{pnu} endpoint tests."""

    def test_possession_wms_returns_png(self, client):
        mock_client = AsyncMock()
        mock_client.get_possession_wms.return_value = b"\x89PNG\r\n\x1a\n"
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get(
                "/api/v1/gs/vworld/possession/1111010100100010000?bbox=37.5,127.0,37.6,127.1"
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"\x89PNG\r\n\x1a\n"
        mock_client.get_possession_wms.assert_awaited_once_with(
            "1111010100100010000", "37.5,127.0,37.6,127.1", width=915, height=700
        )

    def test_possession_wms_unavailable_returns_metadata(self, client):
        mock_client = AsyncMock()
        mock_client.get_possession_wms.return_value = b""
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get(
                "/api/v1/gs/vworld/possession/1111010100100010000?bbox=37.5,127.0,37.6,127.1"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pnu"] == "1111010100100010000"
        assert body["contentType"] == "image/png"
        assert body["dataAvailable"] is False

    def test_possession_wms_missing_bbox_returns_422(self, client):
        response = client.get("/api/v1/gs/vworld/possession/1111010100100010000")
        assert response.status_code == 422

    def test_possession_wms_unconfigured_key_returns_400(self, client):
        mock_client = AsyncMock()
        mock_client.get_possession_wms.side_effect = VWorldNotConfigured("VWORLD_API_KEY unset")
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get(
                "/api/v1/gs/vworld/possession/1111010100100010000?bbox=37.5,127.0,37.6,127.1"
            )

        assert response.status_code == 400
        assert "VWORLD_API_KEY" in response.json()["detail"]


class TestVWorldCharacteristicsEndpoint:
    """GET /api/v1/gs/vworld/characteristics/{pnu} endpoint tests."""

    def test_characteristics_returns_data(self, client):
        mock_client = AsyncMock()
        mock_client.get_land_characteristics.return_value = {
            "pnu": "1111010100100010000",
            "items": [{"pnu": "1111010100100010000"}],
            "count": 1,
            "source": "vworld",
            "dataAvailable": True,
            "year": "2024",
        }
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get(
                "/api/v1/gs/vworld/characteristics/1111010100100010000?stdrYear=2024"
            )

        assert response.status_code == 200
        body = response.json()
        assert body["pnu"] == "1111010100100010000"
        assert body["count"] == 1
        assert body["dataAvailable"] is True
        assert body["year"] == "2024"
        mock_client.get_land_characteristics.assert_awaited_once_with(
            "1111010100100010000", "2024"
        )

    def test_characteristics_unconfigured_key_returns_400(self, client):
        mock_client = AsyncMock()
        mock_client.get_land_characteristics.side_effect = VWorldNotConfigured("VWORLD_API_KEY unset")
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get("/api/v1/gs/vworld/characteristics/1111010100100010000")

        assert response.status_code == 400
        assert "VWORLD_API_KEY" in response.json()["detail"]

    def test_characteristics_empty_data_returns_200(self, client):
        mock_client = AsyncMock()
        mock_client.get_land_characteristics.return_value = {
            "pnu": "1111010100100010000",
            "items": [],
            "count": 0,
            "source": "vworld",
            "dataAvailable": False,
            "year": "2024",
        }
        with patch("app.api.v1.integration_router.vworld_client", return_value=mock_client):
            response = client.get("/api/v1/gs/vworld/characteristics/1111010100100010000")

        assert response.status_code == 200
        body = response.json()
        assert body["dataAvailable"] is False
        assert body["count"] == 0
