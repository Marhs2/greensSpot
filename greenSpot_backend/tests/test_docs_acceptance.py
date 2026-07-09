"""
docs/ 기반 수용 테스트 (Acceptance).

참조:
- docs/README.md — 핵심 개념
- docs/api.md — REST 계약
- docs/기능명세서.MD — F-01~F-28 수용 기준
- docs/sql.md — Bookmark/Share Parcel FK 없음

외부 API 실호출 없이 mock 으로 동작한다.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def client():
    with patch("main.init_db"):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Fixtures: live parcel shapes (docs: VW-{pnu})
# ---------------------------------------------------------------------------
def _live_parcel(
    pid: str = "VW-1154510100100010000",
    *,
    tree: float = 70,
    garden: float = 65,
    solar: float = 80,
    top: str = "SOLAR",
    district: str = "금천구",
    area: float = 1200,
) -> Dict[str, Any]:
    return {
        "id": pid,
        "name": f"{district} 테스트 부지",
        "district": district,
        "neighborhood": "가산동",
        "lat": 37.48,
        "lng": 126.89,
        "areaSqm": area,
        "parcelType": "UNUSED_LAND",
        "ownership": "PUBLIC",
        "soilType": "LOAM",
        "solarIrradiance": 4.2,
        "sunlightHours": 6.0,
        "heatIsland": 2.1,
        "surfaceTempSummer": 34.0,
        "airQuality": 22,
        "nearbyHouseholds": None,
        "pedestrianFlow": None,
        "roadAdjacent": True,
        "waterAccess": False,
        "electricityAccess": True,
        "nearbySchools": None,
        "nearbyHospitals": None,
        "nearbyParks": None,
        "nearbySubwayStations": None,
        "regulatoryRestriction": "",
        "regulations": [],
        "sumokFeasibility": {
            "status": "AVAILABLE",
            "score": tree,
            "reason": "제한 없음",
            "blockingRegulations": [],
            "warningRegulations": [],
            "requiredChecks": [],
            "confidence": 0.9,
        },
        "confidence": 0.9,
        "dataSource": "VWorld Live",
        "dataProvenance": {
            "boundary": {"source": "VWorld", "actual": True},
            "soilType": {"source": "농촌진흥청", "actual": True},
            "pedestrianFlow": {"source": "GreenSpot", "actual": False},
        },
        "scores": {
            "treeScore": tree,
            "gardenScore": garden,
            "solarScore": solar,
            "topRecommendation": top,
            "uncertainty": 5,
        },
    }


# =============================================================================
# F-18 / api.md Health
# =============================================================================
class TestDocHealth:
    def test_health_returns_status_and_env_flags(self, client):
        r = client.get("/api/gs/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] in ("healthy", "unhealthy")
        env = body["environment"]
        for key in (
            "vworldApiKeyConfigured",
            "kosisApiKeyConfigured",
            "visualCrossingApiKeyConfigured",
        ):
            assert key in env
            assert isinstance(env[key], bool)


# =============================================================================
# F-03 / docs — 규제 affectedUses "all" 페널티 (그린벨트 등)
# =============================================================================
class TestDocRegulationPenalties:
    def test_affected_uses_all_zeros_all_scores(self):
        """기능명세 F-03: affectedUses=all 은 전 용도에 페널티."""
        from app.services.vworld_service import apply_regulation_penalties

        applied = apply_regulation_penalties(
            {"sumokScore": 80, "gardenScore": 70, "solarScore": 90},
            [
                {
                    "regulationType": "GREEN_BELT",
                    "affectedUses": ["all"],
                    "penaltyType": "zero",
                    "penaltyValue": 0,
                }
            ],
        )
        assert applied["sumokScore"] == 0.0
        assert applied["gardenScore"] == 0.0
        assert applied["solarScore"] == 0.0
        assert len(applied["penalties"]) == 3

    def test_affected_uses_sumok_only(self):
        from app.services.vworld_service import apply_regulation_penalties

        applied = apply_regulation_penalties(
            {"sumokScore": 80, "gardenScore": 70, "solarScore": 90},
            [
                {
                    "regulationType": "URBAN_NATURE_PARK",
                    "affectedUses": ["sumok"],
                    "penaltyType": "multiplier",
                    "penaltyValue": 0.5,
                }
            ],
        )
        assert applied["sumokScore"] == 40.0
        assert applied["gardenScore"] == 70.0
        assert applied["solarScore"] == 90.0


# =============================================================================
# F-27 / docs — dataProvenance actual 규칙
# =============================================================================
class TestDocDataProvenance:
    def test_build_data_provenance_flags_actual_only_when_true(self):
        from app.services.vworld_discovery_service import build_data_provenance

        prov = build_data_provenance(
            "VWorld",
            soil_type_actual=True,
            ownership_actual=False,
            air_quality_actual=True,
            solar_actual=False,
            heat_actual=True,
            regulations=[{"code": "GREEN_BELT"}],
            households_actual=False,
            road_adjacent_actual=True,
            parcel_type_actual=True,
            area_actual=True,
        )
        assert prov["soilType"]["actual"] is True
        assert prov["ownership"]["actual"] is False
        assert prov["airQuality"]["actual"] is True
        assert prov["solarIrradiance"]["actual"] is False
        # 월별 일사는 모델 — 항상 false
        assert prov["monthlyIrradiance"]["actual"] is False
        assert prov["waterAccess"]["actual"] is False
        assert prov["electricityAccess"]["actual"] is False

    def test_live_parcel_social_metrics_are_null_not_fake_zero(self):
        """docs: 미연동 사회지표는 null (가짜 0 금지)."""
        p = _live_parcel()
        assert p["pedestrianFlow"] is None
        assert p["nearbySchools"] is None
        assert p["nearbySubwayStations"] is None


# =============================================================================
# F-04 / docs — Agent soft-sort (topRecommendation = 정렬 키)
# =============================================================================
class TestDocAgentSoftSort:
    def test_extract_criteria_tree_keyword(self):
        from app.services.agent_service import _extract_criteria_from_query

        c = _extract_criteria_from_query("금천구 수목")
        assert c.get("district") == "금천구" or c.get("region") == "금천구"
        assert c.get("topRecommendation") == "TREE"
        assert c.get("live") is True

    def test_extract_criteria_garden_and_solar(self):
        from app.services.agent_service import _extract_criteria_from_query

        assert _extract_criteria_from_query("용산구 텃밭")["topRecommendation"] == "GARDEN"
        assert _extract_criteria_from_query("강남구 태양광")["topRecommendation"] == "SOLAR"

    def test_score_for_use_prefers_tree_when_requested(self):
        from app.services.agent_service import _score_for_use_parcel

        p = {
            "scores": {
                "treeScore": 71,
                "gardenScore": 60,
                "solarScore": 85,
                "topRecommendation": "SOLAR",
            }
        }
        # 1위가 SOLAR여도 TREE 요청 시 treeScore
        assert _score_for_use_parcel(p, "TREE") == 71.0
        assert _score_for_use_parcel(p, "SOLAR") == 85.0

    def test_db_fallback_does_not_hard_filter_top_recommendation(self):
        """strictTopRecommendation 없으면 1위 불일치 필지도 유지."""
        from app.services.agent_service import search_parcels_by_criteria

        rows = [
            {
                "id": "A",
                "district": "금천구",
                "scores": {
                    "treeScore": 75,
                    "gardenScore": 50,
                    "solarScore": 90,
                    "topRecommendation": "SOLAR",
                },
            },
            {
                "id": "B",
                "district": "금천구",
                "scores": {
                    "treeScore": 60,
                    "gardenScore": 55,
                    "solarScore": 40,
                    "topRecommendation": "TREE",
                },
            },
        ]
        db = AsyncMock()
        with patch(
            "app.services.agent_service.settings"
        ) as st, patch(
            "app.services.agent_service.get_all_parcels",
            new=AsyncMock(return_value=(rows, {})),
        ):
            st.vworld_api_key = ""
            result = _run(
                search_parcels_by_criteria(
                    db,
                    {
                        "district": "금천구",
                        "topRecommendation": "TREE",
                        "limit": 10,
                    },
                )
            )
        assert len(result) == 2
        # treeScore 내림차순: A(75) 먼저
        assert result[0]["id"] == "A"
        assert result[0]["scores"]["topRecommendation"] == "SOLAR"

    def test_strict_top_recommendation_hard_filters(self):
        from app.services.agent_service import search_parcels_by_criteria

        rows = [
            {
                "id": "A",
                "district": "금천구",
                "scores": {
                    "treeScore": 75,
                    "gardenScore": 50,
                    "solarScore": 90,
                    "topRecommendation": "SOLAR",
                },
            },
            {
                "id": "B",
                "district": "금천구",
                "scores": {
                    "treeScore": 60,
                    "gardenScore": 55,
                    "solarScore": 40,
                    "topRecommendation": "TREE",
                },
            },
        ]
        db = AsyncMock()
        with patch(
            "app.services.agent_service.settings"
        ) as st, patch(
            "app.services.agent_service.get_all_parcels",
            new=AsyncMock(return_value=(rows, {})),
        ):
            st.vworld_api_key = ""
            result = _run(
                search_parcels_by_criteria(
                    db,
                    {
                        "district": "금천구",
                        "topRecommendation": "TREE",
                        "strictTopRecommendation": True,
                        "limit": 10,
                    },
                )
            )
        assert len(result) == 1
        assert result[0]["id"] == "B"

    def test_agent_endpoint_returns_results_shape(self, client):
        live_payload = {
            "results": [_live_parcel(tree=72, solar=80, top="SOLAR")],
            "meta": {
                "source": "vworld_live",
                "preferredUse": "TREE",
                "strictTopRecommendation": False,
            },
            "message": None,
        }
        with patch("app.services.agent_service.settings") as st, patch(
            "app.services.agent_service.live_search",
            new=AsyncMock(return_value=live_payload),
        ), patch(
            "app.services.agent_service.chat",
            new=AsyncMock(side_effect=Exception("no llm")),
        ):
            st.vworld_api_key = "test-key"
            r = client.post("/api/gs/agent", json={"query": "금천구 수목"})
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 1
        assert body["results"][0]["id"].startswith("VW-")
        assert "criteria" in body
        assert body["criteria"].get("topRecommendation") == "TREE"


# =============================================================================
# F-06 / api.md — 라이브 시뮬레이션
# =============================================================================
class TestDocLiveSimulate:
    def test_normalize_scenario_aliases(self):
        from app.services.simulation_service import normalize_scenario_type

        assert normalize_scenario_type("TREE") == "PLANT_TREES"
        assert normalize_scenario_type("SUMOK") == "PLANT_TREES"
        assert normalize_scenario_type("GARDEN") == "CREATE_GARDEN"
        assert normalize_scenario_type("SOLAR") == "INSTALL_SOLAR"
        assert normalize_scenario_type("COMPARE_ALL") == "COMPARE_ALL"

    def test_simulate_live_with_area_hint_no_db(self):
        from app.services.simulation_service import simulate_scenario

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        with patch(
            "app.services.simulation_service.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.services.simulation_service.live_get_parcel",
            new=AsyncMock(return_value=None),
        ):
            result = _run(
                simulate_scenario(
                    db,
                    "VW-1117012500100010000",
                    "PLANT_TREES",
                    10,
                    area_sqm_hint=2000,
                    name_hint="힌트 부지",
                )
            )
        assert result is not None
        assert result["parcelId"] == "VW-1117012500100010000"
        assert "PLANT_TREES" in result["scenarios"]
        # 라이브는 scenarios 테이블 저장 안 함
        db.add.assert_not_called()

    def test_simulate_endpoint_quantity_limit(self, client):
        r = client.post(
            "/api/gs/parcels/DD-001/simulate",
            json={"scenarioType": "PLANT_TREES", "quantity": 9999},
        )
        assert r.status_code == 400
        assert "수량" in r.json()["detail"] or "초과" in str(r.json())

    def test_simulate_endpoint_live_id_with_hint(self, client):
        payload = {
            "parcelId": "VW-1117012500100010000",
            "parcelName": "테스트",
            "parcelArea": 1000.0,
            "scenarios": {
                "PLANT_TREES": {
                    "label": "나무 10그루",
                    "effects": {"carbonKgPerYear": 794},
                }
            },
            "elapsed_ms": 1,
        }
        with patch(
            "app.api.v1.gs_router.simulate_scenario",
            new=AsyncMock(return_value=payload),
        ):
            r = client.post(
                "/api/gs/parcels/VW-1117012500100010000/simulate",
                json={
                    "scenario_type": "PLANT_TREES",
                    "quantity": 10,
                    "area_sqm": 1000,
                },
            )
        assert r.status_code == 200
        assert r.json()["parcelId"] == "VW-1117012500100010000"


# =============================================================================
# F-07 / docs — 비교 (DB + VW 혼합)
# =============================================================================
class TestDocCompare:
    def test_compare_requires_two_ids(self, client):
        r = client.post("/api/gs/compare", json={"ids": ["only-one"]})
        # pydantic min_length=2 → 422, 또는 라우터 400
        assert r.status_code in (400, 422)

    def test_compare_mix_db_and_live(self):
        from app.services.parcel_service import compare_parcels

        db_parcel = MagicMock()
        db_parcel.id = "DD-001"
        db_parcel.name = "시드"
        db_parcel.district = "동대문구"
        db_parcel.area_sqm = 500
        score = MagicMock()
        score.tree_score = 60
        score.garden_score = 70
        score.solar_score = 50
        score.top_recommendation = "GARDEN"
        db_parcel.scores = score

        live = {
            "parcel": _live_parcel("VW-1117012500100010000", district="용산구"),
            "scores": {
                "treeScore": 68,
                "gardenScore": 71,
                "solarScore": 74,
                "topRecommendation": "SOLAR",
            },
        }

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.unique.return_value.all.return_value = [db_parcel]
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.services.live_search_service.live_get_parcel",
            new=AsyncMock(return_value=live),
        ), patch(
            "app.services.simulation_service.simulate_scenario",
            new=AsyncMock(
                return_value={
                    "scenarios": {
                        "PLANT_TREES": {
                            "effects": {
                                "carbonKgPerYear": 100,
                                "costPerCarbonKgWon": 2000,
                            }
                        }
                    }
                }
            ),
        ):
            out = _run(compare_parcels(db, ["DD-001", "VW-1117012500100010000"]))

        assert out is not None
        assert len(out["comparison"]) == 2
        assert "ranking" in out
        assert set(out["ranking"].keys()) >= {"tree", "garden", "solar", "carbon", "costEfficiency"}


# =============================================================================
# F-11 / sql.md — 북마크 VW-* (Parcel FK 없음)
# =============================================================================
class TestDocBookmarksLive:
    def test_bookmark_create_request_accepts_snapshot_fields(self):
        from app.schemas.schemas import BookmarkCreateRequest

        req = BookmarkCreateRequest(
            parcelId="VW-1117012500100010000",
            parcelName="한강로 부지",
            district="용산구",
            topRecommendation="SOLAR",
            topScore=74,
        )
        assert req.parcelId.startswith("VW-")
        assert req.district == "용산구"

    def test_bookmark_model_has_no_parcel_fk(self):
        """docs/sql.md: bookmarks.parcel_id 에 Parcel FK 없음."""
        from app.models.models import Bookmark
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Bookmark)
        fk_tables = {
            fk.column.table.name
            for col in mapper.columns
            for fk in col.foreign_keys
        }
        assert "parcels" not in fk_tables
        assert "users" in fk_tables


# =============================================================================
# F-14 / docs — Share VW-*
# =============================================================================
class TestDocShare:
    def test_share_model_no_parcel_fk(self):
        from app.models.models import Share
        from sqlalchemy import inspect as sa_inspect

        mapper = sa_inspect(Share)
        fk_tables = {
            fk.column.table.name
            for col in mapper.columns
            for fk in col.foreign_keys
        }
        assert "parcels" not in fk_tables


# =============================================================================
# F-25 / KOSIS 25구
# =============================================================================
class TestDocKosis25Districts:
    def test_twenty_five_seoul_districts_mapped(self):
        from app.services.kosis_service import DISTRICT_TO_OBJ_L1

        assert len(DISTRICT_TO_OBJ_L1) == 25
        for d in ("금천구", "용산구", "서초구", "강남구", "종로구"):
            assert d in DISTRICT_TO_OBJ_L1

    def test_kosis_endpoint_rejects_non_seoul_region(self, client):
        r = client.get("/api/v1/gs/kosis/population?district=해운대구")
        assert r.status_code == 400


# =============================================================================
# F-01 / F-02 — parcels list & detail contracts
# =============================================================================
class TestDocParcelsApi:
    def test_list_parcels_db_fallback_shape(self, client):
        with patch(
            "app.api.v1.gs_router.settings"
        ) as st, patch(
            "app.api.v1.gs_router.get_all_parcels",
            new=AsyncMock(
                return_value=(
                    [
                        {
                            "id": "DD-001",
                            "name": "테스트",
                            "district": "동대문구",
                            "scores": {
                                "treeScore": 60,
                                "gardenScore": 70,
                                "solarScore": 50,
                                "topRecommendation": "GARDEN",
                                "uncertainty": 4,
                            },
                        }
                    ],
                    {"total": 1},
                )
            ),
        ):
            st.vworld_api_key = ""
            r = client.get("/api/gs/parcels?live=false")
        assert r.status_code == 200
        body = r.json()
        assert "parcels" in body
        assert body["source"] == "database"

    def test_get_parcel_live_prefix(self, client):
        detail = {
            "parcel": _live_parcel(),
            "scores": _live_parcel()["scores"],
            "source": "vworld_live",
        }
        with patch(
            "app.api.v1.gs_router.live_get_parcel",
            new=AsyncMock(return_value=detail),
        ):
            r = client.get("/api/gs/parcels/VW-1154510100100010000")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] in ("vworld_live", "vworld_live_cache")
        assert body["parcel"]["id"].startswith("VW-")

    def test_get_parcel_404(self, client):
        with patch(
            "app.api.v1.gs_router.live_get_parcel",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v1.gs_router.get_parcel_detail",
            new=AsyncMock(return_value=None),
        ):
            r = client.get("/api/gs/parcels/DOES-NOT-EXIST")
        assert r.status_code == 404


# =============================================================================
# F-12 / stats — DB 시드 집계
# =============================================================================
class TestDocStats:
    def test_stats_endpoint_keys(self, client):
        with patch(
            "app.api.v1.gs_router.get_stats_full",
            new=AsyncMock(
                return_value={
                    "totalParcels": 0,
                    "byDistrict": [],
                    "byType": [],
                    "byRecommendation": {"TREE": 0, "GARDEN": 0, "SOLAR": 0},
                    "generatedAt": "2026-07-09T00:00:00",
                }
            ),
        ):
            r = client.get("/api/gs/stats")
        assert r.status_code == 200
        body = r.json()
        assert "byRecommendation" in body or "totalParcels" in body


# =============================================================================
# live_search soft-sort meta (F-28)
# =============================================================================
class TestDocLiveSearchMeta:
    def test_score_for_use_soft_sort_key(self):
        from app.services.live_search_service import _score_for_use

        p = {
            "scores": {
                "treeScore": 71,
                "gardenScore": 60,
                "solarScore": 85,
                "topRecommendation": "SOLAR",
            }
        }
        assert _score_for_use(p, "TREE") == 71.0
        assert _score_for_use(p, None) == 85.0  # top rec SOLAR

    def test_live_stats_from_results(self):
        from app.services.live_search_service import live_stats_from_results

        results = [
            _live_parcel("VW-1", tree=70, garden=60, solar=80, top="SOLAR"),
            _live_parcel("VW-2", tree=75, garden=90, solar=50, top="GARDEN"),
        ]
        # scores nested under parcel
        for r in results:
            pass
        stats = live_stats_from_results(results)
        assert stats["total"] == 2
        assert "avgTreeScore" in stats or "topTreeCount" in stats


# =============================================================================
# Report (api.md) — live resolve
# =============================================================================
class TestDocReport:
    def test_report_markdown_for_live_resolved(self):
        from app.services.report_service import generate_report

        detail = {
            "parcel": _live_parcel(),
            "scores": _live_parcel()["scores"],
            "source": "vworld_live",
        }
        db = MagicMock()
        with patch(
            "app.services.report_service.get_parcel_detail_resolved",
            new=AsyncMock(return_value=detail),
        ), patch(
            "app.services.report_service.simulate_compare_all",
            new=AsyncMock(
                return_value={
                    "scenarios": {
                        "PLANT_TREES": {
                            "effects": {
                                "carbonKgPerYear": 794,
                                "costEstimateWon": 2_000_000,
                            }
                        }
                    }
                }
            ),
        ):
            md = _run(generate_report(db, "VW-1154510100100010000", "markdown"))
        assert md is not None
        assert "# GreenSpot 분석 리포트" in md
        assert "수목 식재" in md
        assert "794" in md or "CO" in md


# =============================================================================
# Scenario table FK note (sql.md) — live does not insert
# =============================================================================
class TestDocScenarioLiveNoPersist:
    def test_live_parcel_flag(self):
        from app.services.simulation_service import _LiveParcelArea, _is_live_parcel

        live = _LiveParcelArea("VW-1", 1000, "x")
        assert _is_live_parcel(live) is True


# =============================================================================
# Auth contract (api.md)
# =============================================================================
class TestDocAuthContract:
    def test_signup_validation_short_password(self, client):
        r = client.post(
            "/api/auth/signup",
            json={"email": "a@b.com", "password": "123"},
        )
        # pydantic min_length=6 → 422
        assert r.status_code == 422

    def test_bookmarks_require_auth(self, client):
        r = client.get("/api/bookmarks")
        assert r.status_code in (401, 403)
