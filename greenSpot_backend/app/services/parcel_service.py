from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from app.models.models import Parcel, ParcelScore
from app.db.database import Base
from app.services.vworld_discovery_service import build_data_provenance, normalize_soil_type_for_api
from app.services.ttl_cache import cache_get, cache_set
import json

logger = logging.getLogger(__name__)

DEFAULT_DB_DATA_SOURCE = "VWorld/LP_PA_CBND_BUBUN"


async def _enrich_soil_from_location(
    lat: float,
    lng: float,
    *,
    existing_soil: str = "UNKNOWN",
) -> Dict[str, Any]:
    """좌표 → VWorld PNU → 흙토람 토양 실조회.

    Returns:
        {
          soilType, soilTypeLabel, soilDetail, pnu,
          soil_type_actual, source
        }
    """
    from app.core.config import settings
    from app.services.soil_service import client as soil_client
    from app.services.vworld_service import VWorldClient

    result: Dict[str, Any] = {
        "soilType": normalize_soil_type_for_api(existing_soil),
        "soilTypeLabel": None,
        "soilDetail": None,
        "pnu": None,
        "soil_type_actual": False,
        "source": "흙토람 (농진청)",
    }

    if not settings.soil_api_key:
        result["source"] = "흙토람 (농진청, 미연동)"
        return result

    cache_key = f"soil:latlng:{round(lat, 5)}:{round(lng, 5)}"
    cached = cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    pnu: Optional[str] = None
    try:
        if settings.vworld_api_key:
            pnu = await VWorldClient().resolve_pnu_at_point(lat, lng)
    except Exception as exc:  # noqa: BLE001
        logger.info("PNU resolve failed lat=%s lng=%s: %s", lat, lng, exc)

    if not pnu:
        cache_set(cache_key, result, 600.0)
        return result

    result["pnu"] = pnu
    try:
        soil = await soil_client().get_soil_type(pnu, fallback="UNKNOWN")
    except Exception as exc:  # noqa: BLE001
        logger.warning("soil enrich failed pnu=%s: %s", pnu, exc)
        cache_set(cache_key, result, 300.0)
        return result

    if soil.get("dataAvailable") and soil.get("soilType"):
        mapped = normalize_soil_type_for_api(str(soil["soilType"]))
        if mapped != "UNKNOWN":
            result["soilType"] = mapped
            result["soilTypeLabel"] = soil.get("soilTypeLabel")
            result["soilDetail"] = soil.get("soilDetail")
            result["soil_type_actual"] = True
            result["source"] = soil.get("source") or "흙토람 (농진청)"
    else:
        # 조회는 했으나 토양도 미제공(도심 등)
        result["soilDetail"] = soil.get("soilDetail")
        result["source"] = soil.get("source") or "흙토람 (농진청)"

    cache_set(cache_key, result, 1800.0 if result["soil_type_actual"] else 600.0)
    return result


