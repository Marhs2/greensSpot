"""실제 API 연동(추정 → 실제) 관련 단위/통합 테스트.

테스트 목표:
- VWorld 토지특성정보로 parcelType 실제값이 반영되는지 확인
- AirKorea/토지소유/토양 API 키 미설정 시 graceful fallback 확인
- dataProvenance의 actual 플래그가 API 성공/실패에 따라 동기화되는지 확인
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services import airkorea_service, land_ownership_service, soil_service
from app.services.vworld_discovery_service import (
    build_data_provenance,
    build_parcel_from_feature,
    classify_parcel_type_from_land_characteristics,
)


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# classify_parcel_type_from_land_characteristics
# ---------------------------------------------------------------------------
def test_classify_parcel_type_from_land_characteristics_maps_lndcgr():
    # UI 호환 parcelType
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "대"}]) == "VACANT_LOT"
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "임야"}]) == "UNUSED_LAND"
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "공장용지"}]) == "BROWNFIELD"
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "공원"}]) == "UNUSED_LAND"
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "잡종지"}]) == "UNUSED_LAND"


def test_classify_parcel_type_from_land_characteristics_falls_back_to_code():
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCode": "대"}]) == "VACANT_LOT"


def test_classify_parcel_type_from_land_characteristics_returns_none_for_unknown():
    assert classify_parcel_type_from_land_characteristics([{"lndcgrCodeNm": "미확인"}]) is None
    assert classify_parcel_type_from_land_characteristics([]) is None


# ---------------------------------------------------------------------------
# build_data_provenance
# ---------------------------------------------------------------------------
def test_build_data_provenance_flags_actual_when_requested():
    prov = build_data_provenance(
        "VWorld/LP_PA_CBND_BUBUN",
        regulations=[{"code": "URBAN_ZONE"}],
        parcel_type_actual=True,
        ownership_actual=True,
        soil_type_actual=True,
        air_quality_actual=True,
    )
    assert prov["parcelType"]["actual"] is True
    assert prov["parcelType"]["source"] == "VWorld 토지특성정보"
    assert prov["ownership"]["actual"] is True
    assert prov["soilType"]["actual"] is True
    assert prov["airQuality"]["actual"] is True
    assert prov["airQuality"]["source"] == "AirKorea"


def test_build_data_provenance_defaults_keep_estimated():
    prov = build_data_provenance("VWorld/LP_PA_CBND_BUBUN", regulations=[])
    assert prov["parcelType"]["actual"] is False
    assert prov["ownership"]["actual"] is False
    assert prov["soilType"]["actual"] is False
    assert prov["airQuality"]["actual"] is False


# ---------------------------------------------------------------------------
# airkorea_service
# ---------------------------------------------------------------------------
def test_airkorea_client_returns_fallback_when_unconfigured():
    with patch("app.services.airkorea_service.settings.airkorea_api_key", ""):
        c = airkorea_service.AirKoreaClient()
        result = _run(c.get_air_quality("용산구", fallback=30.0))
    assert result["pm25"] == 30.0
    assert result["dataAvailable"] is False
    assert "미연동" in result["source"]


def test_airkorea_client_parses_pm25_from_response():
    response = {
        "response": {
            "body": {
                "items": [
                    {"stationName": "용산", "pm25Value": "27.5"},
                    {"stationName": "강남", "pm25Value": "31.0"},
                ]
            }
        }
    }
    with patch("app.services.airkorea_service.httpx.AsyncClient") as cls:
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value=response)
        instance = MagicMock()
        instance.get = AsyncMock(return_value=resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        cls.return_value = instance

        c = airkorea_service.AirKoreaClient(api_key="K", base_url="[REDACTED-URL]")
        result = _run(c.get_air_quality("용산구"))

    assert result["dataAvailable"] is True
    assert result["pm25"] == 27.5
    assert result["station"] == "용산"


def test_airkorea_client_uses_fallback_on_http_error():
    with patch("app.services.airkorea_service.httpx.AsyncClient") as cls:
        instance = MagicMock()
        instance.get = AsyncMock(side_effect=httpx.HTTPError("boom"))
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        cls.return_value = instance

        c = airkorea_service.AirKoreaClient(api_key="K", base_url="[REDACTED-URL]")
        result = _run(c.get_air_quality("용산구", fallback=20.0))

    assert result["pm25"] == 20.0
    assert result["dataAvailable"] is False


# ---------------------------------------------------------------------------
# land_ownership_service
# ---------------------------------------------------------------------------
def test_land_ownership_client_returns_unknown_when_unconfigured():
    with patch("app.services.land_ownership_service.settings.land_ownership_api_key", ""):
        c = land_ownership_service.LandOwnershipClient()
        result = _run(c.get_ownership("1117010300101680003"))
    assert result["ownership"] == "UNKNOWN"
    assert result["dataAvailable"] is False


def test_land_ownership_client_parses_private():
    response = {
        "response": {
            "body": {
                "items": [{"ownerSe": "개인"}]
            }
        }
    }
    with patch("app.services.land_ownership_service.httpx.AsyncClient") as cls:
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value=response)
        instance = MagicMock()
        instance.get = AsyncMock(return_value=resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        cls.return_value = instance

        c = land_ownership_service.LandOwnershipClient(api_key="K", base_url="[REDACTED-URL]")
        result = _run(c.get_ownership("1117010300101680003"))

    assert result["dataAvailable"] is True
    assert result["ownership"] == "PRIVATE"


# ---------------------------------------------------------------------------
# soil_service
# ---------------------------------------------------------------------------
def test_soil_client_returns_unknown_when_unconfigured():
    with patch("app.services.soil_service.settings.soil_api_key", ""):
        c = soil_service.SoilClient()
        result = _run(c.get_soil_type("1117010300101680003"))
    assert result["soilType"] == "UNKNOWN"
    assert result["dataAvailable"] is False


def test_soil_client_parses_loam():
    response = {
        "response": {
            "body": {
                "items": [{"soilTexture": "양토"}]
            }
        }
    }
    with patch("app.services.soil_service.httpx.AsyncClient") as cls:
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value=response)
        instance = MagicMock()
        instance.get = AsyncMock(return_value=resp)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        cls.return_value = instance

        c = soil_service.SoilClient(api_key="K", base_url="[REDACTED-URL]")
        result = _run(c.get_soil_type("1117010300101680003"))

    assert result["dataAvailable"] is True
    assert result["soilType"] == "LOAM"


# ---------------------------------------------------------------------------
# build_parcel_from_feature integration
# ---------------------------------------------------------------------------
async def _mock_vworld_client(
    *,
    land_chars: Dict[str, Any] | None = None,
    regulations: list | None = None,
):
    mock = MagicMock()
    mock.get_land_characteristics = AsyncMock(return_value=land_chars or {"items": [], "dataAvailable": False})
    mock.get_regulations_at_point = AsyncMock(return_value=regulations or [])
    return mock


@pytest.mark.asyncio
async def test_build_parcel_from_feature_uses_actual_parcel_type():
    from app.services.ttl_cache import cache_clear
    cache_clear()
    feature = {
        "properties": {
            "pnu": "1117010300101680003",
            "addr": "서울특별시 용산구 용산동4가 168-3",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [126.980, 37.526],
                [126.981, 37.526],
                [126.981, 37.527],
                [126.980, 37.527],
                [126.980, 37.526],
            ]],
        },
    }
    mock_vworld = await _mock_vworld_client(
        land_chars={
            "items": [{"pnu": "1117010300101680003", "lndcgrCodeNm": "임야"}],
            "dataAvailable": True,
        }
    )

    with patch("app.services.vworld_discovery_service.vworld_client", return_value=mock_vworld):
        with patch("app.services.vworld_discovery_service.airkorea_client") as aq_factory:
            aq_factory.return_value.get_air_quality = AsyncMock(
                return_value={"pm25": None, "dataAvailable": False}
            )
        with patch("app.services.vworld_discovery_service.land_ownership_client") as lo_factory:
            lo_factory.return_value.get_ownership = AsyncMock(
                return_value={"ownership": "UNKNOWN", "dataAvailable": False}
            )
        with patch("app.services.vworld_discovery_service.soil_client") as soil_factory:
            soil_factory.return_value.get_soil_type = AsyncMock(
                return_value={"soilType": "UNKNOWN", "dataAvailable": False}
            )

        result = await build_parcel_from_feature(feature)

    assert result is not None
    assert result["parcel_type"] == "UNUSED_LAND"
    assert result.get("land_category") == "FOREST"
    assert result["data_provenance"]["parcelType"]["actual"] is True
    assert result["data_provenance"]["parcelType"]["source"] == "VWorld 토지특성정보"


@pytest.mark.asyncio
async def test_build_parcel_from_feature_falls_back_when_land_chars_empty():
    from app.services.ttl_cache import cache_clear
    cache_clear()
    feature = {
        "properties": {
            "pnu": "1117010300101680003",
            "addr": "서울특별시 용산구 용산동4가 168-3",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [126.980, 37.526],
                [126.981, 37.526],
                [126.981, 37.527],
                [126.980, 37.527],
                [126.980, 37.526],
            ]],
        },
    }
    mock_vworld = await _mock_vworld_client(land_chars={"items": [], "dataAvailable": False})

    with patch("app.services.vworld_discovery_service.vworld_client", return_value=mock_vworld):
        with patch("app.services.vworld_discovery_service.airkorea_client") as aq_factory:
            aq_factory.return_value.get_air_quality = AsyncMock(
                return_value={"pm25": None, "dataAvailable": False}
            )
        with patch("app.services.vworld_discovery_service.land_ownership_client") as lo_factory:
            lo_factory.return_value.get_ownership = AsyncMock(
                return_value={"ownership": "UNKNOWN", "dataAvailable": False}
            )
        with patch("app.services.vworld_discovery_service.soil_client") as soil_factory:
            soil_factory.return_value.get_soil_type = AsyncMock(
                return_value={"soilType": "UNKNOWN", "dataAvailable": False}
            )

        result = await build_parcel_from_feature(feature)

    assert result is not None
    assert result["data_provenance"]["parcelType"]["actual"] is False
