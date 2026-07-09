"""simulation_service 단위 테스트."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.simulation_service import (
    _LiveParcelArea,
    _resolve_parcel_for_sim,
    simulate_scenario,
)
from app.services.vworld_discovery_service import VWorldDiscoveryError


def _run(coro):
    """asyncio.run 의 얇은 래퍼."""
    return asyncio.run(coro)


@pytest.fixture
def db():
    """AsyncSession mock with synchronous add and async commit."""
    mock = AsyncMock()
    mock.add = MagicMock(return_value=None)
    mock.commit = AsyncMock(return_value=None)
    return mock


class TestResolveParcelForSim:
    def test_returns_db_parcel_when_found(self, db):
        parcel = object()
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=parcel),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(return_value=None),
            ):
                result = _run(_resolve_parcel_for_sim(db, "PNU-123"))
        assert result is parcel

    def test_returns_live_parcel_area_with_name(self, db):
        live = {"parcel": {"name": "live parcel", "areaSqm": 1234.5}}
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(return_value=live),
            ):
                result = _run(_resolve_parcel_for_sim(db, "PNU-123"))
        assert isinstance(result, _LiveParcelArea)
        assert result.id == "PNU-123"
        assert result.name == "live parcel"
        assert result.area_sqm == 1234.5

    def test_returns_none_when_parcel_not_found(self, db):
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(return_value=None),
            ):
                result = _run(_resolve_parcel_for_sim(db, "PNU-123"))
        assert result is None

    def test_returns_none_when_live_get_parcel_raises(self, db):
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(side_effect=VWorldDiscoveryError("VWorld failure")),
            ):
                result = _run(_resolve_parcel_for_sim(db, "PNU-123"))
        assert result is None


class TestSimulateScenarioLiveParcel:
    """Live parcels do not have the full Parcel model but must expose `.name`."""

    def _mock_live(self, name: str, area_sqm: float):
        return {
            "parcel": {
                "name": name,
                "areaSqm": area_sqm,
            }
        }

    @pytest.mark.parametrize(
        "scenario_type, quantity",
        [
            ("PLANT_TREES", 10),
            ("CREATE_GARDEN", 5),
            ("INSTALL_SOLAR", 8),
        ],
    )
    def test_live_parcel_simulation_does_not_crash(self, db, scenario_type, quantity):
        live = self._mock_live("unused playground", 1000.0)
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(return_value=live),
            ):
                result = _run(simulate_scenario(db, "PNU-LIVE", scenario_type, quantity))

        assert result is not None
        assert result["parcelName"] == "unused playground"
        assert result["parcelArea"] == 1000.0
        assert result["parcelId"] == "PNU-LIVE"
        assert scenario_type in result["scenarios"]
        # 라이브 필지는 DB FK 가 없어 시나리오 행을 저장하지 않는다
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_live_parcel_without_name_defaults_to_empty_string(self, db):
        live = {"parcel": {"areaSqm": 500.0}}
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.simulation_service.live_get_parcel",
                new=AsyncMock(return_value=live),
            ):
                result = _run(simulate_scenario(db, "PNU-NONAME", "PLANT_TREES", 1))

        assert result is not None
        assert result["parcelName"] == ""