async def get_all_parcels(
    db: AsyncSession,
    district: Optional[str] = None,
    parcel_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 5000,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    query = select(Parcel).options(selectinload(Parcel.scores)).outerjoin(ParcelScore)

    if district:
        query = query.where(Parcel.district == district)
    if parcel_type:
        query = query.where(Parcel.parcel_type == parcel_type)

    result = await db.execute(query.offset(skip).limit(limit))
    parcels = result.scalars().unique().all()

    parcel_list = []
    for p in parcels:
        score = p.scores
        parcel_dict = {
            "id": p.id,
            "name": p.name,
            "district": p.district,
            "neighborhood": p.neighborhood,
            "lat": p.lat,
            "lng": p.lng,
            "areaSqm": p.area_sqm,
            "parcelType": p.parcel_type,
            "ownership": p.ownership,
            "soilType": p.soil_type,
            "solarIrradiance": p.solar_irradiance,
            "monthlyIrradiance": p.monthly_irradiance,
            "sunlightHours": p.sunlight_hours,
            "heatIsland": p.heat_island,
            "surfaceTempSummer": p.surface_temp_summer,
            "airQuality": p.air_quality,
            "nearbyHouseholds": p.nearby_households,
            "pedestrianFlow": p.pedestrian_flow,
            "roadAdjacent": p.road_adjacent,
            "waterAccess": p.water_access,
            "electricityAccess": p.electricity_access,
            "nearbySchools": p.nearby_schools,
            "nearbyHospitals": p.nearby_hospitals,
            "nearbyParks": p.nearby_parks,
            "nearbySubwayStations": p.nearby_subway_stations,
            "regulatoryRestriction": p.regulatory_restriction,
            "regulations": p.regulations or [],
            "sumokFeasibility": p.sumok_feasibility,
            "confidence": p.confidence,
            "dataProvenance": build_data_provenance(
                DEFAULT_DB_DATA_SOURCE,
                regulations=p.regulations,
            ),
        }
        if score:
            parcel_dict["scores"] = {
                "treeScore": score.tree_score,
                "gardenScore": score.garden_score,
                "solarScore": score.solar_score,
                "topRecommendation": score.top_recommendation,
                "uncertainty": score.uncertainty,
                "treeBreakdown": [],
                "gardenBreakdown": [],
                "solarBreakdown": [],
            }
        parcel_list.append(parcel_dict)

    stats_query = select(
        func.count(Parcel.id),
        func.avg(ParcelScore.tree_score),
        func.avg(ParcelScore.garden_score),
        func.avg(ParcelScore.solar_score),
        func.sum(Parcel.area_sqm),
    ).select_from(Parcel).outerjoin(ParcelScore)
    if district:
        stats_query = stats_query.where(Parcel.district == district)
    if parcel_type:
        stats_query = stats_query.where(Parcel.parcel_type == parcel_type)

    stats_row = (await db.execute(stats_query)).one()
    total = stats_row[0] or 0

    rec_query = select(ParcelScore.top_recommendation, func.count(ParcelScore.id)).group_by(
        ParcelScore.top_recommendation
    )
    rec_rows = await db.execute(rec_query)
    rec_counts = {row[0]: row[1] for row in rec_rows.all()}

    stats = {
        "total": total,
        "avgTreeScore": round(stats_row[1] or 0),
        "avgGardenScore": round(stats_row[2] or 0),
        "avgSolarScore": round(stats_row[3] or 0),
        "topTreeCount": rec_counts.get("TREE", 0),
        "topGardenCount": rec_counts.get("GARDEN", 0),
        "topSolarCount": rec_counts.get("SOLAR", 0),
        "totalAreaSqm": round(stats_row[4] or 0),
    }

    return parcel_list, stats


async def get_parcel_by_id(db: AsyncSession, parcel_id: str) -> Optional[Parcel]:
    result = await db.execute(
        select(Parcel).options(selectinload(Parcel.scores)).where(Parcel.id == parcel_id)
    )
    return result.scalar_one_or_none()


async def get_parcel_detail_resolved(db: AsyncSession, parcel_id: str) -> Optional[Dict[str, Any]]:
    """DB 우선, 없으면 VWorld 실시간 캐시/PNU 조회."""
    from app.services.live_search_service import live_get_parcel

    detail = await get_parcel_detail(db, parcel_id)
    if detail:
        return detail
    live = await live_get_parcel(parcel_id)
    if live:
        return live
    return None


async def get_parcel_detail(db: AsyncSession, parcel_id: str) -> Optional[Dict[str, Any]]:
    parcel = await get_parcel_by_id(db, parcel_id)
    if not parcel:
        return None

    # 시드 부지도 좌표→PNU→흙토람으로 실제 토양 보강
    soil_enrich = await _enrich_soil_from_location(
        float(parcel.lat),
        float(parcel.lng),
        existing_soil=str(parcel.soil_type or "UNKNOWN"),
    )
    soil_type = soil_enrich["soilType"]
    soil_actual = bool(soil_enrich["soil_type_actual"])

    # 실측 토양이면 DB에도 캐시해 다음 조회·목록 점수 입력으로 활용
    if soil_actual and soil_type != parcel.soil_type:
        try:
            parcel.soil_type = soil_type
            await db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("persist soil_type failed id=%s: %s", parcel_id, exc)
            await db.rollback()

    score = parcel.scores
    parcel_dict = {
        "id": parcel.id,
        "name": parcel.name,
        "district": parcel.district,
        "neighborhood": parcel.neighborhood,
        "lat": parcel.lat,
        "lng": parcel.lng,
        "areaSqm": parcel.area_sqm,
        "parcelType": parcel.parcel_type,
        "ownership": parcel.ownership,
        "soilType": soil_type,
        "soilTypeLabel": soil_enrich.get("soilTypeLabel"),
        "soilDetail": soil_enrich.get("soilDetail"),
        "pnu": soil_enrich.get("pnu"),
        "solarIrradiance": parcel.solar_irradiance,
        "monthlyIrradiance": parcel.monthly_irradiance,
        "sunlightHours": parcel.sunlight_hours,
        "heatIsland": parcel.heat_island,
        "surfaceTempSummer": parcel.surface_temp_summer,
        "airQuality": parcel.air_quality,
        "nearbyHouseholds": parcel.nearby_households,
        "pedestrianFlow": parcel.pedestrian_flow,
        "roadAdjacent": parcel.road_adjacent,
        "waterAccess": parcel.water_access,
        "electricityAccess": parcel.electricity_access,
        "nearbySchools": parcel.nearby_schools,
        "nearbyHospitals": parcel.nearby_hospitals,
        "nearbyParks": parcel.nearby_parks,
        "nearbySubwayStations": parcel.nearby_subway_stations,
        "regulatoryRestriction": parcel.regulatory_restriction,
        "regulations": parcel.regulations or [],
        "sumokFeasibility": parcel.sumok_feasibility,
        "confidence": parcel.confidence,
        "dataSource": "GreenSpot DB + 흙토람" if soil_actual else "GreenSpot DB",
        "dataProvenance": build_data_provenance(
            DEFAULT_DB_DATA_SOURCE,
            regulations=parcel.regulations,
            soil_type_actual=soil_actual,
        ),
    }

    scores_dict = {}
    if score:
        scores_dict = {
            "treeScore": score.tree_score,
            "gardenScore": score.garden_score,
            "solarScore": score.solar_score,
            "topRecommendation": score.top_recommendation,
            "uncertainty": score.uncertainty,
            "treeBreakdown": [],
            "gardenBreakdown": [],
            "solarBreakdown": [],
        }

    return {
        "parcel": parcel_dict,
        "scores": scores_dict,
        "source": "database",
    }


async def compare_parcels(db: AsyncSession, parcel_ids: List[str]) -> Optional[Dict[str, Any]]:
    """DB 시드 + 라이브 VW- 필지 혼합 비교.

    라이브 필지는 parcels 테이블에 없을 수 있으므로 live_get_parcel 로 보강한다.
    """
    if len(parcel_ids) < 2:
        return None

    # 순서 유지하며 중복 제거
    ordered_ids: List[str] = []
    seen: set[str] = set()
    for pid in parcel_ids:
        if pid and pid not in seen:
            seen.add(pid)
            ordered_ids.append(pid)

    result = await db.execute(
        select(Parcel)
        .options(selectinload(Parcel.scores))
        .where(Parcel.id.in_(ordered_ids))
    )
    db_by_id = {p.id: p for p in result.scalars().unique().all()}

    from app.services.live_search_service import live_get_parcel
    from app.services.simulation_service import simulate_scenario

    comparison: List[Dict[str, Any]] = []
    for pid in ordered_ids:
        p = db_by_id.get(pid)
        if p:
            score = p.scores
            area = float(p.area_sqm or 0)
            entry = {
                "id": p.id,
                "name": p.name,
                "district": p.district,
                "areaSqm": area,
                "scores": {
                    "tree": score.tree_score if score else 0,
                    "garden": score.garden_score if score else 0,
                    "solar": score.solar_score if score else 0,
                    "top": score.top_recommendation if score else "NONE",
                },
                "effects": {},
            }
        else:
            try:
                live = await live_get_parcel(pid)
            except Exception:  # noqa: BLE001
                live = None
            if not live or not live.get("parcel"):
                continue
            lp = live["parcel"]
            ls = live.get("scores") or lp.get("scores") or {}
            area = float(lp.get("areaSqm") or 0)
            entry = {
                "id": lp.get("id") or pid,
                "name": lp.get("name") or pid,
                "district": lp.get("district") or "",
                "areaSqm": area,
                "scores": {
                    "tree": ls.get("treeScore") or 0,
                    "garden": ls.get("gardenScore") or 0,
                    "solar": ls.get("solarScore") or 0,
                    "top": ls.get("topRecommendation") or "NONE",
                },
                "effects": {},
            }

        # 탄소 비교용: 나무 시나리오 1회 (면적 기반 기본 수량)
        tree_qty = min(28, max(1, int(entry["areaSqm"] / 20))) if entry["areaSqm"] else 10
        try:
            sim = await simulate_scenario(
                db,
                entry["id"],
                "PLANT_TREES",
                tree_qty,
                area_sqm_hint=entry["areaSqm"],
                name_hint=entry["name"],
            )
            if sim and sim.get("scenarios", {}).get("PLANT_TREES", {}).get("effects"):
                entry["effects"] = {
                    "PLANT_TREES": sim["scenarios"]["PLANT_TREES"]["effects"],
                }
        except Exception:  # noqa: BLE001
            pass

        comparison.append(entry)

    if len(comparison) < 2:
        return None

    ranking = {
        "tree": [c["id"] for c in sorted(comparison, key=lambda x: x["scores"]["tree"], reverse=True)],
        "garden": [c["id"] for c in sorted(comparison, key=lambda x: x["scores"]["garden"], reverse=True)],
        "solar": [c["id"] for c in sorted(comparison, key=lambda x: x["scores"]["solar"], reverse=True)],
        "carbon": [
            c["id"]
            for c in sorted(
                comparison,
                key=lambda x: (
                    (x.get("effects") or {}).get("PLANT_TREES") or {}
                ).get("carbonKgPerYear", 0),
                reverse=True,
            )
        ],
        "costEfficiency": [
            c["id"]
            for c in sorted(
                comparison,
                key=lambda x: (
                    (x.get("effects") or {}).get("PLANT_TREES") or {}
                ).get("costPerCarbonKgWon")
                if (
                    (x.get("effects") or {}).get("PLANT_TREES") or {}
                ).get("costPerCarbonKgWon")
                is not None
                else float("inf"),
            )
        ],
    }

    return {
        "comparison": comparison,
        "ranking": ranking,
    }


async def get_stats(db: AsyncSession) -> Dict[str, Any]:
    """호환용 래퍼 — 실제 집계는 stats_service 사용."""
    from app.services.stats_service import get_stats as get_stats_full

    return await get_stats_full(db)