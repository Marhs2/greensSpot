from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AgentQuery
from app.services.parcel_service import get_all_parcels
from app.services.llm_service import chat, LLMNotConfigured
from app.services.live_search_service import (
    live_search,
    extract_region_name,
    extract_neighborhood,
)
from app.services.vworld_discovery_service import VWorldDiscoveryError
from app.core.config import settings
import json
import re
import time

PARCEL_TYPE_MAP = {
    "빈터": "VACANT_LOT",
    "옥상": "ROOFTOP",
    "유휴지": "UNUSED_LAND",
    "방치건물": "ABANDONED",
    "오염정화지": "BROWNFIELD",
}

USE_MAP = {
    "식수": "TREE",
    "나무": "TREE",
    "수목": "TREE",
    "식재": "TREE",
    "텃밭": "GARDEN",
    "태양광": "SOLAR",
    "솔라": "SOLAR",
}


def _extract_min_score(query: str) -> Optional[int]:
    m = re.search(r"(\d{2,3})\s*점", query)
    if m:
        return int(m.group(1))
    if re.search(r"점수\s*(높|상위|좋)", query) or "높은 점수" in query:
        return 70
    return None


def _extract_limit(query: str) -> int:
    m = re.search(r"상위\s*(\d+)\s*개", query)
    if m:
        return min(int(m.group(1)), 20)
    return 10


def _extract_criteria_from_query(query: str) -> Dict[str, Any]:
    criteria: Dict[str, Any] = {}

    district = extract_region_name(query)
    if district:
        criteria["district"] = district
        criteria["region"] = district

    neighborhood = extract_neighborhood(query)
    if neighborhood:
        criteria["neighborhood"] = neighborhood

    for keyword, ptype in PARCEL_TYPE_MAP.items():
        if keyword in query:
            criteria["parcelType"] = ptype
            break

    for keyword, use in USE_MAP.items():
        if keyword in query:
            criteria["topRecommendation"] = use
            break

    min_score = _extract_min_score(query)
    if min_score is not None:
        criteria["minScore"] = min_score

    criteria["sortBy"] = "score"
    criteria["limit"] = _extract_limit(query)
    criteria["live"] = True
    criteria["explanation"] = _criteria_explanation(criteria)
    return criteria


def _criteria_explanation(criteria: Dict[str, Any]) -> str:
    parts: List[str] = []
    if criteria.get("district"):
        parts.append(f"지역={criteria['district']}")
    if criteria.get("neighborhood"):
        parts.append(f"동={criteria['neighborhood']}")
    if criteria.get("parcelType"):
        parts.append(f"유형={criteria['parcelType']}")
    if criteria.get("topRecommendation"):
        parts.append(f"추천={criteria['topRecommendation']}")
    if criteria.get("minScore"):
        parts.append(f"최소점수={criteria['minScore']}")
    if criteria.get("limit"):
        parts.append(f"상위 {criteria['limit']}개")
    parts.append("VWorld 실시간")
    return " · ".join(parts) if parts else "VWorld 실시간 조회"


def _top_score(parcel: Dict[str, Any]) -> float:
    scores = parcel.get("scores") or {}
    rec = scores.get("topRecommendation", "TREE")
    if rec == "TREE":
        return float(scores.get("treeScore") or 0)
    if rec == "GARDEN":
        return float(scores.get("gardenScore") or 0)
    if rec == "SOLAR":
        return float(scores.get("solarScore") or 0)
    return max(
        float(scores.get("treeScore") or 0),
        float(scores.get("gardenScore") or 0),
        float(scores.get("solarScore") or 0),
    )


def _score_for_use_parcel(parcel: Dict[str, Any], use: Optional[str] = None) -> float:
    scores = parcel.get("scores") or {}
    rec = (use or scores.get("topRecommendation") or "TREE").upper()
    if rec in ("TREE", "SUMOK"):
        return float(scores.get("treeScore") or 0)
    if rec == "GARDEN":
        return float(scores.get("gardenScore") or 0)
    if rec == "SOLAR":
        return float(scores.get("solarScore") or 0)
    return _top_score(parcel)


