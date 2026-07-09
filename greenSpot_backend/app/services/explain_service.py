import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Parcel, ParcelScore
from app.services.parcel_service import get_parcel_detail_resolved
from app.services.llm_service import chat, LLMNotConfigured


def _fallback_explanation(parcel: Dict[str, Any], scores: Dict[str, Any]) -> str:
    score_items = sorted(
        [(k, v) for k, v in scores.items() if k.endswith("Score")],
        key=lambda x: x[1],
        reverse=True,
    )
    second = score_items[1][0] if len(score_items) > 1 else "NONE"
    third = score_items[2][0] if len(score_items) > 2 else "NONE"
    top_score = score_items[0][1] if score_items else 0
    return f"""## 📍 부지 요약
- 부지명: {parcel.get('name')}
- 위치: {parcel.get('district')} {parcel.get('neighborhood')}
- 면적: {parcel.get('areaSqm')}㎡
- 유형: {parcel.get('parcelType')}
- 소유권: {parcel.get('ownership')}
- 규제: {parcel.get('regulatoryRestriction')}

## 🎯 추천 결과 및 이유
1순위: {scores.get('topRecommendation', 'NONE')} (점수: {top_score})
- 불확실성: ±{scores.get('uncertainty', 0)}점

## 💡 대안 용도 검토
- 2순위: {second}
- 3순위: {third}

## ⚠️ 한계 및 보완점
- 신뢰도: {parcel.get('confidence', 0) * 100:.0f}%
- 데이터 출처: USDA i-Tree, 기상청, KOSIS, Landsat, 서울연구원
"""


async def explain_parcel(db: AsyncSession, parcel_id: str) -> Optional[Dict[str, Any]]:
    detail = await get_parcel_detail_resolved(db, parcel_id)
    if not detail:
        return None

    parcel = detail["parcel"]
    scores = detail["scores"]

    facts = {
        "parcelName": parcel.get("name"),
        "district": parcel.get("district"),
        "neighborhood": parcel.get("neighborhood"),
        "areaSqm": parcel.get("areaSqm"),
        "parcelType": parcel.get("parcelType"),
        "ownership": parcel.get("ownership"),
        "soilType": parcel.get("soilType"),
        "regulatoryRestriction": parcel.get("regulatoryRestriction"),
        "solarIrradiance": parcel.get("solarIrradiance"),
        "sunlightHours": parcel.get("sunlightHours"),
        "heatIsland": parcel.get("heatIsland"),
        "airQuality": parcel.get("airQuality"),
        "roadAdjacent": parcel.get("roadAdjacent"),
        "waterAccess": parcel.get("waterAccess"),
        "electricityAccess": parcel.get("electricityAccess"),
        "scores": scores,
    }

    explanation = _fallback_explanation(parcel, scores)
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 GreenSpot 부지 분석 AI입니다. facts 객체의 수치만 사용해 "
                    "한국어 마크다운 4개 섹션(📍 부지 요약, 🎯 추천 결과 및 이유, "
                    "💡 대안 용도 검토, ⚠️ 한계 및 보완점)으로 설명하세요. "
                    "facts 외의 수치를 만들지 말고, 출처(USDA i-Tree/기상청/"
                    "KOSIS/Landsat/서울연구원)를 명시하세요. 정치적 단어(불평등/격차/"
                    "소외/차별)를 사용하지 마세요."
                ),
            },
            {
                "role": "user",
                "content": f"다음 facts로 부지 분석 리포트를 작성하세요:\n{json.dumps(facts, ensure_ascii=False, default=str)}",
            },
        ]
        explanation = await chat(messages)
    except (LLMNotConfigured, Exception):
        # LLM 실패 시 규칙 기반 fallback (api.md 명세)
        explanation = _fallback_explanation(parcel, scores)

    return {
        "parcelId": parcel_id,
        "explanation": explanation,
        "facts": facts,
        "promptVersion": "v3-greenspot3",
        "uncertainty": scores.get("uncertainty", 0),
    }