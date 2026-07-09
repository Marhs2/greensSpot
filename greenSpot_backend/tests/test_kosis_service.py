"""
KosisClient 단위 테스트.

httpx.AsyncClient 를 unittest.mock 으로 대체하여 KOSIS Open API 응답을 시뮬레이션한다.
pytest-asyncio 없이 동기 테스트 함수 내부에서 asyncio.run() 으로 코루틴을 실행한다.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.config import settings as app_settings
from app.services.kosis_service import (
    DISTRICT_TO_OBJ_L1,
    KosisClient,
    KosisNotConfigured,
    client,
)


def _run(coro):
    """asyncio.run 의 얇은 래퍼."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# httpx.AsyncClient mock helpers
# ---------------------------------------------------------------------------
def _make_async_client_with_rows(rows: Any) -> MagicMock:
    """rows 데이터를 JSON 으로 반환하는 AsyncClient mock class."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock(return_value=None)
    resp.json = MagicMock(return_value=rows)

    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)

    cls = MagicMock(return_value=instance)
    return cls


def _patch_async_client(rows: Any):
    return patch("app.services.kosis_service.httpx.AsyncClient", _make_async_client_with_rows(rows))


def _make_async_client_with_side_effect(side_effect) -> MagicMock:
    """AsyncClient.get 이 특정 예외를 던지도록 하는 mock class."""
    instance = MagicMock()
    instance.get = AsyncMock(side_effect=side_effect)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)
    return cls


# ---------------------------------------------------------------------------
# factory / configuration
# ---------------------------------------------------------------------------
def test_client_factory_returns_kosis_client():
    c = client()
    assert isinstance(c, KosisClient)


def test_missing_api_key_raises_kosis_not_configured():
    c = KosisClient(api_key="")
    with pytest.raises(KosisNotConfigured):
        c._check_key()


def test_whitespace_api_key_raises_kosis_not_configured():
    c = KosisClient(api_key="   ")
    with pytest.raises(KosisNotConfigured):
        c._check_key()


# ---------------------------------------------------------------------------
# district mapping
# ---------------------------------------------------------------------------
def test_district_to_obj_l1_known_districts():
    assert KosisClient._district_to_obj_l1("중구") == "11140"
    assert KosisClient._district_to_obj_l1("성동구") == "11200"
    assert KosisClient._district_to_obj_l1("용산구") == "11170"
    assert KosisClient._district_to_obj_l1("동대문구") == "11230"
    assert KosisClient._district_to_obj_l1("마포구") == "11440"
    assert KosisClient._district_to_obj_l1("강남구") == "11680"


def test_district_to_obj_l1_unknown_district_raises():
    with pytest.raises(ValueError):
        KosisClient._district_to_obj_l1("없는구")


def test_district_mapping_constant_is_complete():
    # 서울 25개 자치구
    assert len(DISTRICT_TO_OBJ_L1) == 25
    assert "용산구" in DISTRICT_TO_OBJ_L1
    assert "마포구" in DISTRICT_TO_OBJ_L1


# ---------------------------------------------------------------------------
# get_population — happy path
# ---------------------------------------------------------------------------
def test_get_population_success():
    rows: List[Dict[str, Any]] = [{"DT": "12345"}]
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result == {
        "source": "kosis",
        "district": "강남구",
        "year": 2023,
        "population": 12345,
        "dataAvailable": True,
    }


def test_get_population_success_comma_separated_value():
    rows: List[Dict[str, Any]] = [{"DT": "12,345"}]
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["population"] == 12345
    assert result["dataAvailable"] is True


def test_get_population_success_falls_back_to_other_keys():
    rows: List[Dict[str, Any]] = [{"C1": "9876"}]
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["population"] == 9876
    assert result["dataAvailable"] is True


def test_get_population_year_defaults_to_previous_year():
    rows: List[Dict[str, Any]] = [{"DT": "100"}]
    expected_year = datetime.now(timezone.utc).year - 1
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("중구"))

    assert result["year"] == expected_year
    assert result["dataAvailable"] is True


# ---------------------------------------------------------------------------
# get_household — happy path
# ---------------------------------------------------------------------------
def test_get_household_success():
    rows: List[Dict[str, Any]] = [{"DT": "4567"}]
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_household("마포구", year=2022))

    assert result == {
        "source": "kosis",
        "district": "마포구",
        "year": 2022,
        "households": 4567,
        "dataAvailable": True,
    }


# ---------------------------------------------------------------------------
# failure modes
# ---------------------------------------------------------------------------
def test_get_population_empty_response_returns_fallback():
    with _patch_async_client([]):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result == {
        "source": "kosis",
        "district": "강남구",
        "year": 2023,
        "population": None,
        "dataAvailable": False,
    }


def test_get_population_dict_with_empty_list_returns_fallback():
    with _patch_async_client({"list": []}):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False
    assert result["population"] is None


def test_get_population_error_response_returns_fallback():
    with _patch_async_client({"errCd": "20", "errMsg": "NO_DATA"}):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False
    assert result["population"] is None


def test_get_population_no_numeric_value_returns_fallback():
    rows: List[Dict[str, Any]] = [{"ITM_NM": "총인구", "OBJ_NM": "강남구"}]
    with _patch_async_client(rows):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False
    assert result["population"] is None


def test_get_population_httpx_http_error_returns_fallback():
    cls = _make_async_client_with_side_effect(httpx.HTTPError("boom"))
    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result == {
        "source": "kosis",
        "district": "강남구",
        "year": 2023,
        "population": None,
        "dataAvailable": False,
    }


def test_get_population_httpx_status_error_returns_fallback():
    resp = MagicMock()
    resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())
    )
    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)

    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False


def test_get_population_key_error_returns_fallback():
    resp = MagicMock()
    resp.raise_for_status = MagicMock(return_value=None)

    def _bad_json():
        raise KeyError("missing")

    resp.json = _bad_json
    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)

    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False


def test_get_population_value_error_returns_fallback():
    resp = MagicMock()
    resp.raise_for_status = MagicMock(return_value=None)
    resp.json = MagicMock(side_effect=ValueError("bad json"))
    instance = MagicMock()
    instance.get = AsyncMock(return_value=resp)
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)

    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("강남구", year=2023))

    assert result["dataAvailable"] is False


def test_get_population_unknown_district_returns_fallback_without_http_call():
    with patch("app.services.kosis_service.httpx.AsyncClient") as cls:
        c = KosisClient(api_key="test-key")
        result = _run(c.get_population("없는구", year=2023))

    cls.assert_not_called()
    assert result == {
        "source": "kosis",
        "district": "없는구",
        "year": 2023,
        "population": None,
        "dataAvailable": False,
    }


def test_get_population_missing_key_raises_before_request():
    with patch("app.services.kosis_service.httpx.AsyncClient") as cls:
        c = KosisClient(api_key="")
        with pytest.raises(KosisNotConfigured):
            _run(c.get_population("강남구", year=2023))
        cls.assert_not_called()


# ---------------------------------------------------------------------------
# get_household — failure modes (대칭성 검증)
# ---------------------------------------------------------------------------
def test_get_household_empty_response_returns_fallback():
    with _patch_async_client([]):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_household("마포구", year=2023))

    assert result == {
        "source": "kosis",
        "district": "마포구",
        "year": 2023,
        "households": None,
        "dataAvailable": False,
    }


def test_get_household_httpx_error_returns_fallback():
    cls = _make_async_client_with_side_effect(httpx.HTTPError("boom"))
    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="test-key")
        result = _run(c.get_household("마포구", year=2023))

    assert result["dataAvailable"] is False
    assert result["households"] is None


def test_get_household_unknown_district_returns_fallback():
    with patch("app.services.kosis_service.httpx.AsyncClient") as cls:
        c = KosisClient(api_key="test-key")
        result = _run(c.get_household("없는구", year=2023))

    cls.assert_not_called()
    assert result["dataAvailable"] is False
    assert result["households"] is None


# ---------------------------------------------------------------------------
# API 파라미터 검증
# ---------------------------------------------------------------------------
def test_get_population_passes_expected_query_params():
    captured: Dict[str, Any] = {}

    async def fake_get(url: str, params: Optional[Dict[str, Any]] = None, **_kw):
        captured["url"] = url
        captured["params"] = params
        resp = MagicMock()
        resp.raise_for_status = MagicMock(return_value=None)
        resp.json = MagicMock(return_value=[{"DT": "1"}])
        return resp

    instance = MagicMock()
    instance.get = fake_get
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=None)
    cls = MagicMock(return_value=instance)

    with patch("app.services.kosis_service.httpx.AsyncClient", cls):
        c = KosisClient(api_key="K1")
        _run(c.get_population("강남구", year=2023))

    params = captured["params"]
    assert params["method"] == "getList"
    assert params["apiKey"] == "K1"
    assert params["itmId"] == "T1"
    assert params["objL1"] == "11680"  # 강남구
    assert params["objL2"] == ""
    assert params["objL3"] == ""
    assert params["objL4"] == ""
    assert params["objL5"] == ""
    assert params["format"] == "json"
    assert params["jsonVD"] == "Y"
    assert params["prdSe"] == "Y"
    assert params["startPrdDe"] == "2023"
    assert params["endPrdDe"] == "2023"
    assert captured["url"] == app_settings.kosis_base_url
