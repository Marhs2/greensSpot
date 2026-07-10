"""
GreenSpot 전체 기능 통합 테스트.

docs/api.md · 기능명세서 F-01~F-28 · 모든 라우트 커버.
외부 API는 mock. 인증·북마크는 인메모리 SQLite(db_client).

실행:
  python -m pytest tests/test_all_features.py -q
  python -m pytest tests/ -q
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import live_parcel_dict

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _signup_login(client, email: str = "feat@test.com", password: str = "secret12"):
    r = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert r.status_code in (201, 409)
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    data = r.json()
    return data["access_token"], data["refresh_token"]


# =============================================================================
# 1. Health (F-18)
# =============================================================================
class TestFeatureHealth:
    def test_health_ok(self, client):
        r = client.get("/api/gs/health")
        assert r.status_code == 200
        b = r.json()
        assert "status" in b
        assert "database" in b
        assert "stats" in b
        assert "environment" in b
        assert "elapsed_ms" in b

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "docs" in r.json()
        assert r.json()["health"] == "/api/gs/health"


# =============================================================================
# 2. Parcels list / detail (F-01, F-02, F-28)
# =============================================================================
class TestFeatureParcels:
    def test_list_db_mode(self, client):
        with patch("app.api.v1.gs_router.settings") as st, patch(
            "app.api.v1.gs_router.get_all_parcels",
            new=AsyncMock(
                return_value=(
                    [
                        {
                            "id": "DD-001",
                            "name": "시드",
                            "district": "동대문구",
                            "scores": {
                                "treeScore": 60,
                                "gardenScore": 80,
                                "solarScore": 50,
                                "topRecommendation": "GARDEN",
                                "uncertainty": 4,
                            },
                        }
                    ],
                    {
                        "total": 1,
                        "avgTreeScore": 60,
                        "avgGardenScore": 80,
                        "avgSolarScore": 50,
                        "topTreeCount": 0,
                        "topGardenCount": 1,
                        "topSolarCount": 0,
                        "totalAreaSqm": 500,
                    },
                )
            ),
        ):
            st.vworld_api_key = ""
            r = client.get("/api/gs/parcels?live=false")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "database"
        assert len(body["parcels"]) == 1

    def test_list_live_mode(self, client):
        p = live_parcel_dict()
        with patch("app.api.v1.gs_router.settings") as st, patch(
            "app.api.v1.gs_router.live_search",
            new=AsyncMock(
                return_value={
                    "results": [p],
                    "meta": {"source": "vworld_live"},
                    "message": None,
                }
            ),
        ), patch(
            "app.api.v1.gs_router.live_stats_from_results",
            return_value={"total": 1, "avgTreeScore": 70},
        ):
            st.vworld_api_key = "key"
            r = client.get("/api/gs/parcels?district=금천구&live=true&limit=10")
        assert r.status_code == 200
        assert r.json()["source"] == "vworld_live"
        assert r.json()["parcels"][0]["id"].startswith("VW-")

    def test_list_live_discovery_error_400(self, client):
        from app.services.vworld_discovery_service import VWorldDiscoveryError

        with patch("app.api.v1.gs_router.settings") as st, patch(
            "app.api.v1.gs_router.live_search",
            new=AsyncMock(side_effect=VWorldDiscoveryError("bad region")),
        ):
            st.vworld_api_key = "key"
            r = client.get("/api/gs/parcels?district=XXX&live=true")
        assert r.status_code == 400

    def test_detail_db(self, client):
        with patch(
            "app.api.v1.gs_router.get_parcel_detail",
            new=AsyncMock(
                return_value={
                    "parcel": {"id": "DD-001", "name": "시드", "district": "동대문구"},
                    "scores": {"treeScore": 60, "topRecommendation": "GARDEN"},
                    "source": "database",
                }
            ),
        ):
            r = client.get("/api/gs/parcels/DD-001")
        assert r.status_code == 200
        assert r.json()["source"] == "database"

    def test_detail_live_vw(self, client):
        p = live_parcel_dict()
        with patch(
            "app.api.v1.gs_router.live_get_parcel",
            new=AsyncMock(
                return_value={"parcel": p, "scores": p["scores"], "source": "vworld_live"}
            ),
        ):
            r = client.get(f"/api/gs/parcels/{p['id']}")
        assert r.status_code == 200
        assert r.json()["parcel"]["id"].startswith("VW-")

    def test_detail_404(self, client):
        with patch(
            "app.api.v1.gs_router.live_get_parcel",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v1.gs_router.get_parcel_detail",
            new=AsyncMock(return_value=None),
        ):
            r = client.get("/api/gs/parcels/NOPE")
        assert r.status_code == 404


# =============================================================================
# 3. Agent (F-04, F-16, F-17)
# =============================================================================
class TestFeatureAgent:
    def test_agent_search_success(self, client):
        p = live_parcel_dict(tree=72, solar=80, top="SOLAR")
        with patch("app.services.agent_service.settings") as st, patch(
            "app.services.agent_service.live_search",
            new=AsyncMock(
                return_value={
                    "results": [p],
                    "meta": {"preferredUse": "TREE", "strictTopRecommendation": False},
                    "message": None,
                }
            ),
        ), patch(
            "app.services.agent_service.chat",
            new=AsyncMock(side_effect=Exception("no llm")),
        ):
            st.vworld_api_key = "k"
            r = client.post("/api/gs/agent", json={"query": "금천구 수목"})
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 1
        assert body["criteria"]["topRecommendation"] == "TREE"
        assert "summary" in body
        assert "elapsed_ms" in body

    def test_agent_query_too_short(self, client):
        r = client.post("/api/gs/agent", json={"query": "a"})
        assert r.status_code == 422

    def test_agent_empty_region_message(self, client):
        with patch("app.services.agent_service.settings") as st, patch(
            "app.services.agent_service.live_search",
            new=AsyncMock(
                return_value={
                    "results": [],
                    "meta": {},
                    "message": "지역을 입력해 주세요",
                }
            ),
        ), patch(
            "app.services.agent_service.search_parcels_by_criteria",
            new=AsyncMock(return_value=[]),
        ):
            st.vworld_api_key = "k"
            r = client.post("/api/gs/agent", json={"query": "수목 추천해줘"})
        assert r.status_code == 200
        assert r.json()["count"] == 0


# =============================================================================
# 4. Explain (F-05)
# =============================================================================
class TestFeatureExplain:
    def test_explain_success(self, client):
        with patch(
            "app.api.v1.gs_router.explain_parcel",
            new=AsyncMock(
                return_value={
                    "parcelId": "DD-001",
                    "explanation": "## 요약\n테스트",
                    "facts": {"areaSqm": 100},
                    "promptVersion": "v3-greenspot3",
                    "uncertainty": 5,
                }
            ),
        ):
            r = client.post("/api/gs/parcels/DD-001/explain", json={})
        assert r.status_code == 200
        assert "explanation" in r.json()

    def test_explain_404(self, client):
        with patch(
            "app.api.v1.gs_router.explain_parcel",
            new=AsyncMock(return_value=None),
        ):
            r = client.post("/api/gs/parcels/NOPE/explain", json={})
        assert r.status_code == 404


# =============================================================================
# 5. Simulate (F-06)
# =============================================================================
class TestFeatureSimulate:
    def test_plant_trees(self, client):
        with patch(
            "app.api.v1.gs_router.simulate_scenario",
            new=AsyncMock(
                return_value={
                    "parcelId": "DD-001",
                    "parcelName": "시드",
                    "parcelArea": 500,
                    "scenarios": {
                        "PLANT_TREES": {
                            "label": "나무 10그루",
                            "effects": {"carbonKgPerYear": 794},
                        }
                    },
                    "elapsed_ms": 2,
                }
            ),
        ):
            r = client.post(
                "/api/gs/parcels/DD-001/simulate",
                json={"scenarioType": "PLANT_TREES", "quantity": 10},
            )
        assert r.status_code == 200
        assert "PLANT_TREES" in r.json()["scenarios"]

    def test_aliases_tree_garden_solar(self, client):
        for alias, key in [
            ("TREE", "PLANT_TREES"),
            ("GARDEN", "CREATE_GARDEN"),
            ("SOLAR", "INSTALL_SOLAR"),
        ]:
            with patch(
                "app.api.v1.gs_router.simulate_scenario",
                new=AsyncMock(
                    return_value={
                        "parcelId": "DD-001",
                        "parcelName": "x",
                        "parcelArea": 100,
                        "scenarios": {key: {"effects": {}}},
                        "elapsed_ms": 1,
                    }
                ),
            ):
                r = client.post(
                    "/api/gs/parcels/DD-001/simulate",
                    json={"scenario_type": alias, "quantity": 5},
                )
            assert r.status_code == 200, alias

    def test_compare_all(self, client):
        with patch(
            "app.api.v1.gs_router.simulate_compare_all",
            new=AsyncMock(
                return_value={
                    "parcelId": "VW-1",
                    "parcelName": "live",
                    "parcelArea": 1000,
                    "scenarios": {
                        "PLANT_TREES": {"effects": {}},
                        "CREATE_GARDEN": {"effects": {}},
                        "INSTALL_SOLAR": {"effects": {}},
                    },
                    "elapsed_ms": 3,
                }
            ),
        ):
            r = client.post(
                "/api/gs/parcels/VW-1/simulate",
                json={"scenarioType": "COMPARE_ALL", "quantity": 10, "area_sqm": 1000},
            )
        assert r.status_code == 200
        sc = r.json()["scenarios"]
        assert "PLANT_TREES" in sc and "CREATE_GARDEN" in sc and "INSTALL_SOLAR" in sc

    def test_quantity_limit(self, client):
        r = client.post(
            "/api/gs/parcels/DD-001/simulate",
            json={"scenarioType": "PLANT_TREES", "quantity": 999},
        )
        assert r.status_code == 400

    def test_simulate_404(self, client):
        with patch(
            "app.api.v1.gs_router.simulate_scenario",
            new=AsyncMock(return_value=None),
        ):
            r = client.post(
                "/api/gs/parcels/NOPE/simulate",
                json={"scenarioType": "PLANT_TREES", "quantity": 10},
            )
        assert r.status_code == 404


# =============================================================================
# 6. Compare (F-07)
# =============================================================================
class TestFeatureCompare:
    def test_compare_ok(self, client):
        with patch(
            "app.api.v1.gs_router.compare_parcels",
            new=AsyncMock(
                return_value={
                    "comparison": [
                        {"id": "A", "scores": {"tree": 1, "garden": 2, "solar": 3}},
                        {"id": "B", "scores": {"tree": 2, "garden": 1, "solar": 1}},
                    ],
                    "ranking": {
                        "tree": ["B", "A"],
                        "garden": ["A", "B"],
                        "solar": ["A", "B"],
                        "carbon": ["A", "B"],
                        "costEfficiency": ["A", "B"],
                    },
                }
            ),
        ):
            r = client.post("/api/gs/compare", json={"ids": ["A", "B"]})
        assert r.status_code == 200
        assert len(r.json()["comparison"]) == 2

    def test_compare_too_few(self, client):
        r = client.post("/api/gs/compare", json={"ids": ["A"]})
        assert r.status_code in (400, 422)

    def test_compare_invalid_parcels(self, client):
        with patch(
            "app.api.v1.gs_router.compare_parcels",
            new=AsyncMock(return_value=None),
        ):
            r = client.post("/api/gs/compare", json={"ids": ["X", "Y"]})
        assert r.status_code == 400


# =============================================================================
# 7. Report / Export (F-08, F-13)
# =============================================================================
class TestFeatureReportExport:
    def test_report_markdown(self, client):
        with patch(
            "app.api.v1.gs_router.generate_report",
            new=AsyncMock(return_value="# GreenSpot 분석 리포트\n- 테스트"),
        ):
            r = client.post(
                "/api/gs/report",
                json={"parcelId": "DD-001", "format": "markdown"},
            )
        assert r.status_code == 200
        assert "text/markdown" in r.headers.get("content-type", "")
        assert "GreenSpot" in r.text

    def test_report_json(self, client):
        with patch(
            "app.api.v1.gs_router.generate_report",
            new=AsyncMock(return_value='{"parcel":{}}'),
        ):
            r = client.post(
                "/api/gs/report",
                json={"parcelId": "DD-001", "format": "json"},
            )
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_report_404(self, client):
        with patch(
            "app.api.v1.gs_router.generate_report",
            new=AsyncMock(return_value=None),
        ):
            r = client.post(
                "/api/gs/report",
                json={"parcelId": "NOPE", "format": "markdown"},
            )
        assert r.status_code == 404

    def test_export_csv(self, client):
        csv_body = "\ufeffID,부지명\nDD-001,테스트\n"
        with patch(
            "app.api.v1.gs_router.export_csv",
            new=AsyncMock(return_value=csv_body),
        ):
            r = client.get("/api/gs/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "DD-001" in r.text


# =============================================================================
# 8. Stats / Trending / History (F-12, F-16, F-17)
# =============================================================================
class TestFeatureStatsTrendingHistory:
    def test_stats(self, client):
        with patch(
            "app.api.v1.gs_router.get_stats_full",
            new=AsyncMock(
                return_value={
                    "totalParcels": 3,
                    "byDistrict": [],
                    "byType": [],
                    "byRecommendation": {"TREE": 1, "GARDEN": 1, "SOLAR": 1},
                    "generatedAt": datetime.utcnow(),
                }
            ),
        ):
            r = client.get("/api/gs/stats")
        assert r.status_code == 200
        assert r.json()["totalParcels"] == 3

    def test_trending_removed(self, client):
        r = client.get("/api/gs/trending")
        assert r.status_code == 404

    def test_history_removed(self, client):
        r = client.get("/api/gs/history?limit=10")
        assert r.status_code == 404


# =============================================================================
# 9. Auth full flow (F-09, F-10, F-19) — F-20 제거
# =============================================================================
class TestFeatureAuth:
    def test_signup_login_refresh_logout(self, db_client):
        email = "allfeat@example.com"
        password = "secret12"

        r = db_client.post(
            "/api/auth/signup",
            json={"email": email, "password": password},
        )
        assert r.status_code == 201
        assert r.json()["ok"] is True

        r = db_client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert r.status_code == 200
        tokens = r.json()
        access, refresh = tokens["access_token"], tokens["refresh_token"]
        assert tokens.get("user", {}).get("email") == email
        assert access

        r = db_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert r.status_code == 200
        new_refresh = r.json()["refresh_token"]

        r = db_client.post(
            "/api/auth/logout",
            json={"refresh_token": new_refresh},
        )
        assert r.status_code == 200

        # 폐기된 refresh 재사용 실패
        r = db_client.post(
            "/api/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert r.status_code == 401

    def test_signup_duplicate(self, db_client):
        email = "dup@example.com"
        db_client.post("/api/auth/signup", json={"email": email, "password": "secret12"})
        r = db_client.post(
            "/api/auth/signup",
            json={"email": email, "password": "secret12"},
        )
        assert r.status_code == 409

    def test_login_wrong_password(self, db_client):
        email = "wrong@example.com"
        db_client.post("/api/auth/signup", json={"email": email, "password": "secret12"})
        r = db_client.post(
            "/api/auth/login",
            json={"email": email, "password": "bad-password"},
        )
        assert r.status_code == 401

    def test_me_removed(self, db_client):
        r = db_client.get("/api/users/me")
        assert r.status_code == 404

    def test_preferences_removed(self, db_client):
        access, _ = _signup_login(db_client, "pref@example.com")
        r = db_client.patch(
            "/api/users/me/preferences",
            headers=_auth_headers(access),
            json={"theme": "dark"},
        )
        assert r.status_code == 404


# =============================================================================
# 10. Bookmarks + Share (F-11, F-14)
# =============================================================================
class TestFeatureBookmarksShare:
    def test_bookmark_crud_live_snapshot(self, db_client):
        access, _ = _signup_login(db_client, "bm@example.com")
        headers = _auth_headers(access)
        pid = "VW-1117012500100010000"

        r = db_client.post(
            "/api/bookmarks",
            headers=headers,
            json={
                "parcelId": pid,
                "parcelName": "라이브 부지",
                "district": "용산구",
                "topRecommendation": "SOLAR",
                "topScore": 74,
            },
        )
        assert r.status_code == 201

        r = db_client.get("/api/bookmarks", headers=headers)
        assert r.status_code == 200
        marks = r.json()["bookmarks"]
        assert any(b["parcelId"] == pid for b in marks)

        # 중복 409
        r = db_client.post(
            "/api/bookmarks",
            headers=headers,
            json={
                "parcelId": pid,
                "parcelName": "라이브 부지",
                "district": "용산구",
            },
        )
        assert r.status_code == 409

        r = db_client.delete(
            f"/api/bookmarks?parcelId={pid}",
            headers=headers,
        )
        assert r.status_code == 200

        r = db_client.get("/api/bookmarks", headers=headers)
        assert all(b["parcelId"] != pid for b in r.json()["bookmarks"])

    def test_bookmark_requires_auth(self, db_client):
        r = db_client.get("/api/bookmarks")
        assert r.status_code in (401, 403)

    def test_share_vw(self, db_client):
        r = db_client.post(
            "/api/share",
            json={"parcelId": "VW-1117012500100010000"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "shareId" in body
        assert "url" in body
        assert "VW-1117012500100010000" in body["url"] or "share" in body["url"]

    def test_share_unknown_non_vw_404(self, db_client):
        with patch(
            "app.api.v1.auth_router.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            r = db_client.post("/api/share", json={"parcelId": "DD-NOPE"})
        assert r.status_code == 404


# =============================================================================
# 11. Integration — VWorld layers / regulations / enrich (F-03, F-28)
# =============================================================================
class TestFeatureIntegrationVWorld:
    def test_vworld_layers(self, client):
        r = client.get("/api/v1/gs/vworld/layers")
        assert r.status_code == 200
        assert "layers" in r.json()
        assert len(r.json()["layers"]) >= 1

    def test_regulations_lookup_404(self, client):
        with patch(
            "app.api.v1.integration_router.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            r = client.get("/api/v1/gs/parcels/NOPE/regulations")
        assert r.status_code == 404

    def test_regulations_lookup_ok(self, client):
        parcel = MagicMock()
        parcel.id = "DD-001"
        parcel.lat = 37.5
        parcel.lng = 127.0
        with patch(
            "app.api.v1.integration_router.get_parcel_by_id",
            new=AsyncMock(return_value=parcel),
        ), patch(
            "app.api.v1.integration_router.vworld_client"
        ) as vc:
            vc.return_value.get_regulations_at_point = AsyncMock(
                return_value=[{"code": "GREEN_BELT", "name": "개발제한구역"}]
            )
            r = client.get("/api/v1/gs/parcels/DD-001/regulations")
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_regulations_sync_404(self, client):
        with patch(
            "app.api.v1.integration_router.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            r = client.post("/api/v1/gs/parcels/NOPE/regulations/sync")
        assert r.status_code == 404

    def test_enrich_404(self, client):
        with patch(
            "app.api.v1.integration_router.get_parcel_by_id",
            new=AsyncMock(return_value=None),
        ):
            r = client.post("/api/v1/gs/parcels/NOPE/enrich")
        assert r.status_code == 404

    def test_admin_recompute_removed(self, client):
        """관리자 점수 재계산 API 는 제공하지 않는다."""
        r = client.post("/api/v1/gs/admin/scores/recompute")
        assert r.status_code == 404

    def test_enrich_ok(self, client):
        parcel = MagicMock()
        parcel.id = "DD-001"
        parcel.district = "강남구"
        parcel.confidence = 0.9
        parcel.solar_irradiance = 3.0
        parcel.sunlight_hours = 5.0
        with patch(
            "app.api.v1.integration_router.get_parcel_by_id",
            new=AsyncMock(return_value=parcel),
        ), patch(
            "app.api.v1.integration_router.kma_client"
        ) as kc:
            kc.return_value.get_climate_for_district = AsyncMock(
                return_value={
                    "dataAvailable": True,
                    "solarIrradiance": 4.5,
                    "sunlightHours": 6.5,
                }
            )
            r = client.post("/api/v1/gs/parcels/DD-001/enrich")
        assert r.status_code == 200
        assert r.json()["updated"] is True


# =============================================================================
# 12. KOSIS (F-25) — 공개 API 제거
# =============================================================================
class TestFeatureKosis:
    def test_population_removed(self, client):
        r = client.get("/api/v1/gs/kosis/population?district=강남구")
        assert r.status_code == 404

    def test_households_removed(self, client):
        r = client.get("/api/v1/gs/kosis/households?district=금천구")
        assert r.status_code == 404

    def test_district_mapping_still_in_service(self):
        # 내부 라이브 보강용 매핑은 서비스 모듈에 남을 수 있음
        from app.services.kosis_service import DISTRICT_TO_OBJ_L1

        assert len(DISTRICT_TO_OBJ_L1) == 25
        assert "금천구" in DISTRICT_TO_OBJ_L1


# =============================================================================
# 13. Visual Crossing (climate / heat / timeline)
# =============================================================================
class TestFeatureVisualCrossing:
    def test_climate_unconfigured(self, client):
        from app.services.visual_crossing_service import VisualCrossingNotConfigured

        mock_cli = MagicMock()
        mock_cli.get_climate_for_district = AsyncMock(
            side_effect=VisualCrossingNotConfigured("no key")
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_cli,
        ):
            r = client.get(
                "/api/v1/gs/visualcrossing/climate?lat=37.5&lng=127.0"
            )
        assert r.status_code == 400

    def test_climate_success_mocked(self, client):
        mock_cli = MagicMock()
        mock_cli.get_climate_for_district = AsyncMock(
            return_value={
                "source": "visualcrossing",
                "district": None,
                "location": "37.5,127.0",
                "start": "2025-01-01",
                "end": "2025-01-30",
                "solarIrradiance": 4.0,
                "sunlightHours": 6.0,
                "avgTemperature": 10.0,
                "dataAvailable": True,
            }
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_cli,
        ):
            r = client.get(
                "/api/v1/gs/visualcrossing/climate?lat=37.5&lng=127.0&days=30"
            )
        assert r.status_code == 200
        assert r.json()["dataAvailable"] is True

    def test_heat_success_mocked(self, client):
        mock_cli = MagicMock()
        mock_cli.get_heat_estimates = AsyncMock(
            return_value={
                "source": "visualcrossing",
                "district": None,
                "location": "37.5,127.0",
                "period": {"start": "2024-06-01", "end": "2024-08-31"},
                "heatIsland": 2.0,
                "surfaceTempSummer": 32.0,
                "avgTemperature": 27.0,
                "maxTemperature": 33.0,
                "dataAvailable": True,
            }
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_cli,
        ):
            r = client.get(
                "/api/v1/gs/visualcrossing/heat?lat=37.5&lng=127.0"
            )
        assert r.status_code == 200

    def test_heat_coord_validation(self, client):
        r = client.get(
            "/api/v1/gs/visualcrossing/heat?lat=999&lng=127.0"
        )
        assert r.status_code in (400, 422)

    def test_timeline_missing_location(self, client):
        r = client.get("/api/v1/gs/visualcrossing/timeline")
        assert r.status_code == 422

    def test_timeline_success(self, client):
        mock_cli = MagicMock()
        mock_cli.get_timeline = AsyncMock(
            return_value=[{"datetime": "2025-07-01", "temp": 27.0}]
        )
        with patch(
            "app.api.v1.integration_router.visual_crossing_client",
            return_value=mock_cli,
        ):
            r = client.get(
                "/api/v1/gs/visualcrossing/timeline"
                "?location=37.5,127.0&start=2025-07-01&end=2025-07-02"
            )
        assert r.status_code == 200
        body = r.json()
        assert body.get("count", len(body.get("days", []))) >= 1 or body.get("dataAvailable") is not False


# =============================================================================
# 14. VWorld possession / characteristics endpoints
# =============================================================================
class TestFeatureVWorldLand:
    def test_possession_missing_bbox(self, client):
        r = client.get("/api/v1/gs/vworld/possession/1111010100100010000")
        assert r.status_code == 422

    def test_characteristics_unconfigured(self, client):
        with patch("app.core.config.settings.vworld_api_key", ""):
            r = client.get(
                "/api/v1/gs/vworld/characteristics/1111010100100010000"
            )
        assert r.status_code in (200, 400)


# =============================================================================
# 15. Service-level scoring / provenance (F-03, F-27)
# =============================================================================
class TestFeatureScoringProvenance:
    def test_regulation_all_zero(self):
        from app.services.vworld_service import apply_regulation_penalties

        out = apply_regulation_penalties(
            {"sumokScore": 80, "gardenScore": 70, "solarScore": 90},
            [{"affectedUses": ["all"], "penaltyType": "zero", "regulationType": "GREEN_BELT"}],
        )
        assert out["sumokScore"] == out["gardenScore"] == out["solarScore"] == 0.0

    def test_compute_base_scores_bounds(self):
        from app.services.vworld_discovery_service import compute_base_scores

        s = compute_base_scores(
            1000.0,
            "VACANT_LOT",
            {
                "solar_irradiance": 4.0,
                "heat_island": 2.0,
                "soil_type": "LOAM",
                "road_adjacent": True,
                "air_quality": 20,
            },
            actual_flags={"soil_actual": True, "solar_actual": True},
        )
        assert 18 <= s["tree_score"] <= 92
        assert 18 <= s["garden_score"] <= 92
        assert 18 <= s["solar_score"] <= 92
        assert s["top_recommendation"] in ("TREE", "GARDEN", "SOLAR")

    def test_simulation_aliases(self):
        from app.services.simulation_service import normalize_scenario_type

        assert normalize_scenario_type("SUMOK") == "PLANT_TREES"
        assert normalize_scenario_type("TREE") == "PLANT_TREES"


# =============================================================================
# 16. F-16/F-17 제거 — trending/history 미제공
# =============================================================================
class TestFeatureDualPrefix:
    def test_trending_and_history_removed(self, client):
        assert client.get("/api/gs/trending").status_code == 404
        assert client.get("/api/gs/history").status_code == 404
