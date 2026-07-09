"""report_service 단위 테스트."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.report_service import generate_report


def _run(coro):
    """asyncio.run 의 얇은 래퍼."""
    return asyncio.run(coro)


def _sample_live_parcel_detail():
    return {
        "parcel": {
            "id": "VW-1111010100100210000",
            "name": "테스트 공유지",
            "district": "중구",
            "neighborhood": "test동",
            "lat": 37.56,
            "lng": 126.99,
            "areaSqm": 500.0,
            "parcelType": "VACANT_LOT",
            "ownership": "UNKNOWN",
            "soilType": "UNKNOWN",
            "regulatoryRestriction": "NONE",
            "solarIrradiance": 4.0,
            "sunlightHours": 6.0,
            "heatIsland": 2.5,
            "surfaceTempSummer": 36.0,
            "airQuality": 25.0,
            "nearbyHouseholds": 1000,
            "pedestrianFlow": 2000,
            "nearbySchools": 2,
            "nearbyHospitals": 1,
            "nearbyParks": 1,
            "nearbySubwayStations": 1,
            "confidence": 0.86,
        },
        "scores": {
            "treeScore": 70,
            "gardenScore": 80,
            "solarScore": 60,
            "uncertainty": 6,
        },
        "source": "live",
    }


def test_generate_report_uses_resolved_live_parcel():
    """VW-... ID 등 DB에 없는 live parcel도 get_parcel_detail_resolved를 통해 리포트가 생성돼야 한다."""
    db = MagicMock()
    parcel_id = "VW-1111010100100210000"

    with patch(
        "app.services.report_service.get_parcel_detail_resolved",
        new=AsyncMock(return_value=_sample_live_parcel_detail()),
    ) as mock_resolved:
        report = _run(generate_report(db, parcel_id))

    mock_resolved.assert_awaited_once_with(db, parcel_id)
    assert isinstance(report, str)
    assert len(report) > 0
    assert "# GreenSpot 분석 리포트" in report
    assert "테스트 공유지" in report
