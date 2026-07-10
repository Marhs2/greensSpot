from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.core.config import settings
from app.models.models import Parcel, ParcelScore
from app.services.parcel_service import get_all_parcels, get_parcel_detail, compare_parcels, get_stats
from app.services.stats_service import get_stats as get_stats_full
from app.services.agent_service import ai_search
from app.services.live_search_service import live_search, live_get_parcel, live_stats_from_results
from app.services.vworld_discovery_service import VWorldDiscoveryError
from app.services.explain_service import explain_parcel
from app.services.simulation_service import simulate_scenario, simulate_compare_all
from app.services.report_service import generate_report
from app.services.export_service import export_csv
from app.schemas.schemas import (
    HealthResponse, ParcelListResponse, ParcelDetailResponse, AgentSearchRequest,
    AgentSearchResponse, ExplainResponse, SimulateRequest, ScenarioResponse,
    CompareRequest, CompareResponse, ReportRequest, StatsResponse,
)
from datetime import datetime
import time
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gs", tags=["greenspot"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    start = time.time()
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    from app.models.models import Parcel, ParcelScore, Scenario, AgentQuery
    from sqlalchemy import select, func

    parcels_count = 0
    scores_count = 0
    scenarios_count = 0
    agent_queries_count = 0

    try:
        parcels_result = await db.execute(select(func.count(Parcel.id)))
        parcels_count = parcels_result.scalar()
    except Exception:
        pass

    try:
        scores_result = await db.execute(select(func.count(ParcelScore.id)))
        scores_count = scores_result.scalar()
    except Exception:
        pass

    try:
        scenarios_result = await db.execute(select(func.count(Scenario.id)))
        scenarios_count = scenarios_result.scalar()
    except Exception:
        pass

    try:
        agent_result = await db.execute(select(func.count(AgentQuery.id)))
        agent_queries_count = agent_result.scalar()
    except Exception:
        pass

    elapsed = int((time.time() - start) * 1000)

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database=db_status,
        stats={
            "parcels": parcels_count,
            "scores": scores_count,
            "scenarios": scenarios_count,
            "agentQueries": agent_queries_count,
        },
        environment={
            "nodeEnv": settings.environment,
            "vworldApiKeyConfigured": bool(settings.vworld_api_key),
            "kmaApiKeyConfigured": bool(settings.kma_api_key),
            "kosisApiKeyConfigured": bool(settings.kosis_api_key),
            "visualCrossingApiKeyConfigured": bool(settings.visual_crossing_api_key),
        },
        elapsed_ms=elapsed,
    )


@router.get("/parcels", response_model=ParcelListResponse)
async def list_parcels(
    district: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    live: bool = Query(True, description="VWorld 실시간 조회 (기본값)"),
    limit: int = Query(15, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    if live and settings.vworld_api_key and district:
        try:
            payload = await live_search({
                "district": district,
                "region": district,
                "parcelType": type,
                "limit": limit,
            })
            results = payload.get("results") or []
            return ParcelListResponse(
                parcels=results,
                stats=live_stats_from_results(results),
                source="vworld_live",
                vworldEnabled=True,
            )
        except VWorldDiscoveryError as e:
            raise HTTPException(status_code=400, detail=str(e))

    parcels, stats = await get_all_parcels(db, district=district, parcel_type=type)
    return ParcelListResponse(
        parcels=parcels,
        stats=stats,
        source="database",
        vworldEnabled=bool(settings.vworld_api_key),
    )


@router.get("/parcels/{parcel_id}", response_model=ParcelDetailResponse)
async def get_parcel(parcel_id: str, db: AsyncSession = Depends(get_db)):
    if parcel_id.startswith("VW-") or (len(parcel_id) == 19 and parcel_id.isdigit()):
        live = await live_get_parcel(parcel_id)
        if live:
            return ParcelDetailResponse(
                parcel=live["parcel"],
                scores=live["scores"],
                source=live.get("source", "vworld_live"),
            )
    detail = await get_parcel_detail(db, parcel_id)
    if not detail:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")
    return detail


@router.post("/agent", response_model=AgentSearchResponse)
async def agent_search(request: AgentSearchRequest, db: AsyncSession = Depends(get_db)):
    result = await ai_search(db, request.query)
    return AgentSearchResponse(**result)


@router.post("/parcels/{parcel_id}/explain", response_model=ExplainResponse)
async def explain_scores(parcel_id: str, db: AsyncSession = Depends(get_db)):
    result = await explain_parcel(db, parcel_id)
    if not result:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")
    return result


@router.post("/parcels/{parcel_id}/simulate", response_model=ScenarioResponse)
async def simulate(parcel_id: str, request: SimulateRequest, db: AsyncSession = Depends(get_db)):
    from app.services.simulation_service import normalize_scenario_type

    scenario_type = normalize_scenario_type(request.scenarioType)
    limits = {
        "PLANT_TREES": 200,
        "CREATE_GARDEN": 150,
        "INSTALL_SOLAR": 500,
        "COMPARE_ALL": 500,
        "SUMOK": 200,
        "TREE": 200,
        "GARDEN": 150,
        "SOLAR": 500,
    }
    max_qty = limits.get(scenario_type, limits.get(request.scenarioType, 500))
    if request.quantity > max_qty:
        raise HTTPException(status_code=400, detail=f"수량 초과: 최대 {max_qty}")

    hint_kwargs = {
        "area_sqm_hint": request.areaSqm,
        "name_hint": request.parcelName,
    }

    if scenario_type == "COMPARE_ALL":
        result = await simulate_compare_all(db, parcel_id, **hint_kwargs)
        if not result:
            raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")
        return ScenarioResponse(**result)

    result = await simulate_scenario(
        db, parcel_id, scenario_type, request.quantity, **hint_kwargs
    )
    if not result:
        logger.info("simulate endpoint returned 404 for parcel_id=%s scenario=%s", parcel_id, scenario_type)
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")
    return ScenarioResponse(**result)


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    if len(request.ids) < 2:
        raise HTTPException(status_code=400, detail="비교할 부지 2개 이상 필요")
    result = await compare_parcels(db, request.ids)
    if not result:
        raise HTTPException(status_code=400, detail="유효한 부지 2개 이상 필요")
    return CompareResponse(**result)


@router.post("/report")
async def export_report(request: ReportRequest, db: AsyncSession = Depends(get_db)):
    content = await generate_report(db, request.parcelId, request.format)
    if not content:
        raise HTTPException(status_code=404, detail="부지를 찾을 수 없음")

    if request.format == "markdown":
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="greenspot-{request.parcelId}.md"'},
        )
    else:
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="greenspot-{request.parcelId}.json"'},
        )


@router.get("/export")
async def export_csv_endpoint(db: AsyncSession = Depends(get_db)):
    content = await export_csv(db)
    from datetime import datetime
    filename = f"greenspot-parcels-{datetime.utcnow().strftime('%Y-%m-%d')}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats_endpoint(db: AsyncSession = Depends(get_db)):
    stats = await get_stats_full(db)
    return StatsResponse(**stats)



