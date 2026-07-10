"""
외부 데이터 연동 라우터 (명세서 기준 /api/v1/gs).

- VWorld WFS 규제 조회/동기화  -> sumokFeasibility / ParcelRegulation
- Visual Crossing Weather API 환경 데이터 (climate / heat / timeline)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta

from app.db.database import get_db
from app.models.models import Parcel, ParcelScore, ParcelRegulation
from app.services.parcel_service import get_parcel_by_id
from app.services.auth_service import generate_id
from app.services.vworld_service import (
    client as vworld_client,
    VWORLD_LAYERS,
    apply_regulation_penalties,
    compute_sumok_feasibility,
    VWorldNotConfigured,
    VWorldBBoxError,
)
from app.services.kma_service import client as kma_client, KmaNotConfigured
from app.services.visual_crossing_service import (
    client as visual_crossing_client,
    VisualCrossingNotConfigured,
)
from app.schemas.schemas import (
    VisualCrossingClimateResponse,
    VisualCrossingHeatResponse,
    VisualCrossingTimelineResponse,
    VWorldLandCharacteristicsResponse,
)

router = APIRouter(prefix="/api/v1/gs", tags=["greenspot-external"])


# ---------------------------------------------------------------------------
# 좌표/위치 헬퍼
# ---------------------------------------------------------------------------
def _validate_coordinates(lat: float, lng: float):
    if lat < -90 or lat > 90:
        raise HTTPException(status_code=400, detail="lat은 -90~90 범위여야 합니다.")
    if lng < -180 or lng > 180:
        raise HTTPException(status_code=400, detail="lng은 -180~180 범위여야 합니다.")


def _format_latlng_location(lat: float, lng: float) -> str:
    """Visual Crossing location 형식(``lat,lng``)으로 변환."""
    return f"{round(lat, 6)},{round(lng, 6)}"


def _parse_date_or_days(start: Optional[str], end: Optional[str], days: Optional[int]):
    """``days`` 또는 ``start``/``end`` 중 하나를 받아 (start, end) 문자열 튜플로 정규화."""
    if start or end:
        if start and not end:
            end = str(date.today())
        if end and not start:
            start = str(date.today() - timedelta(days=30))
        return start, end
    n = days if days and days > 0 else 30
    n = min(n, 365)
    end_d = date.today()
    start_d = end_d - timedelta(days=n)
    return str(start_d), str(end_d)


# ---------------------------------------------------------------------------
# VWorld 레이어 카탈로그
# ---------------------------------------------------------------------------
@router.get("/vworld/layers")
async def vworld_layers():
    return {
        "layers": [
            {
                "typename": typename,
                "code": cfg["code"],
                "name": cfg["name"],
                "severity": cfg["severity"],
                "affectedUses": cfg["affectedUses"],
                "penaltyType": cfg["penaltyType"],
                "penaltyValue": cfg["penaltyValue"],
                "legalBasis": cfg["legalBasis"],
            }
            for typename, cfg in VWORLD_LAYERS.items()
        ]
    }


# ---------------------------------------------------------------------------
# 부지 규제 실시간 조회 (VWorld, 미저장)
# ---------------------------------------------------------------------------
@router.get("/parcels/{parcel_id}/regulations")
async def lookup_regulations(parcel_id: str, db: AsyncSession = Depends(get_db)):
    parcel = await get_parcel_by_id(db, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")

    try:
        regs = await vworld_client().get_regulations_at_point(parcel.lat, parcel.lng)
    except VWorldNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "parcelId": parcel.id,
        "coordinates": {"lat": parcel.lat, "lng": parcel.lng},
        "regulations": regs,
        "count": len(regs),
        "source": "VWorld",
    }


# ---------------------------------------------------------------------------
# 부지 규제 동기화 + 수목 식재 가능성/점수 재계산 (저장)
# ---------------------------------------------------------------------------
@router.post("/parcels/{parcel_id}/regulations/sync")
async def sync_regulations(parcel_id: str, db: AsyncSession = Depends(get_db)):
    parcel = await get_parcel_by_id(db, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")

    try:
        regs = await vworld_client().get_regulations_at_point(parcel.lat, parcel.lng)
    except VWorldNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 기존 규제 삭제 후 재삽입
    await db.execute(delete(ParcelRegulation).where(ParcelRegulation.parcel_id == parcel.id))
    for reg in regs:
        db.add(ParcelRegulation(
            id=generate_id(),
            parcel_id=parcel.id,
            regulation_type=reg["regulationType"],
            regulation_name=reg.get("regulationName"),
            severity=reg["severity"],
            affected_uses=reg["affectedUses"],
            penalty_type=reg["penaltyType"],
            penalty_value=reg.get("penaltyValue"),
            legal_basis=reg.get("legalBasis"),
            description=reg.get("description"),
            source=reg.get("source", "VWorld"),
            source_layer=reg.get("sourceLayer"),
            typename=reg.get("typename"),
            raw_data=reg.get("rawData"),
        ))

    parcel.regulations = regs
    parcel.regulations_updated_at = datetime.utcnow()

    # 점수 패널티 적용
    score = parcel.scores
    if score is not None:
        base = {
            "sumokScore": float(score.sumok_score if score.sumok_score is not None else score.tree_score),
            "gardenScore": float(score.garden_score),
            "solarScore": float(score.solar_score),
        }
        applied = apply_regulation_penalties(base, regs)
        feasibility = compute_sumok_feasibility(
            applied["sumokScore"], regs, parcel.confidence
        )
        score.sumok_score = applied["sumokScore"]
        score.sumok_feasibility_snapshot = feasibility
        score.regulations_snapshot = regs
        score.is_latest = True
        score.algorithm_version = "v3-greenspot3"
        parcel.sumok_feasibility = feasibility
        parcel.sumok_feasibility_updated_at = datetime.utcnow()
    else:
        parcel.sumok_feasibility = compute_sumok_feasibility(0.0, regs, parcel.confidence)
        parcel.sumok_feasibility_updated_at = datetime.utcnow()

    await db.commit()
    return {
        "parcelId": parcel.id,
        "regulations": regs,
        "sumokFeasibility": parcel.sumok_feasibility,
        "source": "VWorld",
    }


# ---------------------------------------------------------------------------
# 기상청 ASOS 환경 데이터 보강
# ---------------------------------------------------------------------------
@router.post("/parcels/{parcel_id}/enrich")
async def enrich_environment(parcel_id: str, db: AsyncSession = Depends(get_db)):
    parcel = await get_parcel_by_id(db, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")

    try:
        climate = await kma_client().get_climate_for_district(parcel.district)
    except KmaNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not climate.get("dataAvailable"):
        return {
            "parcelId": parcel.id,
            "updated": False,
            "message": "기상청 데이터를 가져오지 못했습니다.",
            "climate": climate,
        }

    parcel.solar_irradiance = climate["solarIrradiance"]
    parcel.sunlight_hours = climate["sunlightHours"]
    parcel.confidence = min(parcel.confidence, 0.95)
    await db.commit()

    return {
        "parcelId": parcel.id,
        "updated": True,
        "solarIrradiance": parcel.solar_irradiance,
        "sunlightHours": parcel.sunlight_hours,
        "climate": climate,
        "source": "KMA",
    }


# ---------------------------------------------------------------------------
# VWorld 토지소유정보 WMS (getPossessionWMS)
# ---------------------------------------------------------------------------
@router.get("/vworld/possession/{pnu}")
async def vworld_possession_wms(
    pnu: str,
    bbox: str = Query(..., description="EPSG:4326 bbox `ymin,xmin,ymax,xmax`"),
    width: int = Query(915, ge=1, le=2048, description="이미지 너비(px)"),
    height: int = Query(700, ge=1, le=2048, description="이미지 높이(px)"),
):
    try:
        png_bytes = await vworld_client().get_possession_wms(
            pnu, bbox, width=width, height=height
        )
    except VWorldNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    except VWorldBBoxError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not png_bytes:
        return {
            "pnu": pnu,
            "contentType": "image/png",
            "dataAvailable": False,
        }

    return Response(content=png_bytes, media_type="image/png")


# ---------------------------------------------------------------------------
# VWorld 토지특성정보 (getLandCharacteristics)
# ---------------------------------------------------------------------------
@router.get(
    "/vworld/characteristics/{pnu}",
    response_model=VWorldLandCharacteristicsResponse,
)
async def vworld_land_characteristics(
    pnu: str,
    stdrYear: Optional[str] = Query(None, description="조회 기준 연도 (YYYY)"),
):
    try:
        payload = await vworld_client().get_land_characteristics(pnu, stdrYear)
    except VWorldNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VWorldLandCharacteristicsResponse(**payload)


# ---------------------------------------------------------------------------
# Visual Crossing Weather API
# ---------------------------------------------------------------------------
@router.get(
    "/visualcrossing/climate",
    response_model=VisualCrossingClimateResponse,
)
async def visualcrossing_climate(
    lat: float = Query(..., description="위도 (-90~90)"),
    lng: float = Query(..., description="경도 (-180~180)"),
    days: int = Query(30, ge=1, le=365, description="조회 기간(일), 기본 30"),
):
    _validate_coordinates(lat, lng)
    location = _format_latlng_location(lat, lng)
    start, end = _parse_date_or_days(None, None, days)
    try:
        payload = await visual_crossing_client().get_climate_for_district(
            district=None, start=start, end=end, location=location,
        )
    except VisualCrossingNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VisualCrossingClimateResponse(**payload)


@router.get(
    "/visualcrossing/heat",
    response_model=VisualCrossingHeatResponse,
)
async def visualcrossing_heat(
    lat: float = Query(..., description="위도 (-90~90)"),
    lng: float = Query(..., description="경도 (-180~180)"),
    days: int = Query(30, ge=1, le=365, description="여름 산정 윈도우(일), 기본 30"),
):
    _validate_coordinates(lat, lng)
    location = _format_latlng_location(lat, lng)
    try:
        payload = await visual_crossing_client().get_heat_estimates(
            district=None, days=days, location=location,
        )
    except VisualCrossingNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VisualCrossingHeatResponse(**payload)


@router.get(
    "/visualcrossing/timeline",
    response_model=VisualCrossingTimelineResponse,
)
async def visualcrossing_timeline(
    location: str = Query(..., description="Visual Crossing location (도시명 또는 'lat,lng')"),
    start: Optional[str] = Query(None, description="시작일 (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="종료일 (YYYY-MM-DD)"),
):
    try:
        days = await visual_crossing_client().get_timeline(
            location, start=start, end=end,
        )
    except VisualCrossingNotConfigured as e:
        raise HTTPException(status_code=400, detail=str(e))

    resolved_start, resolved_end = _parse_date_or_days(start, end, None)
    return VisualCrossingTimelineResponse(
        source="visualcrossing",
        location=location,
        start=resolved_start,
        end=resolved_end,
        days=days,
        count=len(days),
        dataAvailable=bool(days),
    )