async def search_parcels_by_criteria(db: AsyncSession, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """VWorld 실시간 검색 우선, API 키 없을 때만 DB 폴백."""
    if settings.vworld_api_key:
        try:
            payload = await live_search(criteria)
            if payload.get("message") and not payload.get("results"):
                return []
            return payload.get("results") or []
        except VWorldDiscoveryError:
            pass

    district = criteria.get("district")
    preferred = criteria.get("topRecommendation")
    strict_top = bool(criteria.get("strictTopRecommendation"))
    parcels, _ = await get_all_parcels(db, district=district, parcel_type=criteria.get("parcelType"))
    filtered: List[Dict[str, Any]] = []
    for p in parcels:
        if district and p.get("district") != district:
            continue
        scores = p.get("scores") or {}
        # 용도 키워드(수목/텃밭/태양광)는 정렬 우선 — 1위 불일치로 전부 버리지 않음
        if preferred and strict_top:
            if scores.get("topRecommendation") != preferred:
                continue
        if criteria.get("minScore") is not None:
            if _score_for_use_parcel(p, preferred) < float(criteria["minScore"]):
                continue
        filtered.append(p)
    filtered.sort(key=lambda p: _score_for_use_parcel(p, preferred), reverse=True)
    return filtered[: criteria.get("limit", 10)]


def _build_summary(query: str, criteria: Dict[str, Any], results: List[Dict[str, Any]], live_msg: Optional[str] = None) -> str:
    if live_msg and not results:
        return live_msg
    district = criteria.get("district")
    if not results:
        if district:
            return f"{district}에서 조건에 맞는 부지를 찾지 못했습니다. 면적 조건을 넓히거나 용도 키워드를 빼 보세요."
        return "지역명을 포함해 검색해 주세요. 예: 용산구, 해운대구, 성남시"
    lead = results[0].get("name", "")
    region = district or results[0].get("district", "해당 지역")
    src = "VWorld 실시간" if settings.vworld_api_key else "DB"
    pref = criteria.get("topRecommendation")
    pref_note = ""
    if pref:
        label = {"TREE": "수목", "GARDEN": "텃밭", "SOLAR": "태양광"}.get(pref, pref)
        sc = _score_for_use_parcel(results[0], pref)
        pref_note = f" ({label} 점수 {sc:.0f} 기준 정렬)"
    return f"{lead} 부지가 추천됩니다. {region} · {src} 조회 {len(results)}건{pref_note}"


async def ai_search(db: AsyncSession, query: str) -> Dict[str, Any]:
    start = time.time()
    criteria = _extract_criteria_from_query(query)

    live_msg: Optional[str] = None
    if settings.vworld_api_key:
        try:
            payload = await live_search(criteria)
            live_msg = payload.get("message")
            results = payload.get("results") or []
            if payload.get("meta"):
                criteria["liveMeta"] = payload["meta"]
        except VWorldDiscoveryError as e:
            results = []
            live_msg = str(e)
        except Exception as e:
            # httpx/network 등 미처리 예외가 500+CORS 누락으로 브라우저에 보이지 않게 함
            results = await search_parcels_by_criteria(db, criteria)
            live_msg = f"실시간 검색 일시 실패, DB 폴백: {e}"
            if not results:
                live_msg = f"실시간 검색에 실패했습니다. 잠시 후 다시 시도해 주세요. ({e})"
    else:
        results = await search_parcels_by_criteria(db, criteria)

    summary = _build_summary(query, criteria, results, live_msg)

    if results:
        try:
            names = ", ".join(r.get("name", "") for r in results[:5])
            messages = [
                {
                    "role": "system",
                    "content": (
                        "당신은 GreenSpot 부지 검색 AI입니다. VWorld 실시간 검색 결과만 요약하세요. "
                        "새로운 수치를 만들지 마세요. 한국어로 1~2문장으로 간결히 작성하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"검색어: {query}\n"
                        f"검색 조건: {json.dumps(criteria, ensure_ascii=False)}\n"
                        f"찾은 부지({len(results)}개): {names}\n요약해줘."
                    ),
                },
            ]
            summary = await chat(messages)
        except (LLMNotConfigured, Exception):
            pass

    source = "ai" if results else "fallback"
    if settings.vworld_api_key and results:
        source = "ai"

    elapsed = int((time.time() - start) * 1000)

    agent_query = AgentQuery(
        id=_generate_id(),
        query=query,
        criteria=criteria,  # JSON 컬럼 — 이중 dumps 금지
        result_count=len(results),
        summary=summary,
        source=source,
    )
    db.add(agent_query)
    await db.commit()

    return {
        "query": query,
        "criteria": criteria,
        "results": results,
        "summary": summary,
        "count": len(results),
        "elapsed_ms": elapsed,
        "source": source,
    }


def _generate_id() -> str:
    import secrets
    return secrets.token_hex(8)