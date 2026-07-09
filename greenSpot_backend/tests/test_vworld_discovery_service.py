"""Tests for VWorld discovery service."""
from __future__ import annotations

import asyncio
from unittest.mock import patch, AsyncMock

from app.services.vworld_discovery_service import build_parcel_from_feature


def _run(coro):
    return asyncio.run(coro)


def test_build_parcel_from_feature_dedupes_regulations_by_code():
    """Duplicate regulation codes should be collapsed, keeping the first occurrence."""
    feature = {
        "properties": {
            "pnu": "2635010100108000000",
            "addr": "서울특별시 용산구 이태원동 347-2",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [126.99, 37.53],
                    [126.991, 37.53],
                    [126.991, 37.531],
                    [126.99, 37.531],
                    [126.99, 37.53],
                ]
            ],
        },
    }

    duplicate_regulations = [
        {
            "regulationType": "URBAN_ZONE",
            "regulationName": "Urban zone A",
            "severity": "warning",
        },
        {
            "regulationType": "URBAN_ZONE",
            "regulationName": "Urban zone B",
            "severity": "restricted",
        },
        {
            "regulationType": "PARK",
            "regulationName": "Park",
            "severity": "info",
        },
        {
            "regulationType": "URBAN_ZONE",
            "regulationName": "Urban zone C",
            "severity": "prohibited",
        },
    ]

    with patch("app.services.vworld_discovery_service.vworld_client") as mock_client:
        mock_client.return_value.get_regulations_at_point = AsyncMock(
            return_value=duplicate_regulations
        )
        parcel = _run(build_parcel_from_feature(feature))

    assert parcel is not None
    codes = [r["code"] for r in parcel["regulations"]]
    assert codes == ["URBAN_ZONE", "PARK"]
    # First occurrence should be kept.
    assert parcel["regulations"][0]["name"] == "Urban zone A"
    assert parcel["regulations"][0]["severity"] == "warning"


def test_build_parcel_accepts_seoul_gu_district():
    """Addresses ending in '구' should produce a parcel."""
    feature = {
        "properties": {
            "pnu": "2635010100108000002",
            "addr": "서울특별시 용산구 이태원동 347-2",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [126.99, 37.53],
                    [126.991, 37.53],
                    [126.991, 37.531],
                    [126.99, 37.531],
                    [126.99, 37.53],
                ]
            ],
        },
    }

    with patch("app.services.vworld_discovery_service.vworld_client") as mock_client:
        mock_client.return_value.get_regulations_at_point = AsyncMock(return_value=[])
        parcel = _run(build_parcel_from_feature(feature))

    assert parcel is not None
    assert parcel["district"] == "용산구"


def test_build_parcel_accepts_si_district():
    """Addresses ending in '시' (e.g. 제주시) should also produce a parcel."""
    feature = {
        "properties": {
            "pnu": "5011010100100010000",
            "addr": "제주특별자치도 제주시 이도일동 123",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [126.52, 33.50],
                    [126.521, 33.50],
                    [126.521, 33.501],
                    [126.52, 33.501],
                    [126.52, 33.50],
                ]
            ],
        },
    }

    with patch("app.services.vworld_discovery_service.vworld_client") as mock_client:
        mock_client.return_value.get_regulations_at_point = AsyncMock(return_value=[])
        parcel = _run(build_parcel_from_feature(feature))

    assert parcel is not None
    assert parcel["district"] == "제주시"


def test_build_parcel_rejects_invalid_district():
    """An address with no '구' or '시' district should be rejected."""
    feature = {
        "properties": {
            "pnu": "1111111111111111111",
            "addr": "서울특별시",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [126.99, 37.53],
                    [126.991, 37.53],
                    [126.991, 37.531],
                    [126.99, 37.531],
                    [126.99, 37.53],
                ]
            ],
        },
    }

    with patch("app.services.vworld_discovery_service.vworld_client") as mock_client:
        mock_client.return_value.get_regulations_at_point = AsyncMock(return_value=[])
        parcel = _run(build_parcel_from_feature(feature))

    assert parcel is None


def test_build_parcel_from_feature_keeps_unique_regulations():
    """When all regulation codes are unique, none are removed."""
    feature = {
        "properties": {
            "pnu": "2635010100108000001",
            "addr": "서울특별시 용산구 이태원동 347-3",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [126.99, 37.53],
                    [126.991, 37.53],
                    [126.991, 37.531],
                    [126.99, 37.531],
                    [126.99, 37.53],
                ]
            ],
        },
    }

    unique_regulations = [
        {"regulationType": "A", "regulationName": "A", "severity": "info"},
        {"regulationType": "B", "regulationName": "B", "severity": "info"},
    ]

    with patch("app.services.vworld_discovery_service.vworld_client") as mock_client:
        mock_client.return_value.get_regulations_at_point = AsyncMock(
            return_value=unique_regulations
        )
        parcel = _run(build_parcel_from_feature(feature))

    assert parcel is not None
    assert len(parcel["regulations"]) == 2
