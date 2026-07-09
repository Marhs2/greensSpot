"""live_search_service 단위 테스트."""
from __future__ import annotations

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.live_search_service import _internal_to_api, _LIVE_CACHE, extract_region_name, live_get_parcel, resolve_region
from app.services.vworld_discovery_service import build_data_provenance


def _run(coro):
    """asyncio.run 의 얇은 래퍼."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# extract_region_name
# ---------------------------------------------------------------------------
def test_extract_region_name_city_district_with_space():
    assert extract_region_name("성남시 분당구 텃밭 후보") == "성남시 분당구"


def test_extract_region_name_district_only():
    assert extract_region_name("강남구 옥상") == "강남구"


def test_extract_region_name_city_only():
    assert extract_region_name("제주시") == "제주시"


def test_extract_region_name_province_city_district():
    result = extract_region_name("경기도 성남시 분당구")
    assert result in ("경기도 성남시 분당구", "성남시 분당구")


def test_extract_region_name_suwon_paldal():
    assert extract_region_name("수원시 팔달구 장안동") == "수원시 팔달구"


def test_extract_region_name_seoul_gangnam():
    assert extract_region_name("서울시 강남구 논현동") == "서울시 강남구"


def test_extract_region_name_seoul_special_city_gangnam():
    """광역시/특별시 + 구 패턴에서 시/도 접미사를 보존해야 한다."""
    assert extract_region_name("서울특별시 강남구") == "서울특별시 강남구"


def test_extract_region_name_no_region():
    assert extract_region_name("텃밭 후보") is None


# ---------------------------------------------------------------------------
# resolve_region — filters must preserve spaces in region_name
# ---------------------------------------------------------------------------
def _sigg_response(name: str, full_name: str, sig_cd: str) -> Dict[str, Any]:
    return {
        "status": "OK",
        "record": {"total": 1},
        "result": {
            "featureCollection": {
                "features": [
                    {
                        "properties": {
                            "sig_kor_nm": name,
                            "full_nm": full_name,
                            "sig_cd": sig_cd,
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [127.0, 37.0],
                                    [127.1, 37.0],
                                    [127.1, 37.1],
                                    [127.0, 37.1],
                                    [127.0, 37.0],
                                ]
                            ],
                        },
                    }
                ]
            }
        },
    }


def test_resolve_region_preserves_space_in_filter():
    """VWorld like 필터에 공백이 제거되지 않고 전달되어야 한다."""
    response = _sigg_response("성남시 분당구", "경기도 성남시 분당구", "41135")
    captured_attrs = []

    async def _patched_get(url, params=None, **kwargs):
        if params and "attrFilter" in params:
            captured_attrs.append(params["attrFilter"])
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value={"response": response})
        return resp

    instance = MagicMock()
    instance.get = AsyncMock(side_effect=_patched_get)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=instance):
        with patch("app.services.live_search_service.VWorldDataClient._check_key", return_value=None):
            result = _run(resolve_region("성남시 분당구"))

    assert result is not None
    assert result["name"] == "성남시 분당구"
    assert result["full_name"] == "경기도 성남시 분당구"
    assert result["sig_cd"] == "41135"
    assert any("성남시 분당구" in attr for attr in captured_attrs)
    assert not any("성남시분당구" in attr for attr in captured_attrs)


def test_resolve_region_falls_back_to_full_nm():
    """sig_kor_nm 검색이 실패하면 full_nm 검색으로 fallback 한다."""
    not_found = {"status": "NOT_FOUND"}
    full_match = _sigg_response("성남시 분당구", "경기도 성남시 분당구", "41135")
    captured_attrs = []

    async def _patched_get(url, params=None, **kwargs):
        if params and "attrFilter" in params:
            captured_attrs.append(params["attrFilter"])
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        if params.get("attrFilter", "").startswith("sig_kor_nm"):
            resp.json = MagicMock(return_value={"response": not_found})
        else:
            resp.json = MagicMock(return_value={"response": full_match})
        return resp

    instance = MagicMock()
    instance.get = AsyncMock(side_effect=_patched_get)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=instance):
        with patch("app.services.live_search_service.VWorldDataClient._check_key", return_value=None):
            result = _run(resolve_region("성남시 분당구"))

    assert result is not None
    assert result["name"] == "성남시 분당구"
    assert captured_attrs == [
        "sig_kor_nm:like:성남시 분당구",
        "full_nm:like:성남시 분당구",
    ]


def test_resolve_region_no_match_returns_none():
    """두 필터 모두 실패하면 None 을 반환한다."""
    not_found = {"status": "NOT_FOUND"}

    async def _patched_get(url, params=None, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value={"response": not_found})
        return resp

    instance = MagicMock()
    instance.get = AsyncMock(side_effect=_patched_get)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=instance):
        with patch("app.services.live_search_service.VWorldDataClient._check_key", return_value=None):
            result = _run(resolve_region("성남시 분당구"))

    assert result is None


# ---------------------------------------------------------------------------
# dataProvenance
# ---------------------------------------------------------------------------
def _sample_internal_row():
    return {
        "id": "VW-1111010100100210000",
        "name": "test parcel",
        "district": "중구",
        "neighborhood": "test동",
        "lat": 37.56,
        "lng": 126.99,
        "area_sqm": 500.0,
        "parcel_type": "VACANT_LOT",
        "ownership": "UNKNOWN",
        "soil_type": "UNKNOWN",
        "solar_irradiance": 4.0,
        "monthly_irradiance": [1.0, 2.0, 3.0],
        "sunlight_hours": 6.0,
        "heat_island": 2.5,
        "surface_temp_summer": 36.0,
        "air_quality": 25.0,
        "nearby_households": 1000,
        "pedestrian_flow": 2000,
        "road_adjacent": True,
        "water_access": True,
        "electricity_access": True,
        "nearby_schools": 2,
        "nearby_hospitals": 1,
        "nearby_parks": 1,
        "nearby_subway_stations": 1,
        "regulatory_restriction": "NONE",
        "regulations": [],
        "sumok_feasibility": {"status": "ALLOWED", "confidence": 0.86},
        "confidence": 0.86,
        "pnu": "1111010100100210000",
        "scores": {
            "tree_score": 70,
            "garden_score": 80,
            "solar_score": 60,
            "top_recommendation": "GARDEN",
            "uncertainty": 6,
        },
        "data_source": "VWorld/LP_PA_CBND_BUBUN",
    }


def test_build_data_provenance_structure():
    """dataProvenance entries must contain source, dataType, actual."""
    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN", regulations=[])

    assert isinstance(provenance, dict)
    required_keys = {
        "boundary",
        "location",
        "areaSqm",
        "regulations",
        "parcelType",
        "ownership",
        "soilType",
        "solarIrradiance",
        "sunlightHours",
        "monthlyIrradiance",
        "heatIsland",
        "surfaceTempSummer",
        "airQuality",
        "roadAdjacent",
        "waterAccess",
        "electricityAccess",
        "nearbyHouseholds",
        "scores",
        "sumokFeasibility",
        "kmaApiKeyConfigured",
        "visualCrossingConfigured",
    }
    assert set(provenance.keys()) == required_keys
    for key, entry in provenance.items():
        if key in ("kmaApiKeyConfigured", "visualCrossingConfigured"):
            assert isinstance(entry, bool)
            continue
        assert isinstance(entry, dict)
        assert "source" in entry and isinstance(entry["source"], str)
        assert "dataType" in entry and isinstance(entry["dataType"], str)
        assert "actual" in entry and isinstance(entry["actual"], bool)


def test_build_data_provenance_vworld_fields_actual_when_live():
    """VWorld boundary/location are actual for live VWorld parcels."""
    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN", regulations=[{"code": "GREEN_BELT"}])
    assert provenance["boundary"]["actual"] is True
    assert provenance["location"]["actual"] is True
    assert provenance["regulations"]["actual"] is True


def test_build_data_provenance_estimated_fields_are_false():
    """Estimated fields always have actual=False."""
    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN")
    assert provenance["parcelType"]["actual"] is False
    assert provenance["ownership"]["actual"] is False
    assert provenance["soilType"]["actual"] is False
    assert provenance["airQuality"]["actual"] is False


def test_build_data_provenance_scores_and_feasibility_actual():
    """scores and sumokFeasibility are always actual."""
    provenance = build_data_provenance("some-other-source")
    assert provenance["scores"]["actual"] is True
    assert provenance["sumokFeasibility"]["actual"] is True


@patch("app.services.vworld_discovery_service.settings")
def test_build_data_provenance_vc_actual_only_when_fetched(mock_settings):
    """VC 키가 있어도 조회 성공 플래그가 없으면 actual=false."""
    mock_settings.kma_api_key = "kma-key"
    mock_settings.kosis_api_key = ""
    mock_settings.visual_crossing_api_key = "vc-key"
    mock_settings.visual_crossing_base_url = "https://weather.visualcrossing.com/"

    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN")
    assert provenance["solarIrradiance"]["actual"] is False
    assert provenance["heatIsland"]["actual"] is False
    assert provenance["visualCrossingConfigured"] is True
    assert provenance["kmaApiKeyConfigured"] is True

    fetched = build_data_provenance(
        "VWorld/LP_PA_CBND_BUBUN",
        solar_actual=True,
        sunlight_actual=True,
        heat_actual=True,
        surface_temp_actual=True,
    )
    assert fetched["solarIrradiance"]["actual"] is True
    assert fetched["sunlightHours"]["actual"] is True
    assert fetched["heatIsland"]["actual"] is True
    assert fetched["surfaceTempSummer"]["actual"] is True
    assert fetched["heatIsland"]["source"] == "Visual Crossing"


@patch("app.services.vworld_discovery_service.settings")
def test_build_data_provenance_visualcrossing_unconfigured(mock_settings):
    """Visual Crossing 미연동 시 기온 기반 필드는 미연동으로 표시된다."""
    mock_settings.kma_api_key = ""
    mock_settings.kosis_api_key = ""
    mock_settings.visual_crossing_api_key = ""
    mock_settings.visual_crossing_base_url = ""

    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN")
    assert provenance["heatIsland"]["actual"] is False
    assert provenance["surfaceTempSummer"]["actual"] is False
    assert "(미연동)" in provenance["heatIsland"]["source"]
    assert "(미연동)" in provenance["surfaceTempSummer"]["source"]
    assert provenance["visualCrossingConfigured"] is False


@patch("app.services.vworld_discovery_service.settings")
def test_build_data_provenance_vworld_boundary_actual(mock_settings):
    """VWorld 출처일 때 boundary/location 은 actual 이다."""
    mock_settings.visual_crossing_api_key = ""
    mock_settings.visual_crossing_base_url = ""

    provenance = build_data_provenance("VWorld/LP_PA_CBND_BUBUN")
    assert provenance["boundary"]["actual"] is True
    assert provenance["location"]["actual"] is True
    assert provenance["boundary"]["source"] == "VWorld"
    assert provenance["location"]["source"] == "VWorld"


def test_internal_to_api_propagates_data_provenance():
    """_internal_to_api copies data_provenance to camelCase dataProvenance."""
    row = _sample_internal_row()
    row["data_provenance"] = build_data_provenance(row["data_source"], regulations=row["regulations"])

    parcel, _ = _internal_to_api(row)

    assert "dataProvenance" in parcel
    assert parcel["dataProvenance"] is row["data_provenance"]
    assert parcel["dataProvenance"]["scores"]["actual"] is True


def test_internal_to_api_handles_missing_accessibility_fields():
    """deprecated 된 사회·접근성 지표가 누락돼도 KeyError 없이 기본값을 반환한다."""
    row = _sample_internal_row()
    for key in [
        "nearby_households",
        "pedestrian_flow",
        "road_adjacent",
        "water_access",
        "electricity_access",
        "nearby_schools",
        "nearby_hospitals",
        "nearby_parks",
        "nearby_subway_stations",
        "regulatory_restriction",
    ]:
        row.pop(key, None)

    parcel, _ = _internal_to_api(row)

    assert parcel["nearbyHouseholds"] is None
    assert parcel["pedestrianFlow"] is None
    assert parcel["roadAdjacent"] is False
    assert parcel["waterAccess"] is False
    assert parcel["electricityAccess"] is False
    assert parcel["nearbySchools"] is None
    assert parcel["nearbyHospitals"] is None
    assert parcel["nearbyParks"] is None
    assert parcel["nearbySubwayStations"] is None
    assert parcel["regulatoryRestriction"] == ""


def _parcel_response(pnu: str = "1111010100100210000") -> Dict[str, Any]:
    return {
        "status": "OK",
        "record": {"total": 1},
        "result": {
            "featureCollection": {
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"pnu": pnu},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [127.0, 37.0],
                                    [127.1, 37.0],
                                    [127.1, 37.1],
                                    [127.0, 37.1],
                                    [127.0, 37.0],
                                ]
                            ],
                        },
                    }
                ]
            }
        },
    }


def test_live_get_parcel_retries_and_succeeds():
    """_data_get이 두 차례 실패 후 세 번째에 성공하면 live_get_parcel도 성공해야 한다."""
    parcel_id = "VW-1111010100100210000"
    _LIVE_CACHE.clear()

    responses = [
        {"status": "ERROR"},
        {"status": "ERROR"},
        _parcel_response(),
    ]

    async def _fake_get(client, http, params):
        # httpx.AsyncClient context manager returns itself when patched below.
        return responses.pop(0)

    instance = MagicMock()
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.live_search_service._data_get", new=AsyncMock(side_effect=_fake_get)) as mock_get:
        with patch("httpx.AsyncClient", return_value=instance):
            with patch(
                "app.services.live_search_service.VWorldDataClient._check_key",
                return_value=None,
            ):
                with patch(
                    "app.services.live_search_service.build_parcel_from_feature",
                    new=AsyncMock(return_value=_sample_internal_row()),
                ):
                    result = _run(live_get_parcel(parcel_id))

    assert result is not None
    assert result["source"] == "vworld_live"
    assert result["parcel"]["id"] == parcel_id
    assert mock_get.call_count == 3
